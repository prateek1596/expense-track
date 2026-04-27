import uuid


def create_mock_consent(bank_name: str, masked_account: str) -> dict:
    consent_id = f"consent_{uuid.uuid4().hex[:10]}"
    consent_url = f"https://consent.mock.setu/{consent_id}"
    return {
        "consent_id": consent_id,
        "consent_url": consent_url,
        "bank_name": bank_name,
        "masked_account": masked_account,
    }
