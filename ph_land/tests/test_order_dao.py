import os
from datetime import datetime, timezone

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from fastapi.testclient import TestClient

import app.services.order_service as order_service
from app.dao.order_dao import OrderDAO
from app.domain.order import Order, OrderStatus
from app.main import app


def _make_order() -> Order:
    return Order(
        customer_id="cust-1",
        service_id="svc-1",
        provider_id="prov-1",
        start_time=datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc),
        details="Initial details",
    )


def test_order_dao_round_trip(tmp_path):
    db_path = tmp_path / "orders.db"
    dao = OrderDAO(db_path=db_path)
    order = _make_order()

    dao.save_order(order)
    saved = dao.list_orders()

    assert len(saved) == 1
    assert saved[0].id == order.id
    assert saved[0].details == "Initial details"


def test_order_dao_update_order(tmp_path):
    db_path = tmp_path / "orders.db"
    dao = OrderDAO(db_path=db_path)
    order = _make_order()
    dao.save_order(order)

    updated = order.model_copy(
        update={
            "details": "Updated details",
            "status": OrderStatus.CONFIRMED,
        }
    )
    dao.update_order(updated)

    saved = dao.get_order_by_id(order.id)
    assert saved is not None
    assert saved.details == "Updated details"
    assert saved.status == OrderStatus.CONFIRMED


def test_order_dao_list_recent_orders_returns_latest_three(tmp_path):
    db_path = tmp_path / "orders.db"
    dao = OrderDAO(db_path=db_path)

    orders = [
        Order(
            customer_id="cust-1",
            service_id=f"svc-{idx}",
            provider_id="prov-1",
            start_time=datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc),
            details=f"order-{idx}",
        )
        for idx in range(1, 6)
    ]

    for order in orders:
        dao.save_order(order)

    recent = dao.list_recent_orders(limit=3)

    assert len(recent) == 3
    assert [order.details for order in recent] == ["order-5", "order-4", "order-3"]


def test_create_order_form_allows_new_orders_without_id(tmp_path, monkeypatch):
    temp_db = tmp_path / "orders.db"
    monkeypatch.setattr(order_service, "_dao", OrderDAO(db_path=temp_db))

    client = TestClient(app)

    response = client.post(
        "/web-office/create-edit-order",
        data={
            "customer_id": "cust-1",
            "service_id": "svc-1",
            "provider_id": "prov-1",
            "start_time": "2026-09-14T09:00:00+00:00",
            "end_time": "2026-09-14T10:00:00+00:00",
            "details": "New order",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/web-office/web-office.html"
