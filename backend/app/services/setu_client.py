from datetime import datetime, timedelta, timezone

import httpx

from app.config import settings


class SetuClientError(Exception):
    pass


def _resolve_consent_id(payload: dict) -> str | None:
    return payload.get("id") or payload.get("consentId") or payload.get("consent_id")


def _resolve_consent_url(payload: dict) -> str | None:
    return payload.get("url") or payload.get("consentUrl") or payload.get("consent_url")


async def create_consent(bank_name: str, masked_account: str, user_id: int) -> dict:
    from_time = (datetime.now(timezone.utc) - timedelta(days=30)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    to_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    payload = {
        "purpose": "Expense Tracking",
        "consentMode": "STORE",
        "consentTypes": ["TRANSACTIONS"],
        "fiTypes": ["DEPOSIT"],
        "DataConsumer": {"id": settings.setu_client_id},
        "Customer": {"id": f"user-{user_id}"},
        "Frequency": {"unit": "DAY", "value": 1},
        "DataLife": {"unit": "YEAR", "value": 1},
        "DataRange": {"from": from_time, "to": to_time},
        "context": {
            "bank_name": bank_name,
            "masked_account": masked_account,
        },
    }

    url = f"{settings.setu_base_url.rstrip('/')}{settings.setu_consent_path}"
    headers = {
        "x-client-id": settings.setu_client_id,
        "x-client-secret": settings.setu_client_secret,
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.setu_timeout_seconds) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise SetuClientError(f"Failed to connect Setu sandbox: {exc}") from exc

    if response.status_code >= 400:
        raise SetuClientError(f"Setu API error {response.status_code}: {response.text}")

    body = response.json()
    consent_id = _resolve_consent_id(body)
    consent_url = _resolve_consent_url(body)
    if not consent_id or not consent_url:
        raise SetuClientError("Setu response did not include consent id/url")

    return {
        "consent_id": consent_id,
        "consent_url": consent_url,
        "bank_name": bank_name,
        "masked_account": masked_account,
    }
