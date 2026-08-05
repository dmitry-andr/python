from __future__ import annotations

from pathlib import Path
import json
from typing import List

from app.domain.customer import Customer

DATA_DIR = Path("data")
CUSTOMERS_FILE = DATA_DIR / "customers.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_customers() -> List[Customer]:
    _ensure_data_dir()
    if not CUSTOMERS_FILE.exists():
        return []
    try:
        with CUSTOMERS_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            customers: List[Customer] = []
            for item in data:
                try:
                    customers.append(Customer(**item))
                except Exception:
                    continue
            return customers
    except Exception:
        return []


def save_customers(customers: List[Customer] | List[dict]) -> None:
    _ensure_data_dir()
    out = []
    for customer in customers:
        if isinstance(customer, Customer):
            out.append(customer.dict())
        else:
            out.append(customer)
    with CUSTOMERS_FILE.open("w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)


def append_customer(customer: Customer) -> None:
    customers = load_customers()
    customers.append(customer)
    save_customers(customers)
