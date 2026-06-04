"""Generate SQLite DDL for D1 tables (reference only)."""

DDL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    nickname TEXT NOT NULL,
    thumb TEXT,
    followers_count INTEGER NOT NULL DEFAULT 0,
    followees_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    desc TEXT NOT NULL DEFAULT '',
    excerpt TEXT NOT NULL DEFAULT '',
    thumb TEXT NOT NULL DEFAULT '',
    cover TEXT NOT NULL DEFAULT '',
    comments_count INTEGER NOT NULL DEFAULT 0,
    likes_count INTEGER NOT NULL DEFAULT 0,
    bookmarks_count INTEGER NOT NULL DEFAULT 0,
    duration INTEGER NOT NULL DEFAULT 0,
    is_free INTEGER NOT NULL DEFAULT 1,
    published_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS episode_user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER,
    user_id INTEGER,
    UNIQUE(episode_id, user_id)
);

CREATE TABLE IF NOT EXISTS episode_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER,
    category_id INTEGER,
    UNIQUE(episode_id, category_id)
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    desc TEXT NOT NULL DEFAULT '',
    logo TEXT NOT NULL,
    background TEXT NOT NULL DEFAULT '',
    subscriptions_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS albums (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    author TEXT NOT NULL,
    cover TEXT NOT NULL,
    published_at TEXT NOT NULL,
    radios_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS episode_album (
    album_id INTEGER,
    episode_id INTEGER,
    PRIMARY KEY(album_id, episode_id)
);
"""

if __name__ == "__main__":
    print(DDL)
