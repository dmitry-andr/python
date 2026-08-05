from fastapi import APIRouter, HTTPException

from app.domain import Order
from app.services.order_service import OrderService

web_services_router = APIRouter()


@web_services_router.get("/health")
async def health_check():
    return {"status": "ok"}


@web_services_router.get("/orders")
async def list_orders():
    return OrderService.list_orders()


@web_services_router.get("/orders/{order_id}")
async def get_order(order_id: str):
    order = OrderService.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@web_services_router.post("/orders", status_code=201)
async def create_order(order: Order):
    try:
        return OrderService.create_order(order)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@web_services_router.put("/orders/{order_id}")
async def update_order(order_id: str, order: Order):
    try:
        return OrderService.update_order(order_id, order)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@web_services_router.delete("/orders/{order_id}")
async def delete_order(order_id: str):
    try:
        deleted_id = OrderService.delete_order(order_id)
        return {"deleted": deleted_id}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
