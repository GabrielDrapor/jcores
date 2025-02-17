from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    nickname = Column(String, nullable=False)
    thumb = Column(String, nullable=True)
    followers_count = Column(Integer, nullable=False, default=0)
    followees_count = Column(Integer, nullable=False, default=0)


class Episode(Base):
    __tablename__ = 'episodes'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    desc = Column(String, nullable=False, default='')
    excerpt = Column(String, nullable=False, default='')
    thumb = Column(String, nullable=False, default='')
    cover = Column(String, nullable=False, default='')
    comments_count = Column(Integer, nullable=False, default=0)
    likes_count = Column(Integer, nullable=False, default=0)
    bookmarks_count = Column(Integer, nullable=False, default=0)
    duration = Column(Integer, nullable=False, comment='in seconds', default=0)
    is_free = Column(Boolean, nullable=False, default=True)
    published_at = Column(String, nullable=False)


class EpisodeUser(Base):
    __tablename__ = 'episode_user'

    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)

    __table_args__ = (
        UniqueConstraint('episode_id', 'user_id'),
    )


class EpisodeCategory(Base):
    __tablename__ = 'episode_category'

    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, index=True)
    category_id = Column(Integer, index=True)

    __table_args__ = (
        UniqueConstraint('episode_id', 'category_id'),
    )


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    desc = Column(String, default='', nullable=False)
    logo = Column(String, nullable=False)
    background = Column(String, nullable=False, default='')
    subscriptions_count = Column(Integer, nullable=False)
