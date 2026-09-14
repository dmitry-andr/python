from __future__ import annotations

import sqlite3
from pathlib import Path

from app.utils.config import DB_APP_DATA_PATH


class DBClient:
    """Shared SQLite connection and schema helper for DAO modules."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path is not None else DB_APP_DATA_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id TEXT PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT,
                    email TEXT,
                    phone TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    service_id TEXT NOT NULL,
                    provider_id TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    details TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS services (
                    id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    service_sub_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL
                )
                """
            )
