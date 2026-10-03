"""Small, dependency-free helpers for runtime configuration."""

from __future__ import annotations

import os


PRODUCTION_ENVIRONMENTS = {"prod", "production"}
TRUE_VALUES = {"1", "true", "yes", "on"}


def is_production() -> bool:
    return os.getenv("APP_ENV", "development").strip().casefold() in (
        PRODUCTION_ENVIRONMENTS
    )


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in TRUE_VALUES


def required_secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} must be configured")
    return value


def validate_security_settings() -> None:
    """Fail startup when production security settings are unsafe."""
    if not is_production():
        return

    errors: list[str] = []
    secrets = {
        name: os.getenv(name, "").strip()
        for name in ("SECRET_KEY", "SETUP_TOKEN")
    }
    for name, value in secrets.items():
        if len(value) < 32:
            errors.append(f"{name} must contain at least 32 characters")
        if any(marker in value.casefold() for marker in ("change-this", "replace-with")):
            errors.append(f"{name} still contains a placeholder value")

    if secrets["SECRET_KEY"] and secrets["SECRET_KEY"] == secrets["SETUP_TOKEN"]:
        errors.append("SECRET_KEY and SETUP_TOKEN must be different")

    origins = [
        value.strip()
        for value in os.getenv("CORS_ORIGINS", "").split(",")
        if value.strip()
    ]
    if not origins or "*" in origins:
        errors.append("CORS_ORIGINS must list explicit HTTPS origins")
    elif any(not origin.startswith("https://") for origin in origins):
        errors.append("Every production CORS origin must use HTTPS")

    allowed_hosts = [
        value.strip()
        for value in os.getenv("ALLOWED_HOSTS", "").split(",")
        if value.strip()
    ]
    if not allowed_hosts or "*" in allowed_hosts:
        errors.append("ALLOWED_HOSTS must list explicit host names")

    if errors:
        raise RuntimeError("Unsafe production configuration: " + "; ".join(errors))
