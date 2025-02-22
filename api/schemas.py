from typing import Optional
from pydantic import BaseModel, computed_field
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from .crud import get_user_ids_by_episode_id, get_category_id_by_episode_id


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    thumb: Optional[str]
    followers_count: int
    followees_count: int


class Category(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    desc: str
    logo: str
    background: str
    subscriptions_count: int


class Episode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    desc: str
    excerpt: str
    thumb: Optional[str]
    cover: Optional[str]
    comments_count: int
    likes_count: int
    bookmarks_count: int
    duration: int
    is_free: bool
    published_at: datetime

    # @computed_field
    # def user_ids(self) -> list[int]:
    #     return get_user_ids_by_episode_id(self.id)

    # @computed_field
    # def category_id(self) -> int:
    #     return get_category_id_by_episode_id(self.id)


class Album(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    author: str
    cover: str
    published_at: str
    radios_count: int
