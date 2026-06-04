"""One-time migration script: PostgreSQL -> Cloudflare D1"""
import os
import sys
import json
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.local'))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ["DATABASE_URL"]
CF_ACCOUNT_ID = os.environ["CLOUDFLARE_ACCOUNT_ID"]
CF_EMAIL = os.environ["CLOUDFLARE_EMAIL"]
CF_API_KEY = os.environ["CLOUDFLARE_API_KEY"]
D1_DB_ID = "cf5574ed-c278-432d-a108-c0b53aa8ddf9"

engine = create_engine(DATABASE_URL)

D1_API = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{D1_DB_ID}/query"
HEADERS = {
    "X-Auth-Email": CF_EMAIL,
    "X-Auth-Key": CF_API_KEY,
    "Content-Type": "application/json",
}

RESERVED = {"desc", "order", "group", "select", "where", "from", "index", "key"}


def d1_exec(sql: str, params: list | None = None):
    body = {"sql": sql}
    if params:
        body["params"] = params
    resp = httpx.post(D1_API, headers=HEADERS, json=body, timeout=30)
    data = resp.json()
    if not data.get("success"):
        print(f"D1 ERROR: {data.get('errors')}")
        print(f"SQL: {sql[:200]}")
    return data


def quote_pg(col: str) -> str:
    return f'"{col}"' if col.lower() in RESERVED else col


def migrate_table(table_name: str, columns: list[str], batch_size: int = 0):
    pg_cols = ", ".join(quote_pg(c) for c in columns)
    d1_cols = ", ".join(columns)
    n = len(columns)
    # D1 max ~100 SQL variables per statement
    if batch_size == 0:
        batch_size = max(1, 90 // n)

    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT {pg_cols} FROM {table_name} ORDER BY 1")).fetchall()

    total = len(rows)
    print(f"{table_name}: {total} rows")
    if not rows:
        return

    for i in range(0, total, batch_size):
        batch = rows[i:i + batch_size]
        all_params = []
        for row in batch:
            for v in row:
                if isinstance(v, bool):
                    all_params.append(1 if v else 0)
                elif v is None:
                    all_params.append(None)
                else:
                    all_params.append(str(v) if not isinstance(v, (int, float)) else v)

        placeholders_one = f"({', '.join(['?'] * n)})"
        placeholders_all = ", ".join([placeholders_one] * len(batch))
        sql = f"INSERT OR IGNORE INTO {table_name} ({d1_cols}) VALUES {placeholders_all}"

        result = d1_exec(sql, all_params)
        if result.get("success"):
            changes = result["result"][0]["meta"]["changes"]
            print(f"  batch {i // batch_size + 1}: {len(batch)} sent, {changes} written")
        else:
            print(f"  batch {i // batch_size + 1}: FAILED")


def main():
    print("=== Migrating PostgreSQL -> Cloudflare D1 ===\n")

    # Clean up test data
    d1_exec("DELETE FROM users WHERE id = 99999")

    migrate_table("users", ["id", "nickname", "thumb", "followers_count", "followees_count"])
    migrate_table("categories", ["id", "name", "desc", "logo", "background", "subscriptions_count"])
    migrate_table("albums", ["id", "title", "description", "author", "cover", "published_at", "radios_count"])
    migrate_table("episodes", ["id", "title", "desc", "excerpt", "thumb", "cover",
                                "comments_count", "likes_count", "bookmarks_count",
                                "duration", "is_free", "published_at"])
    migrate_table("episode_user", ["id", "episode_id", "user_id"])
    migrate_table("episode_category", ["id", "episode_id", "category_id"])
    migrate_table("episode_album", ["album_id", "episode_id"])

    print("\n=== Migration complete ===")

    print("\n=== Verifying row counts ===")
    for table in ["users", "categories", "albums", "episodes", "episode_user", "episode_category", "episode_album"]:
        result = d1_exec(f"SELECT COUNT(*) as cnt FROM {table}")
        if result.get("success") and result.get("result"):
            cnt = result["result"][0]["results"][0]["cnt"]
            print(f"  {table}: {cnt} rows in D1")


if __name__ == "__main__":
    main()
