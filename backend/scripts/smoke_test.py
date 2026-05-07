"""Run a lightweight smoke test against the FastAPI app using TestClient.

This does NOT require the app running in Docker; it imports the ASGI app and runs
requests against it in-process.

Usage:
    python backend/scripts/smoke_test.py
"""
import sys

from pathlib import Path
import sys

# Ensure backend package path is on Python path when running as a script
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.main import app


def main():
    client = TestClient(app)

    r = client.get("/health")
    if r.status_code != 200 or r.json().get("status") != "ok":
        print("Health check failed", r.status_code, r.text)
        sys.exit(1)

    print("Health check OK")

    # Try docs route
    r2 = client.get("/docs")
    if r2.status_code != 200:
        print("Docs route unavailable", r2.status_code)
        sys.exit(1)

    print("Docs route OK")

    print("Smoke tests passed")


if __name__ == "__main__":
    main()
