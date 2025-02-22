import json
import os
from loguru import logger
from api.db import get_db_session
from api.crud import *
from api.models import Episode, EpisodeUser, EpisodeCategory, User, Album, EpisodeAlbum
from api.crawlers import *
import argparse
import os


def backfill_all_episodes_by_user(user_id: int):
    logger.info("user_id: {}", user_id)
    limit, offset = 50, 0
    episodes = []
    users = {}
    logger.info("fetching...")
    cache_path = 'api/data/crawler_cache_{user_id}.json'.format(
        user_id=user_id)
    if os.path.exists(cache_path):
        logger.info("cache exists")
        with open(cache_path, 'r', encoding='utf-8') as f:
            episodes = json.load(f)
        with open('api/data/crawler_cache_included_{user_id}.json'.format(user_id=user_id), 'r', encoding='utf-8') as f:
            users = json.load(f)
    if not episodes:
        while True:
            logger.info("fetching..., limit: {}, offset: {}", limit, offset)
            data = fetch_user_episodes(user_id, limit, offset)
            batch_episodes = data['data']
            episodes += batch_episodes
            included = data['included']
            for item in included:
                if item['type'] == 'users':
                    users[item['id']] = item
            if len(batch_episodes) < limit:
                break
            offset += limit
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(episodes, f, ensure_ascii=False, indent=4)
        with open('api/data/crawler_cache_included_{user_id}.json'.format(user_id=user_id), 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=4)

    logger.info("backfilling {} episodes", len(episodes))
    logger.info("first: {}", episodes[0])
    episodes_data = []
    episode_category_data = []
    episode_user_data = []
    with get_db_session() as db:
        for episode in episodes:
            logger.info("episode: {}", episode)
            episodes_data.append(Episode(
                id=int(episode['id']),
                title=episode['attributes']['title'],
                desc=episode['attributes']['desc'] or '',
                excerpt=episode['attributes']['excerpt'] or '',
                thumb=episode['attributes']['thumb'] or '',
                cover=episode['attributes']['cover'] or '',
                comments_count=episode['attributes']['comments-count'],
                likes_count=episode['attributes']['likes-count'],
                bookmarks_count=episode['attributes']['bookmarks-count'],
                duration=episode['attributes']['duration'],
                is_free=episode['attributes']['is-free'],
                published_at=episode['attributes']['published-at']
            ))
            if episode_data := episode['relationships'].get('category', {}).get('data'):
                category_id = episode_data.get('id')
                if category_id:
                    episode_category_data.append(EpisodeCategory(
                        episode_id=int(episode['id']),
                        category_id=int(category_id)
                    ))
            djs = episode['relationships']['djs']['data']
            for dj in djs:
                episode_user_data.append(EpisodeUser(
                    episode_id=int(episode['id']),
                    user_id=int(dj['id'])
                ))
        batch_insert_episode_users(db, episode_user_data)
        batch_insert_episode_categories(db, episode_category_data)
        batch_insert_episodes(db, episodes_data)

        logger.info("backfilling {} users", len(users))
        db_users = []
        for user_id in users:
            user_attrs = users[user_id]['attributes']
            db_users.append(User(
                id=user_id,
                nickname=user_attrs['nickname'],
                thumb=user_attrs['thumb'],
                followers_count=user_attrs['followers-count'],
                followees_count=user_attrs['followees-count'],
            ))
        batch_insert_users(db, db_users)

    logger.info("done.")


def backfill_albums():
    albums = []
    start_album_id = get_last_album_id(db) + 1
    for album_id in range(start_album_id, 999999):
        logger.info("album_id: {}", album_id)
        try:
            data = fetch_album(album_id)
        except Exception as e:
            logger.error(f"Failed to backfill album {album_id}: {e}")
            continue
        if not data:
            continue
        data = data['data']
        albums.append(Album(
            id=album_id,
            title=data['attributes']['title'],
            description=data['attributes']['description'] or '',
            author=data['attributes']['author'] or '',
            cover=data['attributes']['cover'] or '',
            published_at=data['attributes']['published-at'] or '',
            radios_count=data['attributes']['radios-count'] or 0,
        ))
        if album_id % 10 == 0:
            if not albums:
                # end of albums
                break
            logger.info("backfilling {} albums", album_id)
            with get_db_session() as db:
                batch_insert_albums(db, albums)
            albums = []


def backfill_episode_albums():
    episode_albums = []
    episodes = []
    # for album_id in range(2, 260):
    for album_id in models.RESERVED_ALBUM_IDS:
        logger.info("album_id: {}", album_id)
        try:
            data = fetch_episode_albums(album_id)
        except Exception as e:
            logger.error(f"Failed to backfill album {album_id}: {e}")
            continue
        if not data:
            continue
        data = data['data']
        for d in data:
            episode_albums.append(EpisodeAlbum(
                album_id=album_id,
                episode_id=d['id'],
            ))
            episodes.append(Episode(
                id=d['id'],
                title=d['attributes']['title'],
                desc=d['attributes']['desc'] or '',
                excerpt=d['attributes']['excerpt'] or '',
                thumb=d['attributes']['thumb'] or '',
                cover=d['attributes']['cover'] or '',
                comments_count=d['attributes']['comments-count'],
                likes_count=d['attributes']['likes-count'],
                bookmarks_count=d['attributes']['bookmarks-count'],
                duration=d['attributes']['duration'] or 0,
                is_free=d['attributes']['is-free'],
                published_at=d['attributes']['published-at'] or '',
            ))
    # if not episode_albums:
        # end of episode_albums
        # break
    # logger.info("backfilling {} episode_albums", album_id)
    with get_db_session() as db:
        # batch_insert_episode_albums(db, episode_albums)
        batch_insert_episodes(db, episodes)
    episode_albums = []
    episodes = []


if __name__ == "__main__":
    # backfill_categories()
    # user_id = 13701  # Nadya
    # user_id = 31418  # 重轻
    # user_id = 3  # 西蒙
    # user_id = 124832  # annann
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--user_id', type=int, help='user id')
    # args = parser.parse_args()
    # backfill_all_episodes_by_user(args.user_id)
    # backfill_albums()
    backfill_episode_albums()
