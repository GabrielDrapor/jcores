from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import httpx
from .db import get_db_session
from . import models
from .schemas import Episode, User, Category, Album
from .crud import get_episodes_with_filters, get_all_users, get_all_categories, get_all_albums

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
    album_id: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    sort_field_str: str | None = None,
    asc: bool = False,
    db: Session = Depends(get_db)
):
    sort_field = None
    if sort_field_str is not None:
        sort_field = getattr(models.Episode, sort_field_str, None)
    db_episodes = get_episodes_with_filters(
        db,
        user_id=user_id,
        category_id=category_id,
        album_id=album_id,
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
    db_users = [u for u in db_users if u['id'] in models.RESERVED_USER_IDS]
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


@app.get("/albums")
def get_albums(db: Session = Depends(get_db)):
    db_albums = get_all_albums(db)
    albums = [Album.model_validate(a) for a in db_albums]
    # sort by published_at desc
    albums = [a for a in albums if a.id in models.RESERVED_ALBUM_IDS]
    return sorted(albums, key=lambda a: a.id, reverse=True)


@app.get("/image-proxy/{path:path}")
async def proxy_image(path: str):
    """Proxy endpoint for images from image.gcores.com to avoid CORS issues"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"https://image.gcores.com/{path}"
            response = await client.get(url, follow_redirects=True)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code, detail="Failed to fetch image")

            headers = {key: value for key, value in response.headers.items()
                       if key.lower() in ["content-type", "content-length", "cache-control", "etag"]}

            return StreamingResponse(
                content=response.iter_bytes(),
                status_code=response.status_code,
                headers=headers
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error proxying image: {str(e)}")
