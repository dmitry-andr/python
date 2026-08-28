from __future__ import annotations

from pathlib import Path
import json
from typing import List

from app.domain.customer import Customer
from app.utils.config import CUSTOMERS_FILE


def load_customers() -> List[Customer]:
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
