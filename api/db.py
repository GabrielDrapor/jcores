import os
import json
from typing import Any, Optional, Callable
from functools import wraps
from pathlib import Path
from loguru import logger
import time
import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")

CF_ACCOUNT_ID = (os.getenv("CLOUDFLARE_ACCOUNT_ID") or "").strip()
CF_EMAIL = (os.getenv("CLOUDFLARE_EMAIL") or "").strip()
CF_API_KEY = (os.getenv("CLOUDFLARE_API_KEY") or "").strip()
CF_NAMESPACE_ID = (os.getenv("CLOUDFLARE_NAMESPACE_ID") or "").strip()
D1_DATABASE_ID = (os.getenv("D1_DATABASE_ID") or "").strip()
assert CF_ACCOUNT_ID and CF_EMAIL and CF_API_KEY and CF_NAMESPACE_ID and D1_DATABASE_ID

D1_API = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/d1/database/{D1_DATABASE_ID}/query"
KV_API = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{CF_NAMESPACE_ID}/values"
CF_HEADERS = {
    "X-Auth-Email": CF_EMAIL,
    "X-Auth-Key": CF_API_KEY,
}

_http_client: httpx.Client | None = None


def _get_client() -> httpx.Client:
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=30)
    return _http_client


# --- D1 ---

def d1_query(sql: str, params: list | None = None) -> list[dict]:
    body: dict[str, Any] = {"sql": sql}
    if params:
        body["params"] = params
    start = time.perf_counter()
    resp = _get_client().post(D1_API, headers={**CF_HEADERS, "Content-Type": "application/json"}, json=body)
    data = resp.json()
    elapsed = time.perf_counter() - start
    if not data.get("success"):
        logger.error(f"D1 query failed ({elapsed:.3f}s): {data.get('errors')} | SQL: {sql[:200]}")
        raise RuntimeError(f"D1 query failed: {data.get('errors')}")
    logger.info(f"D1 query OK ({elapsed:.3f}s): {sql[:80]}")
    return data["result"][0].get("results", [])


# --- Cloudflare KV (raw httpx, no SDK) ---

KV_TTL = 3600  # 1 hour


def _kv_get(key: str) -> Optional[Any]:
    resp = _get_client().get(f"{KV_API}/{key}", headers=CF_HEADERS)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return json.loads(resp.content)


def _kv_put(key: str, value: Any) -> None:
    _get_client().put(
        f"{KV_API}/{key}",
        headers=CF_HEADERS,
        data=json.dumps(value),
        params={"expiration_ttl": KV_TTL},
    )


def cf_kv_cache(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        cache_key = f"cache:{func.__name__}:{':'.join(key_parts)}"

        start = time.perf_counter()
        try:
            cached = _kv_get(cache_key)
            if cached is not None:
                logger.info(f"KV hit ({time.perf_counter() - start:.3f}s): {cache_key}")
                return cached
        except Exception as e:
            logger.warning(f"KV get failed: {e}")

        result = func(*args, **kwargs)

        if result is not None:
            try:
                _kv_put(cache_key, result)
            except Exception as e:
                logger.warning(f"KV put failed: {e}")
        return result
    return wrapper
