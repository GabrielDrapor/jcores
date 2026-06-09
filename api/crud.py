from .db import cf_kv_cache, d1_query


@cf_kv_cache
def get_all_users() -> list[dict]:
    return d1_query("SELECT id, nickname, thumb, followers_count, followees_count FROM users ORDER BY id")


@cf_kv_cache
def get_all_categories() -> list[dict]:
    return d1_query("SELECT id, name, desc, logo, background, subscriptions_count FROM categories ORDER BY id")


@cf_kv_cache
def get_all_albums() -> list[dict]:
    return d1_query("SELECT id, title, description, author, cover, published_at, radios_count FROM albums ORDER BY id")


def get_episodes_with_filters(
    user_ids: list[int] | None = None,
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

    sql = "SELECT DISTINCT e.id, e.title, e.desc, e.excerpt, e.thumb, e.cover, e.comments_count, e.likes_count, e.bookmarks_count, e.duration, e.is_free, e.published_at FROM episodes e"
    joins = []
    conditions = []
    params: list = []

    having_params = []
    if user_ids:
        joins.append("JOIN episode_user eu ON e.id = eu.episode_id")
        placeholders = ",".join(["?"] * len(user_ids))
        conditions.append(f"eu.user_id IN ({placeholders})")
        params.extend(user_ids)
        group_by = f" GROUP BY e.id HAVING COUNT(DISTINCT eu.user_id) = ?"
        having_params.append(len(user_ids))
    else:
        group_by = ""

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
    sql += group_by
    params.extend(having_params)

    sql += f" ORDER BY e.{sort_field} {direction} LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = d1_query(sql, params)
    for row in rows:
        row["is_free"] = bool(row["is_free"])
    return rows
