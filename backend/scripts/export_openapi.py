"""Export the FastAPI OpenAPI schema to a JSON file.

Usage:
    python backend/scripts/export_openapi.py
"""
import json
from pathlib import Path
import sys

# Ensure backend package path is on Python path when running as a script
ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.main import app


def main():
    out = Path(__file__).resolve().parents[2] / "openapi.json"
    spec = app.openapi()
    out.write_text(json.dumps(spec, indent=2))
    print(f"Wrote OpenAPI spec to {out}")


if __name__ == "__main__":
    main()
