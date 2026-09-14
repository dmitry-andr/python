from __future__ import annotations

from pathlib import Path
from typing import List

from app.dao.db_client import DBClient
from app.domain.service import Service


class ServiceDAO:
    """Persistence operations for services in SQLite."""

    def __init__(self, db_client: DBClient | None = None, db_path: str | Path | None = None):
        self.db_client = db_client or DBClient(db_path)

    @staticmethod
    def _row_to_service(row) -> Service:
        return Service(
            id=row["id"],
            business_id=row["business_id"],
            service_type=row["service_type"],
            service_sub_type=row["service_sub_type"],
            name=row["name"],
            description=row["description"],
        )

    def save_service(self, service: Service) -> None:
        with self.db_client.connect() as conn:
            conn.execute(
                """
                INSERT INTO services (
                    id, business_id, service_type, service_sub_type, name, description
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    business_id = excluded.business_id,
                    service_type = excluded.service_type,
                    service_sub_type = excluded.service_sub_type,
                    name = excluded.name,
                    description = excluded.description
                """,
                (
                    service.id,
                    service.business_id,
                    service.service_type,
                    service.service_sub_type,
                    service.name,
                    service.description,
                ),
            )

    def update_service(self, service: Service) -> None:
        with self.db_client.connect() as conn:
            conn.execute(
                """
                UPDATE services
                SET business_id = ?,
                    service_type = ?,
                    service_sub_type = ?,
                    name = ?,
                    description = ?
                WHERE id = ?
                """,
                (
                    service.business_id,
                    service.service_type,
                    service.service_sub_type,
                    service.name,
                    service.description,
                    service.id,
                ),
            )

    def list_services(self) -> List[Service]:
        with self.db_client.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, business_id, service_type, service_sub_type, name, description
                FROM services
                ORDER BY name ASC
                """
            ).fetchall()

        return [self._row_to_service(row) for row in rows]

    def get_service_by_id(self, service_id: str) -> Service | None:
        with self.db_client.connect() as conn:
            row = conn.execute(
                """
                SELECT id, business_id, service_type, service_sub_type, name, description
                FROM services
                WHERE id = ?
                """,
                (service_id,),
            ).fetchone()

        if row is None:
            return None
        return self._row_to_service(row)
