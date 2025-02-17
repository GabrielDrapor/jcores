from typing import Optional, Any

from loguru import logger
import models
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy import Column

from db import get_db_session, cache


def db_model_to_dict(db_model_obj: Any) -> dict | None:
    if db_model_obj is None:
        return None
    return {key: item for key, item in db_model_obj.__dict__.items() if not key.startswith('_')}


@cache()
def get_user(db: Session, user_id: int) -> Optional[dict]:
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    return db_model_to_dict(db_user)


@cache()
def get_all_users(db: Session) -> list[dict]:
    db_users = db.query(models.User).order_by(models.User.id).all()
    return [db_model_to_dict(user) for user in db_users]


# 30 minutes cache
@cache(expire=1800)
def get_all_categories(db: Session) -> list[dict]:
    db_categories = db.query(models.Category).order_by(
        models.Category.id).all()
    return [db_model_to_dict(category) for category in db_categories]


def insert_user(
    db: Session,
    user_id: int,
    nickname: str,
    thumb: str,
    followers_count: int,
    followees_count: int,
) -> models.User:
    if get_user(db, user_id) is not None:
        logger.info("user already exists: {}", user_id)
        return
    user = models.User(
        id=user_id,
        nickname=nickname,
        thumb=thumb,
        followers_count=followers_count,
        followees_count=followees_count,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@cache
def get_category(db: Session, category_id: int) -> Optional[dict]:
    db_category = db.query(models.Category).filter(
        models.Category.id == category_id).first()
    return db_model_to_dict(db_category)


def insert_category(
    db: Session,
    category_id: int,
    name: str,
    desc: str,
    logo: str,
    background: str,
    subscriptions_count: int,
):
    category = models.Category(
        id=category_id,
        name=name,
        desc=desc,
        logo=logo,
        background=background,
        subscriptions_count=subscriptions_count,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@cache()
def get_episode(db: Session, episode_id: int) -> Optional[dict]:
    episode = db.query(models.Episode).filter(
        models.Episode.id == episode_id).first()
    return db_model_to_dict(episode)


@cache(expire=300)  # 5 minutes cache
def get_episodes_by_user_id_and_category_id(
    db: Session,
    user_id: int | None = None,
    category_id: int | None = None,
    sort_field: Column | None = None,
    asc: bool = False,
    limit: int = 10,
    offset: int = 0,
) -> list[dict]:

    query = db.query(models.Episode)

    if user_id is not None:
        query = query.join(
            models.EpisodeUser,
            models.Episode.id == models.EpisodeUser.episode_id
        ).filter(models.EpisodeUser.user_id == user_id)

    if category_id is not None:
        query = query.join(
            models.EpisodeCategory,
            models.Episode.id == models.EpisodeCategory.episode_id
        ).filter(models.EpisodeCategory.category_id == category_id)

    if sort_field is None:
        sort_field = models.Episode.published_at
    if asc:
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())

    # Get from database
    episodes = query.offset(offset).limit(limit).all()
    return [db_model_to_dict(episode) for episode in episodes]


@cache()
def get_category_id_by_episode_id(episode_id: int) -> Optional[int]:
    with get_db_session() as db:
        result = db.query(models.EpisodeCategory.category_id).filter(
            models.EpisodeCategory.episode_id == episode_id
        ).first()
        return result[0] if result else None


def insert_episode_category(db: Session, episode_id: int, category_id: int):
    if get_category_id_by_episode_id(db, episode_id) == category_id:
        logger.info("episode category already exists: {}",
                    (episode_id, category_id))
        return
    episode_category = models.EpisodeCategory(
        episode_id=episode_id, category_id=category_id)
    db.add(episode_category)
    db.commit()
    return episode_category


def batch_insert_episodes(db: Session, episodes: list[models.Episode]):
    values = [
        {k: v for k, v in episode.__dict__.items() if not k.startswith('_')}
        for episode in episodes
    ]
    stmt = insert(models.Episode).values(values).on_conflict_do_nothing()
    db.execute(stmt)
    db.commit()
    return


def batch_insert_episode_users(db: Session, episode_users: list[models.EpisodeUser]):
    # insert multi records, if the records already exist, it's no problem
    values = [
        {k: v for k, v in episode_user.__dict__.items() if not k.startswith('_')}
        for episode_user in episode_users
    ]
    stmt = insert(models.EpisodeUser).values(values).on_conflict_do_nothing()
    db.execute(stmt)
    db.commit()
    return


def batch_insert_episode_categories(db: Session, episode_categories: list[models.EpisodeCategory]):
    values = [
        {k: v for k, v in episode_category.__dict__.items() if not k.startswith('_')}
        for episode_category in episode_categories
    ]
    stmt = insert(models.EpisodeCategory).values(
        values).on_conflict_do_nothing()
    db.execute(stmt)
    db.commit()
    return


@cache()
def get_user_ids_by_episode_id(episode_id: int) -> list[int]:
    """get all user_ids by episode_id in `episode_user` table"""
    with get_db_session() as db:
        result = db.query(models.EpisodeUser.user_id).filter(
            models.EpisodeUser.episode_id == episode_id).all()
        return [row[0] for row in result]


def batch_insert_users(db: Session, users: list[models.User]):
    values = [
        {k: v for k, v in user.__dict__.items() if not k.startswith('_')}
        for user in users
    ]
    stmt = insert(models.User).values(values).on_conflict_do_nothing()
    db.execute(stmt)
    db.commit()
    return
