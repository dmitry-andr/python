from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

from app.dao.db_client import DBClient
from app.domain.order import Order, OrderStatus


class OrderDAO:
    """Persistence operations for orders in SQLite."""

    def __init__(self, db_client: DBClient | None = None, db_path: str | Path | None = None):
        self.db_client = db_client or DBClient(db_path)

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if value is None:
            return datetime.now(tz=timezone.utc)
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def _row_to_order(self, row) -> Order:
        return Order(
            id=row["id"],
            customer_id=row["customer_id"],
            service_id=row["service_id"],
            provider_id=row["provider_id"],
            start_time=self._parse_datetime(row["start_time"]),
            end_time=self._parse_datetime(row["end_time"]),
            details=row["details"] or "",
            status=OrderStatus(row["status"]) if row["status"] else OrderStatus.CREATED,
            created_at=self._parse_datetime(row["created_at"]),
        )

    def save_order(self, order: Order) -> None:
        with self.db_client.connect() as conn:
            conn.execute(
                """
                INSERT INTO orders (
                    id, customer_id, service_id, provider_id,
                    start_time, end_time, details, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    customer_id = excluded.customer_id,
                    service_id = excluded.service_id,
                    provider_id = excluded.provider_id,
                    start_time = excluded.start_time,
                    end_time = excluded.end_time,
                    details = excluded.details,
                    status = excluded.status,
                    created_at = excluded.created_at
                """,
                (
                    order.id,
                    order.customer_id,
                    order.service_id,
                    order.provider_id,
                    order.start_time.isoformat(),
                    order.end_time.isoformat(),
                    order.details,
                    order.status.value,
                    order.created_at.isoformat(),
                ),
            )

    def update_order(self, order: Order) -> None:
        with self.db_client.connect() as conn:
            conn.execute(
                """
                UPDATE orders
                SET customer_id = ?,
                    service_id = ?,
                    provider_id = ?,
                    start_time = ?,
                    end_time = ?,
                    details = ?,
                    status = ?,
                    created_at = ?
                WHERE id = ?
                """,
                (
                    order.customer_id,
                    order.service_id,
                    order.provider_id,
                    order.start_time.isoformat(),
                    order.end_time.isoformat(),
                    order.details,
                    order.status.value,
                    order.created_at.isoformat(),
                    order.id,
                ),
            )

    def list_orders(self) -> List[Order]:
        return self.list_recent_orders(limit=None)

    def list_recent_orders(self, limit: int | None = None) -> List[Order]:
        query = """
            SELECT id, customer_id, service_id, provider_id, start_time, end_time,
                   details, status, created_at
            FROM orders
            ORDER BY created_at DESC
        """
        params: tuple = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        with self.db_client.connect() as conn:
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_order(row) for row in rows]

    def get_order_by_id(self, order_id: str) -> Order | None:
        with self.db_client.connect() as conn:
            row = conn.execute(
                """
                SELECT id, customer_id, service_id, provider_id, start_time, end_time,
                       details, status, created_at
                FROM orders
                WHERE id = ?
                """,
                (order_id,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_order(row)

    def delete_order(self, order_id: str) -> str:
        with self.db_client.connect() as conn:
            cursor = conn.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        if cursor.rowcount == 0:
            raise KeyError("Order not found")
        return order_id
