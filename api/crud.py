from typing import Optional

from loguru import logger

from .db import cf_kv_cache, d1_query, d1_execute
from .models import RESERVED_USER_IDS, RESERVED_ALBUM_IDS


@cf_kv_cache
def get_all_users() -> list[dict]:
    return d1_query("SELECT id, nickname, thumb, followers_count, followees_count FROM users ORDER BY id")


@cf_kv_cache
def get_all_categories() -> list[dict]:
    return d1_query("SELECT id, name, desc, logo, background, subscriptions_count FROM categories ORDER BY id")


@cf_kv_cache
def get_all_albums() -> list[dict]:
    return d1_query("SELECT id, title, description, author, cover, published_at, radios_count FROM albums ORDER BY id")


@cf_kv_cache
def get_episodes_with_filters(
    user_id: int | None = None,
    category_id: int | None = None,
    album_id: int | None = None,
    sort_field: str | None = None,
    asc: bool = False,
    limit: int = 10,
    offset: int = 0,
) -> list[dict]:
    allowed_sort = {"published_at", "likes_count", "comments_count", "bookmarks_count"}
    if sort_field not in allowed_sort:
        sort_field = "published_at"
    direction = "ASC" if asc else "DESC"

    sql = "SELECT e.id, e.title, e.desc, e.excerpt, e.thumb, e.cover, e.comments_count, e.likes_count, e.bookmarks_count, e.duration, e.is_free, e.published_at FROM episodes e"
    joins = []
    conditions = []
    params: list = []

    if user_id is not None:
        joins.append("JOIN episode_user eu ON e.id = eu.episode_id")
        conditions.append("eu.user_id = ?")
        params.append(user_id)

    if category_id is not None:
        joins.append("JOIN episode_category ec ON e.id = ec.episode_id")
        conditions.append("ec.category_id = ?")
        params.append(category_id)

    if album_id is not None:
        joins.append("JOIN episode_album ea ON e.id = ea.episode_id")
        conditions.append("ea.album_id = ?")
        params.append(album_id)

    if joins:
        sql += " " + " ".join(joins)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += f" ORDER BY e.{sort_field} {direction} LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = d1_query(sql, params)
    for row in rows:
        row["is_free"] = bool(row["is_free"])
    return rows


@cf_kv_cache
def get_user_ids_by_episode_id(episode_id: int) -> list[int]:
    rows = d1_query("SELECT user_id FROM episode_user WHERE episode_id = ?", [episode_id])
    return [row["user_id"] for row in rows]


@cf_kv_cache
def get_category_id_by_episode_id(episode_id: int) -> Optional[int]:
    rows = d1_query("SELECT category_id FROM episode_category WHERE episode_id = ? LIMIT 1", [episode_id])
    return rows[0]["category_id"] if rows else None
