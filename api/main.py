from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
import httpx
from .schemas import Episode, User, Category, Album
from .crud import get_episodes_with_filters, get_all_users, get_all_categories, get_all_albums
from .models import RESERVED_ALBUM_IDS

app = FastAPI(root_path="/api/py")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_10M = "public, s-maxage=600, stale-while-revalidate=3600"
CACHE_1D = "public, s-maxage=86400, stale-while-revalidate=604800"


def cached_json(data, cache_control: str = CACHE_10M) -> JSONResponse:
    return JSONResponse(content=data, headers={"Cache-Control": cache_control})


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
    data = [Episode.model_validate(e).model_dump(mode="json") for e in db_episodes]
    return cached_json(data)


@app.get("/users")
def get_users():
    db_users = get_all_users()
    users = [User.model_validate(u) for u in db_users]
    data = [u.model_dump(mode="json") for u in sorted(users, key=lambda u: u.followers_count, reverse=True)]
    return cached_json(data)


@app.get("/categories")
def get_categories():
    db_categories = get_all_categories()
    categories = [Category.model_validate(c) for c in db_categories]
    data = [c.model_dump(mode="json") for c in sorted(categories, key=lambda c: c.subscriptions_count, reverse=True)]
    return cached_json(data)


@app.get("/albums")
def get_albums():
    db_albums = get_all_albums()
    albums = [Album.model_validate(a) for a in db_albums]
    data = [a.model_dump(mode="json") for a in sorted(albums, key=lambda a: a.radios_count, reverse=True)]
    return cached_json(data)


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
            headers["Cache-Control"] = CACHE_1D

            return StreamingResponse(
                content=response.iter_bytes(),
                status_code=response.status_code,
                headers=headers
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error proxying image: {str(e)}")
