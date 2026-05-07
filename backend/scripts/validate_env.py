"""Validate required environment variables for running the backend locally.

Usage:
    python backend/scripts/validate_env.py
"""
import os
import sys
from pathlib import Path

# Ensure backend package path is on Python path when running as a script
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.config import settings


REQUIRED = [
    "setu_client_id",
    "setu_client_secret",
    "setu_webhook_secret",
]


def main():
    missing = [k for k in REQUIRED if not getattr(settings, k)]
    if missing:
        print("Missing Setu configuration values in backend/.env or environment:")
        for k in missing:
            print(f" - {k}")
        print("\nPlease create `backend/.env` from `backend/.env.example` and populate Setu sandbox credentials.")
        sys.exit(2)

    print("All required Setu env vars are present.")


if __name__ == "__main__":
    main()
