"""
Periodic data sync: Gcores API -> Cloudflare D1

Designed to run hourly via GitHub Actions. Incremental by default —
only fetches what's new or changed.

Crawling etiquette:
  - 2s delay between every request
  - Small page sizes (20 items)
  - Identifies itself via User-Agent
  - Early termination on known data (no redundant fetching)
  - Total requests per run: ~13 (normal hourly), ~25 (catchup)
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
USER_AGENT = "JCores-Sync/1.0 (https://g.jrd.pub; hourly podcast index)"

client = httpx.Client(timeout=30, headers={"User-Agent": USER_AGENT})
_request_count = 0


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
    global _request_count
    time.sleep(REQUEST_DELAY)
    _request_count += 1
    url = f"{GCORES_BASE}/{path}"
    resp = client.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


# --- Step 1: Sync new episodes + authors + categories + albums ---

def sync_new_episodes():
    """Fetch latest episodes until we hit ones we already have.

    Each episode response includes DJs (-> users), category, and albums
    in the `included` data, so authors and albums accumulate naturally.
    """
    print("=== Syncing new episodes ===")

    existing = {r["id"] for r in d1_query("SELECT id FROM episodes ORDER BY id DESC LIMIT 200")}
    print(f"  Known recent episodes: {len(existing)}")

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


# --- Step 2: Update stats for recent episodes ---

def update_episode_stats():
    """Batch-update likes/bookmarks/comments for the 100 most recent episodes."""
    print("=== Updating episode stats ===")

    recent = d1_query("SELECT id FROM episodes ORDER BY published_at DESC LIMIT 100")
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


# --- Step 3: Sync albums (only when Gcores total changes) ---

def sync_albums():
    """Check if Gcores has new public albums; only full-scan on count change."""
    print("=== Syncing albums ===")

    local_count = d1_query("SELECT COUNT(*) as c FROM albums")[0]["c"]
    meta = gcores_get("albums", {"page[limit]": 1, "fields[albums]": "title"})
    remote_count = meta.get("meta", {}).get("record-count", 0)
    print(f"  Local: {local_count}, Gcores public: {remote_count}")

    if local_count >= remote_count:
        print("  No new public albums, skipping full scan")
        return 0

    existing_ids = {r["id"] for r in d1_query("SELECT id FROM albums")}
    new_count = 0
    offset = 0

    while offset < remote_count:
        data = gcores_get("albums", {
            "page[limit]": 50,
            "page[offset]": offset,
            "sort": "-published-at",
            "fields[albums]": "title,description,author,cover,published-at,radios-count",
        })
        for album in data.get("data", []):
            aid = int(album["id"])
            if aid in existing_ids:
                continue
            a = album["attributes"]
            d1("INSERT OR IGNORE INTO albums (id,title,description,author,cover,published_at,radios_count) VALUES (?,?,?,?,?,?,?)",
               [aid, a.get("title", ""), a.get("description") or "", a.get("author") or "",
                a.get("cover") or "", a.get("published-at") or "", a.get("radios-count", 0)])
            existing_ids.add(aid)
            new_count += 1
        offset += 50

    print(f"  Added {new_count} new albums")
    return new_count


# --- Main ---

def main():
    global _request_count
    _request_count = 0
    start = time.time()
    print(f"Sync started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    new_eps = sync_new_episodes()
    updated = update_episode_stats()
    new_albums = sync_albums()

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
        "gcores_requests": _request_count,
        "totals": totals,
    }

    print(f"\nSync completed in {elapsed:.0f}s ({_request_count} Gcores API requests)")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return summary


if __name__ == "__main__":
    main()
