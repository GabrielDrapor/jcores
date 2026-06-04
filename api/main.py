from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import httpx
from .schemas import Episode, User, Category, Album
from .crud import get_episodes_with_filters, get_all_users, get_all_categories, get_all_albums
from .models import RESERVED_USER_IDS, RESERVED_ALBUM_IDS

app = FastAPI(root_path="/api/py")

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
):
    db_episodes = get_episodes_with_filters(
        user_id=user_id,
        category_id=category_id,
        album_id=album_id,
        limit=limit,
        offset=offset,
        sort_field=sort_field_str,
        asc=asc,
    )
    return [Episode.model_validate(e) for e in db_episodes]


@app.get("/users")
def get_users():
    db_users = get_all_users()
    db_users = [u for u in db_users if u['id'] in RESERVED_USER_IDS]
    users = [User.model_validate(u) for u in db_users]
    return sorted(users, key=lambda u: u.followers_count, reverse=True)


@app.get("/categories")
def get_categories():
    db_categories = get_all_categories()
    categories = [Category.model_validate(c) for c in db_categories]
    return sorted(categories, key=lambda c: c.subscriptions_count, reverse=True)


@app.get("/albums")
def get_albums():
    db_albums = get_all_albums()
    albums = [Album.model_validate(a) for a in db_albums]
    albums = [a for a in albums if a.id in RESERVED_ALBUM_IDS]
    return sorted(albums, key=lambda a: a.id, reverse=True)


@app.get("/image-proxy/{path:path}")
async def proxy_image(path: str):
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
