from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from db import get_db_session
import models
from typing import Optional
from schemas import Episode, User, Category
from crud import get_episodes_by_user_id_and_category_id, get_all_users, get_all_categories

app = FastAPI(root_path="/api/py")


def get_db():
    with get_db_session() as db:
        yield db


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/episodes")
def get_episodes(
    user_id: Optional[int] = None,
    category_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    sort_field_str: str | None = None,
    asc: bool = False,
    db: Session = Depends(get_db)
):
    sort_field = None
    if sort_field_str is not None:
        sort_field = getattr(models.Episode, sort_field_str, None)
    db_episodes = get_episodes_by_user_id_and_category_id(
        db,
        user_id=user_id,
        category_id=category_id,
        limit=limit,
        offset=offset,
        sort_field=sort_field,
        asc=asc,
    )
    episodes = [Episode.model_validate(e) for e in db_episodes]
    return episodes


@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    db_users = get_all_users(db)
    # temp: filter out two users
    db_users = [u for u in db_users if u['id'] in [
        13701,  # Nadya
        31418,  # 重轻
        124832,  # annann
        3,  # 西蒙
        4769,  # 杨溢
        302894,  # 李习习
        19879,  # moby
        13146  # andorgenesis4324
    ]]
    users = [User.model_validate(u) for u in db_users]
    # sort by followers_count desc
    return sorted(users, key=lambda u: u.followers_count, reverse=True)


@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    db_categories = get_all_categories(db)
    # temp: filter out a few categories
    categories = [Category.model_validate(c) for c in db_categories]
    # sort by subscriptions_count desc, then categories
    return sorted(categories, key=lambda c: c.subscriptions_count, reverse=True)
