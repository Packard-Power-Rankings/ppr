from types import SimpleNamespace

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

from api.service.admin_service import AUTH_COOKIE_NAME, AdminServices


class FakeAdminCollection:
    def __init__(self, document=None):
        self.document = document
        self.inserted = None

    async def find_one(self, query, _projection=None):
        if not self.document:
            return None
        if not query or self.document.get("username") == query.get("username"):
            return self.document
        return None

    async def insert_one(self, document):
        self.inserted = document
        self.document = {"_id": "admin-id", **document}
        return SimpleNamespace(inserted_id="admin-id")


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "a-secure-test-secret-that-is-long-enough")


def request_with_headers(*headers):
    return Request({
        "type": "http",
        "method": "GET",
        "path": "/validate-token/",
        "headers": [
            (name.lower().encode("latin-1"), value.encode("latin-1"))
            for name, value in headers
        ],
    })


@pytest.mark.asyncio
async def test_create_admin_preserves_conflict_status():
    service = AdminServices()
    service.admin_collection = FakeAdminCollection({"username": "existing"})

    with pytest.raises(HTTPException) as error:
        await service.create_admin("another-admin", "long-test-password")

    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_create_admin_hashes_password_before_storage():
    service = AdminServices()
    service.admin_collection = FakeAdminCollection()

    admin_id = await service.create_admin("test-admin", "long-test-password")

    assert admin_id == "admin-id"
    assert service.admin_collection.inserted["username"] == "test-admin"
    assert service.admin_collection.inserted["password"] != "long-test-password"
    assert service.check_password(
        "long-test-password",
        service.admin_collection.inserted["password"],
    )


@pytest.mark.asyncio
async def test_login_failure_does_not_reveal_whether_username_exists():
    missing_service = AdminServices()
    missing_service.admin_collection = FakeAdminCollection()
    existing_service = AdminServices()
    existing_service.admin_collection = FakeAdminCollection({
        "username": "test-admin",
        "password": existing_service.hashed_password("correct-password"),
    })

    failures = []
    for service, username in (
        (missing_service, "missing-admin"),
        (existing_service, "test-admin"),
    ):
        with pytest.raises(HTTPException) as error:
            await service.verify_admin(username, "wrong-password")
        failures.append((error.value.status_code, error.value.detail))

    assert failures == [
        (401, "Invalid username or password"),
        (401, "Invalid username or password"),
    ]


@pytest.mark.asyncio
async def test_login_sets_an_httponly_strict_session_cookie(monkeypatch):
    service = AdminServices()
    monkeypatch.setenv("ROOT_PATH", "/api")

    async def verify_admin(_username, _password):
        return "signed-token"

    monkeypatch.setattr(service, "verify_admin", verify_admin)
    response = Response()

    token = await service.login(
        SimpleNamespace(username="test-admin", password="test-password"),
        response,
    )

    cookie = response.headers["set-cookie"]
    assert token.access_token == "signed-token"
    assert f"{AUTH_COOKIE_NAME}=signed-token" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Path=/api/" in cookie


@pytest.mark.asyncio
async def test_current_admin_accepts_cookie_and_checks_account_still_exists():
    service = AdminServices()
    service.admin_collection = FakeAdminCollection({
        "_id": "admin-id",
        "username": "test-admin",
    })
    token = service.generate_access_token({"sub": "test-admin"})
    request = request_with_headers(("cookie", f"{AUTH_COOKIE_NAME}={token}"))

    current_admin = await service.get_current_user(request)

    assert current_admin.username == "test-admin"

    service.admin_collection = FakeAdminCollection()
    with pytest.raises(HTTPException) as error:
        await service.get_current_user(request)
    assert error.value.status_code == 401


def test_password_check_rejects_values_over_bcrypt_limit():
    password_hash = AdminServices.hashed_password("correct-password")

    assert AdminServices.check_password("x" * 73, password_hash) is False
