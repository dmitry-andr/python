from __future__ import annotations

from typing import List

from app.dao.order_dao import OrderDAO
from app.domain import Order


_dao = OrderDAO()


class OrderService:
    @staticmethod
    def list_orders() -> list[Order]:
        return _dao.list_orders()

    @staticmethod
    def list_recent_orders(limit: int = 3) -> list[Order]:
        return _dao.list_recent_orders(limit=limit)

    @staticmethod
    def get_order(order_id: str) -> Order | None:
        return _dao.get_order_by_id(order_id)

    @staticmethod
    def create_order(order: Order) -> Order:
        if _dao.get_order_by_id(order.id) is not None:
            raise ValueError("Order already exists")
        _dao.save_order(order)
        return order

    @staticmethod
    def update_order(order_id: str, order: Order) -> Order:
        existing = _dao.get_order_by_id(order_id)
        if existing is None:
            raise KeyError("Order not found")
        order.id = order_id
        _dao.update_order(order)
        return order

    @staticmethod
    def delete_order(order_id: str) -> str:
        return _dao.delete_order(order_id)
