import pytest

from api.config.settings import validate_security_settings
from api.schemas.items import SetupAdminRequest


def test_production_rejects_weak_or_wildcard_security_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "short")
    monkeypatch.setenv("SETUP_TOKEN", "short")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    monkeypatch.setenv("ALLOWED_HOSTS", "*")

    with pytest.raises(RuntimeError, match="Unsafe production configuration"):
        validate_security_settings()


def test_production_accepts_explicit_https_security_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "s" * 64)
    monkeypatch.setenv("SETUP_TOKEN", "t" * 64)
    monkeypatch.setenv("CORS_ORIGINS", "https://rankings.example.com")
    monkeypatch.setenv("ALLOWED_HOSTS", "rankings.example.com")

    validate_security_settings()


@pytest.mark.parametrize("password", ["short", "x" * 73, " "]) 
def test_setup_admin_request_rejects_unsafe_password_lengths(password):
    with pytest.raises(ValueError):
        SetupAdminRequest(username="test-admin", password=password)
