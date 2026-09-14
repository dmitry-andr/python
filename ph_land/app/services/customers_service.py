from __future__ import annotations

from typing import List

from app.dao.customer_dao import CustomerDAO
from app.domain.customer import Customer


_dao = CustomerDAO()


def load_customers() -> List[Customer]:
    return _dao.list_customers()


def load_recent_customers(limit: int | None = None) -> List[Customer]:
    return _dao.list_recent_customers(limit=limit)


def save_customers(customers: List[Customer] | List[dict]) -> None:
    for customer in customers:
        if isinstance(customer, Customer):
            _dao.save_customer(customer)
        else:
            _dao.save_customer(Customer(**customer))


def append_customer(customer: Customer) -> None:
    _dao.save_customer(customer)


def update_customer(customer: Customer) -> None:
    _dao.update_customer(customer)
