import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
from api.routers import admin_routes, user_routes


def comma_separated_env(name: str, default: str) -> list[str]:
    """Return a clean list from a comma-separated environment variable."""
    return [
        value.strip()
        for value in os.getenv(name, default).split(",")
        if value.strip()
    ]


app = FastAPI(root_path=os.getenv("ROOT_PATH", "").rstrip("/"))

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
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_routes.router, tags=["Admin"])

app.include_router(user_routes.router, tags=["User"])


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000)
