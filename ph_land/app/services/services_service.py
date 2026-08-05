from __future__ import annotations

from pathlib import Path
import json
from typing import List

from app.domain.service import Service

DATA_DIR = Path("data")
SERVICES_FILE = DATA_DIR / "services.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_services() -> List[Service]:
    _ensure_data_dir()
    if not SERVICES_FILE.exists():
        return []
    try:
        with SERVICES_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            # Convert stored dicts to Service instances for safer template access
            services: List[Service] = []
            for item in data:
                try:
                    services.append(Service(**item))
                except Exception:
                    # skip malformed entries
                    continue
            return services
    except Exception:
        return []


def save_services(services: List[Service] | List[dict]) -> None:
    _ensure_data_dir()
    # Normalize to list of dicts for JSON serialization
    out = []
    for s in services:
        if isinstance(s, Service):
            out.append(s.dict())
        else:
            out.append(s)
    with SERVICES_FILE.open("w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)


def append_service(service: Service) -> None:
    services = load_services()
    services.append(service)
    save_services(services)
