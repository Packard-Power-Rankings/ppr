import os
from contextlib import asynccontextmanager

from arq.connections import create_pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
from api.database import close_mongo_client, ensure_database_indexes
from api.config.constants import LEVEL_CONSTANTS
from api.config.settings import env_flag, is_production, validate_security_settings
from api.config.redis import get_redis_settings
from api.routers import admin_routes, user_routes
from api.service.admin_teams import AdminTeamsService
from api.service.execution_history import prune_execution_history
from api.service.flagged_game_service import migrate_legacy_flagged_games
from api.service.ranking_scheduler import initialize_ranking_state


def comma_separated_env(name: str, default: str) -> list[str]:
    """Return a clean list from a comma-separated environment variable."""
    return [
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    ]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_security_settings()
    await ensure_database_indexes()
    await initialize_ranking_state()
    await migrate_legacy_flagged_games()
    await prune_execution_history()
    for level_key in LEVEL_CONSTANTS:
        await AdminTeamsService(level_key).migrate_legacy_uploads()
    redis = await create_pool(get_redis_settings())
    _app.state.redis = redis
    try:
        yield
    finally:
        await redis.aclose()
        close_mongo_client()


docs_enabled = env_flag("ENABLE_API_DOCS", default=not is_production())
app = FastAPI(
    root_path=os.getenv("ROOT_PATH", "").rstrip("/"),
    lifespan=lifespan,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

origins = comma_separated_env("CORS_ORIGINS", "http://localhost:3000")
allowed_hosts = comma_separated_env(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,testserver"
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type", "X-Setup-Token"],
)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), geolocation=(), microphone=()"
    )
    if request.url.path.rstrip("/") in {
        "/token",
        "/logout",
        "/validate-token",
        "/setup/admin",
    }:
        response.headers["Cache-Control"] = "no-store"
    return response

app.include_router(admin_routes.router, tags=["Admin"])

app.include_router(user_routes.router, tags=["User"])


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000)
