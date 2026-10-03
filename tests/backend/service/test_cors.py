import os

import pytest

from api.main import app


@pytest.mark.asyncio
async def test_cors_allows_patch_preflight_for_flagged_issue_resolution():
    origin = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000").split(",")[0].strip()
    response_messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        response_messages.append(message)

    await app(
        {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": "OPTIONS",
            "scheme": "http",
            "path": "/flagged-games/issue-123/resolve",
            "raw_path": b"/flagged-games/issue-123/resolve",
            "query_string": b"",
            "headers": [
                (b"host", b"testserver"),
                (b"origin", origin.encode()),
                (b"access-control-request-method", b"PATCH"),
                (b"access-control-request-headers", b"content-type"),
            ],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "root_path": "",
        },
        receive,
        send,
    )

    response_start = next(
        message for message in response_messages if message["type"] == "http.response.start"
    )
    response_headers = dict(response_start["headers"])

    assert response_start["status"] == 200
    assert b"PATCH" in response_headers[b"access-control-allow-methods"]
