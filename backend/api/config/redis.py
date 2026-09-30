import os

from arq.connections import RedisSettings


def get_redis_settings() -> RedisSettings:
    """Build the shared ARQ connection settings from the environment."""
    password = os.getenv("REDIS_PASSWORD") or None
    return RedisSettings(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        database=int(os.getenv("REDIS_DATABASE", "0")),
        password=password,
        ssl=os.getenv("REDIS_SSL", "false").lower() in {"1", "true", "yes"},
    )
