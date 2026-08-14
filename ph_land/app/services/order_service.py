from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from app.utils.config import DATA_DIR, ORDERS_FILE
from app.domain import Order


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not ORDERS_FILE.exists():
        ORDERS_FILE.write_text("[]", encoding="utf-8")


def _load_orders() -> Dict[str, Order]:
    _ensure_data_dir()
    try:
        with ORDERS_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return {}

    orders: Dict[str, Order] = {}
    for item in data:
        try:
            order = Order(**item)
            orders[order.id] = order
        except Exception:
            continue
    return orders


def _order_to_dict(order: Order) -> dict:
    data = order.dict()
    data["start_time"] = data["start_time"].isoformat()
    data["end_time"] = data["end_time"].isoformat()
    data["created_at"] = data["created_at"].isoformat()
    return data


def _save_orders(orders: Dict[str, Order]) -> None:
    _ensure_data_dir()
    with ORDERS_FILE.open("w", encoding="utf-8") as fh:
        json.dump([_order_to_dict(order) for order in orders.values()], fh, indent=2)


_orders: Dict[str, Order] = _load_orders()


class OrderService:
    @staticmethod
    def list_orders() -> list[Order]:
        return list(_orders.values())

    @staticmethod
    def get_order(order_id: str) -> Order | None:
        return _orders.get(order_id)

    @staticmethod
    def create_order(order: Order) -> Order:
        if order.id in _orders:
            raise ValueError("Order already exists")
        _orders[order.id] = order
        _save_orders(_orders)
        return order

    @staticmethod
    def update_order(order_id: str, order: Order) -> Order:
        if order_id not in _orders:
            raise KeyError("Order not found")
        order.id = order_id
        _orders[order_id] = order
        _save_orders(_orders)
        return order

    @staticmethod
    def delete_order(order_id: str) -> str:
        if order_id not in _orders:
            raise KeyError("Order not found")
        del _orders[order_id]
        _save_orders(_orders)
        return order_id
