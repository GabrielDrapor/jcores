"""
Periodic data sync: Gcores API -> Cloudflare D1

Designed to run hourly. Fetches new episodes, accumulates authors,
updates stats, and syncs albums.

Crawling etiquette: 2s delay between requests, small page sizes.
"""
import os
import sys
import time
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

CF_ACCOUNT_ID = os.environ["CLOUDFLARE_ACCOUNT_ID"].strip()
CF_EMAIL = os.environ["CLOUDFLARE_EMAIL"].strip()
CF_API_KEY = os.environ["CLOUDFLARE_API_KEY"].strip()
D1_DB_ID = os.environ["D1_DATABASE_ID"].strip()

D1_API = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{D1_DB_ID}/query"
D1_HEADERS = {"X-Auth-Email": CF_EMAIL, "X-Auth-Key": CF_API_KEY, "Content-Type": "application/json"}
GCORES_BASE = "https://www.gcores.com/gapi/v1"
REQUEST_DELAY = 2

client = httpx.Client(timeout=30)


def d1(sql, params=None):
    body = {"sql": sql}
    if params:
        body["params"] = params
    resp = client.post(D1_API, headers=D1_HEADERS, json=body)
    data = resp.json()
    if not data.get("success"):
        print(f"  D1 ERROR: {data.get('errors')}")
        return None
    return data["result"][0]


def d1_query(sql, params=None):
    r = d1(sql, params)
    return r.get("results", []) if r else []


def gcores_get(path, params=None):
    time.sleep(REQUEST_DELAY)
    url = f"{GCORES_BASE}/{path}"
    resp = client.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


# --- Sync latest episodes + authors + categories ---

def sync_new_episodes():
    """Fetch latest episodes until we hit ones we already have."""
    print("=== Syncing new episodes ===")

    existing = {r["id"] for r in d1_query("SELECT id FROM episodes ORDER BY id DESC LIMIT 200")}
    max_existing = max(existing) if existing else 0
    print(f"  Known episodes: {len(existing)}, max id: {max_existing}")

    new_episodes = []
    new_users = {}
    new_categories = {}
    new_albums = {}
    episode_users = []
    episode_categories = []
    episode_albums = []
    offset = 0
    page_size = 20
    stop = False

    while not stop:
        print(f"  Fetching episodes offset={offset}...")
        data = gcores_get("radios", {
            "page[limit]": page_size,
            "page[offset]": offset,
            "sort": "-published-at",
            "include": "user,djs,category,albums",
            "fields[radios]": "title,desc,excerpt,thumb,cover,comments-count,likes-count,bookmarks-count,published-at,duration,is-free,djs,category,albums",
        })

        episodes = data.get("data", [])
        if not episodes:
            break

        overlap_count = 0
        for ep in episodes:
            eid = int(ep["id"])
            if eid in existing:
                overlap_count += 1
                if overlap_count >= 5:
                    stop = True
                    break
                continue

            a = ep["attributes"]
            new_episodes.append((
                eid, a.get("title", ""), a.get("desc") or "", a.get("excerpt") or "",
                a.get("thumb") or "", a.get("cover") or "",
                a.get("comments-count", 0), a.get("likes-count", 0), a.get("bookmarks-count", 0),
                a.get("duration", 0), 1 if a.get("is-free", True) else 0,
                a.get("published-at", ""),
            ))

            for dj in ep.get("relationships", {}).get("djs", {}).get("data", []):
                episode_users.append((eid, int(dj["id"])))

            cat_data = ep.get("relationships", {}).get("category", {}).get("data")
            if cat_data:
                episode_categories.append((eid, int(cat_data["id"])))

            for alb in ep.get("relationships", {}).get("albums", {}).get("data", []):
                episode_albums.append((int(alb["id"]), eid))

        for inc in data.get("included", []):
            if inc["type"] == "users":
                uid = int(inc["id"])
                ua = inc["attributes"]
                new_users[uid] = (
                    uid, ua.get("nickname", ""), ua.get("thumb") or "",
                    ua.get("followers-count", 0), ua.get("followees-count", 0),
                )
            elif inc["type"] == "albums":
                aid = int(inc["id"])
                aa = inc["attributes"]
                new_albums[aid] = (
                    aid, aa.get("title", ""), aa.get("description") or "", aa.get("author") or "",
                    aa.get("cover") or "", aa.get("published-at") or "", aa.get("radios-count", 0),
                )
            elif inc["type"] == "categories":
                cid = int(inc["id"])
                ca = inc["attributes"]
                new_categories[cid] = (
                    cid, ca.get("name", ""), ca.get("desc") or "",
                    ca.get("logo") or "", ca.get("background") or "",
                    ca.get("subscriptions-count", 0),
                )

        offset += page_size

    print(f"  Found {len(new_episodes)} new episodes, {len(new_users)} users, {len(new_categories)} categories, {len(new_albums)} albums")

    for ep in new_episodes:
        d1("INSERT OR IGNORE INTO episodes (id,title,desc,excerpt,thumb,cover,comments_count,likes_count,bookmarks_count,duration,is_free,published_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", list(ep))

    for u in new_users.values():
        d1("INSERT OR REPLACE INTO users (id,nickname,thumb,followers_count,followees_count) VALUES (?,?,?,?,?)", list(u))

    for c in new_categories.values():
        d1("INSERT OR REPLACE INTO categories (id,name,desc,logo,background,subscriptions_count) VALUES (?,?,?,?,?,?)", list(c))

    for a in new_albums.values():
        d1("INSERT OR REPLACE INTO albums (id,title,description,author,cover,published_at,radios_count) VALUES (?,?,?,?,?,?,?)", list(a))

    for eid, uid in episode_users:
        d1("INSERT OR IGNORE INTO episode_user (episode_id,user_id) VALUES (?,?)", [eid, uid])

    for eid, cid in episode_categories:
        d1("INSERT OR IGNORE INTO episode_category (episode_id,category_id) VALUES (?,?)", [eid, cid])

    for aid, eid in episode_albums:
        d1("INSERT OR IGNORE INTO episode_album (album_id,episode_id) VALUES (?,?)", [aid, eid])

    return len(new_episodes)


# --- Update stats for existing episodes ---

def update_episode_stats():
    """Update likes/bookmarks/comments for recent episodes."""
    print("=== Updating episode stats ===")

    recent = d1_query("SELECT id FROM episodes ORDER BY published_at DESC LIMIT 200")
    episode_ids = [r["id"] for r in recent]
    print(f"  Updating stats for {len(episode_ids)} recent episodes")

    updated = 0
    for i in range(0, len(episode_ids), 20):
        batch = episode_ids[i:i+20]
        ids_str = ",".join(str(eid) for eid in batch)
        print(f"  Fetching batch {i//20+1}...")
        data = gcores_get("radios", {
            "page[limit]": 20,
            "filter[id]": ids_str,
            "fields[radios]": "comments-count,likes-count,bookmarks-count",
        })

        for ep in data.get("data", []):
            eid = int(ep["id"])
            a = ep["attributes"]
            d1("UPDATE episodes SET comments_count=?, likes_count=?, bookmarks_count=? WHERE id=?",
               [a.get("comments-count", 0), a.get("likes-count", 0), a.get("bookmarks-count", 0), eid])
            updated += 1

    print(f"  Updated {updated} episodes")
    return updated


# --- Sync albums ---

def sync_albums():
    """Fetch all albums, insert any missing ones."""
    print("=== Syncing albums ===")

    existing_ids = {r["id"] for r in d1_query("SELECT id FROM albums")}
    print(f"  Albums in D1: {len(existing_ids)}")

    new_count = 0
    offset = 0
    while True:
        data = gcores_get("albums", {
            "page[limit]": 50,
            "page[offset]": offset,
            "sort": "-published-at",
            "fields[albums]": "title,description,author,cover,published-at,radios-count",
        })
        albums = data.get("data", [])
        if not albums:
            break

        all_known = True
        for album in albums:
            aid = int(album["id"])
            if aid in existing_ids:
                continue
            all_known = False
            a = album["attributes"]
            d1("INSERT OR IGNORE INTO albums (id,title,description,author,cover,published_at,radios_count) VALUES (?,?,?,?,?,?,?)",
               [aid, a.get("title", ""), a.get("description") or "", a.get("author") or "",
                a.get("cover") or "", a.get("published-at") or "", a.get("radios-count", 0)])
            existing_ids.add(aid)
            new_count += 1

        offset += 50
        total = data.get("meta", {}).get("record-count", 0)
        if offset >= total:
            break

    print(f"  Added {new_count} new albums")
    return new_count


def sync_album_episodes():
    """Update episode-album links for reserved albums."""
    print("=== Syncing album episodes ===")
    from api.models import RESERVED_ALBUM_IDS

    total = 0
    for album_id in RESERVED_ALBUM_IDS:
        print(f"  Album {album_id}...")
        data = gcores_get(f"albums/{album_id}/published-audiobooks", {
            "fields[radios]": "title,desc,excerpt,thumb,cover,comments-count,likes-count,bookmarks-count,published-at,duration,is-free,djs,category",
        })

        for ep in data.get("data", []):
            eid = int(ep["id"])
            a = ep["attributes"]
            d1("INSERT OR REPLACE INTO episodes (id,title,desc,excerpt,thumb,cover,comments_count,likes_count,bookmarks_count,duration,is_free,published_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
               [eid, a.get("title", ""), a.get("desc") or "", a.get("excerpt") or "",
                a.get("thumb") or "", a.get("cover") or "",
                a.get("comments-count", 0), a.get("likes-count", 0), a.get("bookmarks-count", 0),
                a.get("duration", 0), 1 if a.get("is-free", True) else 0,
                a.get("published-at", "")])
            d1("INSERT OR IGNORE INTO episode_album (album_id,episode_id) VALUES (?,?)", [album_id, eid])
            total += 1

    print(f"  Synced {total} episode-album links")
    return total


# --- Main ---

def main():
    start = time.time()
    print(f"Sync started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    new_eps = sync_new_episodes()
    updated = update_episode_stats()
    new_albums = sync_albums()
    sync_album_episodes()

    elapsed = time.time() - start
    totals = {}
    for t in ["users", "episodes", "categories", "albums"]:
        r = d1_query(f"SELECT COUNT(*) as c FROM {t}")
        totals[t] = r[0]["c"]

    summary = {
        "new_episodes": new_eps,
        "stats_updated": updated,
        "new_albums": new_albums,
        "elapsed_seconds": round(elapsed),
        "totals": totals,
    }

    print(f"\nSync completed in {elapsed:.0f}s")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return summary


if __name__ == "__main__":
    main()
