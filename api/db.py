import redis
from functools import wraps
from typing import Any, Optional, Callable
import json
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DisconnectionError
from loguru import logger
from contextlib import contextmanager
from .models import Base  # Import the Base from models.py
import time
import os
from cloudflare import Cloudflare, NotFoundError

# Get DATABASE_URL from environment with a default value for local development
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

# Create the engine with optimized pool settings
engine = create_engine(
    DATABASE_URL,
    pool_size=5,               # Reduced from 10 to avoid too many connections
    max_overflow=10,           # Allow up to 10 connections over pool_size
    pool_timeout=30,           # Timeout for getting connection from pool
    pool_recycle=1800,        # Recycle connections after 30 minutes
    pool_pre_ping=True,       # Enable connection health checks
    connect_args={
        "connect_timeout": 10,  # Connection timeout in seconds
        "keepalives": 1,       # Enable TCP keepalive
        "keepalives_idle": 30,  # Idle time before sending keepalive
        "keepalives_interval": 10,  # Interval between keepalives
        "keepalives_count": 5  # Number of keepalive retries
    }
)

Session = sessionmaker(bind=engine)

# Create all tables
# logger.info("Creating tables")
# Base.metadata.create_all(engine)


def retry_on_connection_error(func):
    """Decorator to retry database operations on connection errors."""
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_delay = 1  # Start with 1 second delay

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except (OperationalError, DisconnectionError) as e:
                if attempt == max_retries - 1:  # Last attempt
                    logger.error(f"Failed after {max_retries} attempts: {e}")
                    raise

                logger.warning(
                    f"Database connection error(attempt {attempt + 1}/{max_retries}): {e}")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
    return wrapper


@contextmanager
@retry_on_connection_error
def get_db_session():
    """Provide a transactional scope for a session with retry logic."""
    logger.info("Getting database session")
    session = Session()
    try:
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()


# Redis client singleton
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.Redis.from_url(redis_url, decode_responses=True)


def make_key(prefix: str, *args) -> str:
    """Create a Redis key with prefix and arguments"""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"


def set_cache(key: str, value: Any, expire: int = 3600) -> None:
    """Set cache with expiration (default 1 hour)"""
    try:
        redis_client.set(key, json.dumps(value), ex=expire)
    except Exception as e:
        logger.error(f"Redis set error: {e}")


def get_cache(key: str) -> Optional[Any]:
    """Get cache value, returns None if not found"""
    try:
        start = time.perf_counter()
        data = redis_client.get(key)
        if data is not None:
            logger.info(
                f"Redis get success, key: '{key}', used time: {time.perf_counter() - start}s")
        else:
            logger.info(
                f"Redis get empty, key: '{key}', used time: {time.perf_counter() - start}s")
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Redis get error: {e}")
        return None


def cache(expire: int = 3600 * 24):
    """Decorator for caching function results

    Args:
        expire: Cache expiration time in seconds (default 1 hour)

    Example:
        @cache(3600)
        def get_user(db, user_id: int):
            return db.query(User).filter(User.id == user_id).first()
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip first arg if it's self or db session
            cache_args = args[1:] if args else []

            # Create cache key from function name and args
            key_parts = [str(arg) for arg in cache_args]
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = make_key(func.__name__, *key_parts)

            # Try to get from cache
            cached_data = get_cache(cache_key)
            if cached_data is not None:
                return cached_data

            # Get from function
            result = func(*args, **kwargs)

            # Cache the result if it's not None
            # if result is not None:
            # Handle SQLAlchemy models
            # if isinstance(result, list):
            # cache_data = [db_model_to_dict(item) for item in result]
            # else:
            # cache_data = db_model_to_dict(result)

            set_cache(cache_key, result, expire)
            return result
        return wrapper
    return decorator


CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID") or ""
CF_EMAIL = os.getenv("CLOUDFLARE_EMAIL") or ""
CF_API_KEY = os.getenv("CLOUDFLARE_API_KEY") or ""
CF_NAMESPACE_ID = os.getenv("CLOUDFLARE_NAMESPACE_ID") or ""
assert CF_ACCOUNT_ID and CF_EMAIL and CF_API_KEY and CF_NAMESPACE_ID

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
    """Create a Redis key with prefix and arguments"""
    return f"cache:{prefix}:{':'.join(str(arg) for arg in args)}"


def cf_kv_cache(func: Callable):
    """Decorator for caching function results"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Skip first arg if it's self or db session
        cache_args = args[1:] if args else []

        # Create cache key from function name and args
        key_parts = [str(arg) for arg in cache_args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
        cache_key = build_cf_kv_key(func.__name__, *key_parts)

        # Try to get from cache
        try:
            cached_data = get_cf_kv(cache_key)
            if cached_data is not None:
                return cached_data
        except NotFoundError:
            pass

        # Get from function
        result = func(*args, **kwargs)

        # Cache the result if it's not None
        if result is not None:
            set_cf_kv(cache_key, result)
        return result
    return wrapper
