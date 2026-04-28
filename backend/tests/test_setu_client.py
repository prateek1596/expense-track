import asyncio

import pytest

from app.services import setu_client
from app.services.setu_client import SetuClientError


class FakeResponse:
    def __init__(self, status_code: int, payload: dict, text: str = "ok"):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, timeout: int, captured: dict, response: FakeResponse):
        self.timeout = timeout
        self._captured = captured
        self._response = response

    async def __aenter__(self):
        self._captured["timeout"] = self.timeout
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json, headers):
        self._captured["url"] = url
        self._captured["json"] = json
        self._captured["headers"] = headers
        return self._response


def test_create_consent_maps_setu_response(monkeypatch):
    captured = {}
    response = FakeResponse(200, {"id": "consent-123", "url": "https://setu.example/consent-123"})

    monkeypatch.setattr(setu_client.settings, "setu_base_url", "https://sandbox.setu.test")
    monkeypatch.setattr(setu_client.settings, "setu_consent_path", "/api/v1/consents")
    monkeypatch.setattr(setu_client.settings, "setu_timeout_seconds", 11)
    monkeypatch.setattr(setu_client.settings, "setu_client_id", "client-1")
    monkeypatch.setattr(setu_client.settings, "setu_client_secret", "secret-1")
    monkeypatch.setattr(setu_client.httpx, "AsyncClient", lambda timeout: FakeAsyncClient(timeout, captured, response))

    result = asyncio.run(setu_client.create_consent("HDFC", "XXXX4321", 7))

    assert result == {
        "consent_id": "consent-123",
        "consent_url": "https://setu.example/consent-123",
        "bank_name": "HDFC",
        "masked_account": "XXXX4321",
    }
    assert captured["timeout"] == 11
    assert captured["url"] == "https://sandbox.setu.test/api/v1/consents"
    assert captured["headers"]["x-client-id"] == "client-1"
    assert captured["headers"]["x-client-secret"] == "secret-1"
    assert captured["json"]["Customer"]["id"] == "user-7"


def test_create_consent_rejects_malformed_response(monkeypatch):
    response = FakeResponse(200, {"id": "consent-123"})

    monkeypatch.setattr(setu_client.settings, "setu_base_url", "https://sandbox.setu.test")
    monkeypatch.setattr(setu_client.settings, "setu_consent_path", "/api/v1/consents")
    monkeypatch.setattr(setu_client.settings, "setu_timeout_seconds", 11)
    monkeypatch.setattr(setu_client.settings, "setu_client_id", "client-1")
    monkeypatch.setattr(setu_client.settings, "setu_client_secret", "secret-1")
    monkeypatch.setattr(setu_client.httpx, "AsyncClient", lambda timeout: FakeAsyncClient(timeout, {}, response))

    with pytest.raises(SetuClientError, match="consent id/url"):
        asyncio.run(setu_client.create_consent("HDFC", "XXXX4321", 7))