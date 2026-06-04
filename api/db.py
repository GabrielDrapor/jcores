import os
import json
from typing import Any, Optional, Callable
from functools import wraps
from pathlib import Path
from loguru import logger
import time
import httpx
from dotenv import load_dotenv
from cloudflare import Cloudflare, NotFoundError

load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")

CF_ACCOUNT_ID = (os.getenv("CLOUDFLARE_ACCOUNT_ID") or "").strip()
CF_EMAIL = (os.getenv("CLOUDFLARE_EMAIL") or "").strip()
CF_API_KEY = (os.getenv("CLOUDFLARE_API_KEY") or "").strip()
CF_NAMESPACE_ID = (os.getenv("CLOUDFLARE_NAMESPACE_ID") or "").strip()
D1_DATABASE_ID = (os.getenv("D1_DATABASE_ID") or "").strip()
assert CF_ACCOUNT_ID and CF_EMAIL and CF_API_KEY and CF_NAMESPACE_ID and D1_DATABASE_ID

D1_API = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{D1_DATABASE_ID}/query"
D1_HEADERS = {
    "X-Auth-Email": CF_EMAIL,
    "X-Auth-Key": CF_API_KEY,
    "Content-Type": "application/json",
}

_http_client: httpx.Client | None = None


def _get_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=30)
    return _http_client


def d1_query(sql: str, params: list | None = None) -> list[dict]:
    body: dict[str, Any] = {"sql": sql}
    if params:
        body["params"] = params
    start = time.perf_counter()
    resp = _get_client().post(D1_API, headers=D1_HEADERS, json=body)
    data = resp.json()
    elapsed = time.perf_counter() - start
    if not data.get("success"):
        logger.error(f"D1 query failed ({elapsed:.3f}s): {data.get('errors')} | SQL: {sql[:200]}")
        raise RuntimeError(f"D1 query failed: {data.get('errors')}")
    logger.info(f"D1 query OK ({elapsed:.3f}s): {sql[:80]}")
    return data["result"][0].get("results", [])


def d1_execute(sql: str, params: list | None = None) -> int:
    body: dict[str, Any] = {"sql": sql}
    if params:
        body["params"] = params
    resp = _get_client().post(D1_API, headers=D1_HEADERS, json=body)
    data = resp.json()
    if not data.get("success"):
        logger.error(f"D1 execute failed: {data.get('errors')} | SQL: {sql[:200]}")
        raise RuntimeError(f"D1 execute failed: {data.get('errors')}")
    return data["result"][0]["meta"]["changes"]


# --- Cloudflare KV cache (unchanged) ---

cf_client = Cloudflare(
    api_email=CF_EMAIL,
    api_key=CF_API_KEY
)


def set_cf_kv(key: str, value: Any) -> None:
    global cf_client
    cf_client.kv.namespaces.values.update(
        key_name=key,
        account_id=CF_ACCOUNT_ID,
        namespace_id=CF_NAMESPACE_ID,
        metadata="",
        value=json.dumps(value))


def get_cf_kv(key: str) -> Optional[Any]:
    global cf_client
    start = time.perf_counter()
    binary_resp = cf_client.kv.namespaces.values.get(
        key_name=key,
        account_id=CF_ACCOUNT_ID,
        namespace_id=CF_NAMESPACE_ID,
    )
    value = json.loads(binary_resp.json()['value'])
    logger.info(
        f"CF kv get success, key: '{key}', used time: {time.perf_counter() - start}s")
    return value


def delete_cf_kv(key: str) -> None:
    global cf_client
    cf_client.kv.namespaces.values.delete(
        key_name=key,
        account_id=CF_ACCOUNT_ID,
        namespace_id=CF_NAMESPACE_ID
    )


def build_cf_kv_key(prefix: str, *args) -> str:
    return f"cache:{prefix}:{':'.join(str(arg) for arg in args)}"


def cf_kv_cache(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        cache_key = build_cf_kv_key(func.__name__, *key_parts)

        try:
            cached_data = get_cf_kv(cache_key)
            if cached_data is not None:
                return cached_data
        except NotFoundError:
            pass

        result = func(*args, **kwargs)

        if result is not None:
            set_cf_kv(cache_key, result)
        return result
    return wrapper
