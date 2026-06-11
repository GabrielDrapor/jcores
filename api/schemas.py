from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class User(BaseModel):
    id: int
    nickname: str
    thumb: Optional[str]
    followers_count: int
    followees_count: int


class Category(BaseModel):
    id: int
    name: str
    desc: str
    logo: str
    background: str
    subscriptions_count: int


class DJ(BaseModel):
    id: int
    nickname: str
    thumb: Optional[str]


class Episode(BaseModel):
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
    djs: list[DJ] = []


class Album(BaseModel):
    id: int
    title: str
    description: str
    author: str
    cover: str
    published_at: str
    radios_count: int
