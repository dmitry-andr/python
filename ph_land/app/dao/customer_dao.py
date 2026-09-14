from __future__ import annotations

from pathlib import Path
from typing import List

from app.dao.db_client import DBClient
from app.domain.customer import Customer


class CustomerDAO:
    """Business-entity operations for customer persistence."""

    def __init__(self, db_client: DBClient | None = None, db_path: str | Path | None = None):
        self.db_client = db_client or DBClient(db_path)

    def save_customer(self, customer: Customer) -> None:
        with self.db_client.connect() as conn:
            conn.execute(
                """
                INSERT INTO customers (id, first_name, last_name, email, phone, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    email = excluded.email,
                    phone = excluded.phone,
                    created_at = excluded.created_at
                """,
                (
                    customer.id,
                    customer.first_name,
                    customer.last_name,
                    customer.email,
                    customer.phone,
                    customer.created_at.isoformat(),
                ),
            )

    def update_customer(self, customer: Customer) -> None:
        with self.db_client.connect() as conn:
            conn.execute(
                """
                UPDATE customers
                SET first_name = ?,
                    last_name = ?,
                    email = ?,
                    phone = ?,
                    created_at = ?
                WHERE id = ?
                """,
                (
                    customer.first_name,
                    customer.last_name,
                    customer.email,
                    customer.phone,
                    customer.created_at.isoformat(),
                    customer.id,
                ),
            )

    def list_customers(self) -> List[Customer]:
        return self.list_recent_customers(limit=None)

    def list_recent_customers(self, limit: int | None = None) -> List[Customer]:
        query = "SELECT id, first_name, last_name, email, phone, created_at FROM customers ORDER BY created_at DESC"
        params: tuple = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        with self.db_client.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        customers: List[Customer] = []
        for row in rows:
            customers.append(
                Customer(
                    id=row["id"],
                    first_name=row["first_name"],
                    last_name=row["last_name"] or "",
                    email=row["email"],
                    phone=row["phone"],
                    created_at=row["created_at"],
                )
            )
        return customers

    def get_customer_by_id(self, customer_id: str) -> Customer | None:
        with self.db_client.connect() as conn:
            row = conn.execute(
                "SELECT id, first_name, last_name, email, phone, created_at FROM customers WHERE id = ?",
                (customer_id,),
            ).fetchone()

        if row is None:
            return None

        return Customer(
            id=row["id"],
            first_name=row["first_name"],
            last_name=row["last_name"] or "",
            email=row["email"],
            phone=row["phone"],
            created_at=row["created_at"],
        )
