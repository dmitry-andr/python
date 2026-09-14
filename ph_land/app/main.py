from datetime import datetime, timezone
import json
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.utils.config import APP_NAME, APP_VERSION, DB_RAG_VECTOR_DIR, RUNTIME_DATA_DIR, FAVICON_PATH, STATIC_DIR, TEMPLATES_DIR, WEB_OFFICE_CUSTOMERS_LIST_LIMIT
from app.services.services_service import append_service, get_service, load_services, update_service
from app.services.customers_service import append_customer, load_customers, load_recent_customers, update_customer
from app.services.order_service import OrderService
from app.services.leads_service import load_leads, load_session_history_for_lead
from app.domain import Order
from app.domain.service import Service
from app.domain.customer import Customer

from app.web_services_api.routes_order import web_services_router
from app.llm.controllers.chat_router import chat_router
from app.llm.rag.rag_retriever import build_or_load_vectorstore, get_vectorstore_summary
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

RUNTIME_DATA_DIR.mkdir(parents=True, exist_ok=True)

if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("Set OPENAI_API_KEY in your environment or .env file first.")


app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Serve the web-office template at /web-office/web-office.html
@app.get("/web-office/web-office.html", response_class=HTMLResponse)
async def web_office(request: Request):
    services = load_services()
    customers = load_recent_customers(WEB_OFFICE_CUSTOMERS_LIST_LIMIT)
    orders = OrderService.list_recent_orders(limit=3)
    service_lookup = {service.id: service.name for service in services}
    customer_lookup = {
        customer.id: f"{customer.first_name} {customer.last_name}"
        for customer in customers
    }
    order_items = []
    for order in orders:
        order_items.append(
            {
                "id": order.id,
                "customer_name": customer_lookup.get(order.customer_id, order.customer_id),
                "service_name": service_lookup.get(order.service_id, order.service_id),
                "provider_name": order.provider_id,
                "start_time": order.start_time,
                "end_time": order.end_time,
                "status": order.status.value,
                "details": order.details,
            }
        )

    return templates.TemplateResponse(
        request,
        "web-office/web-office.html",
        {"services": services, "customers": customers, "orders": order_items},
    )


@app.get("/web-office/leads-list.html", response_class=HTMLResponse)
async def leads_list_page(request: Request):
    leads = load_leads()
    return templates.TemplateResponse(request, "web-office/leads-list.html", {"leads": leads})


@app.get("/web-office/lead-chat-details.html", response_class=HTMLResponse)
async def chat_details_page(request: Request):
    lead_index = request.query_params.get("leadIndex")
    try:
        index = int(lead_index) if lead_index is not None else None
    except ValueError:
        index = None

    leads = load_leads()
    lead = leads[index] if index is not None and 0 <= index < len(leads) else None
    lead_session_id = None
    if lead:
        for key in ("captured_in_session_id", "capturedInSessionId", "session_id", "sessionId"):
            lead_session_id = lead.get(key)
            if lead_session_id:
                break

    return templates.TemplateResponse(
        request,
        "web-office/lead-chat-details.html",
        {
            "lead": lead,
            "lead_index": index,
            "leads": leads,
            "lead_session_id": lead_session_id,
            "session_history": load_session_history_for_lead(lead),
        },
    )


@app.get("/web-office/create-edit-service.html", response_class=HTMLResponse)
async def create_service(request: Request):
    service_id = request.query_params.get("service_id")
    service = get_service(service_id) if service_id else None
    return templates.TemplateResponse(request, "web-office/create-edit-service.html", {"service": service})


@app.post("/web-office/create-edit-service")
async def create_service_post(request: Request):
    form = await request.form()
    service_id = form.get("id")
    payload = {
        "business_id": form.get("business_id", ""),
        "service_type": form.get("service_type", ""),
        "service_sub_type": form.get("service_sub_type", ""),
        "name": form.get("name", ""),
        "description": form.get("description", ""),
    }
    if service_id:
        payload["id"] = service_id

    service = Service(**payload)

    if service_id:
        update_service(service)
    else:
        append_service(service)

    return RedirectResponse(url="/web-office/web-office.html", status_code=303)


@app.get("/web-office/create-edit-order.html", response_class=HTMLResponse)
async def create_order(request: Request):
    order_id = request.query_params.get("order_id")
    order = OrderService.get_order(order_id) if order_id else None
    services = load_services()
    customers = load_customers()
    return templates.TemplateResponse(
        request,
        "web-office/create-edit-order.html",
        {"services": services, "customers": customers, "order": order},
    )


@app.post("/web-office/create-edit-order")
async def create_order_post(request: Request):
    form = await request.form()
    order_id = form.get("id")
    start_time = form.get("start_time", "")
    end_time = form.get("end_time", "")

    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid date/time: {exc}") from exc

    if start >= end:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")

    provider_id = form.get("provider_id", "")
    payload = {
        "id": order_id or None,
        "customer_id": form.get("customer_id", ""),
        "service_id": form.get("service_id", ""),
        "provider_id": provider_id or None,
        "start_time": start,
        "end_time": end,
        "details": form.get("details", ""),
    }
    order = Order(**payload)

    if order_id:
        OrderService.update_order(order_id, order)
    else:
        OrderService.create_order(order)

    return RedirectResponse(url="/web-office/web-office.html", status_code=303)


@app.get("/web-office/orders-list.html", response_class=HTMLResponse)
async def orders_list_page(request: Request):
    services = load_services()
    customers = load_recent_customers(WEB_OFFICE_CUSTOMERS_LIST_LIMIT)
    orders = OrderService.list_orders()
    service_lookup = {service.id: service.name for service in services}
    customer_lookup = {
        customer.id: f"{customer.first_name} {customer.last_name}"
        for customer in customers
    }
    order_items = []
    for order in orders:
        order_items.append(
            {
                "id": order.id,
                "customer_name": customer_lookup.get(order.customer_id, order.customer_id),
                "service_name": service_lookup.get(order.service_id, order.service_id),
                "provider_name": order.provider_id,
                "start_time": order.start_time,
                "end_time": order.end_time,
                "status": order.status.value,
                "details": order.details,
            }
        )
    return templates.TemplateResponse(request, "web-office/orders-list.html", {"orders": order_items})


@app.get("/web-office/customers-list.html", response_class=HTMLResponse)
async def customers_list_page(request: Request):
    customers = sorted(load_customers(), key=lambda customer: customer.created_at, reverse=True)
    return templates.TemplateResponse(request, "web-office/customers-list.html", {"customers": customers})


@app.get("/web-office/create-edit-customer.html", response_class=HTMLResponse)
async def create_customer(request: Request):
    customer_id = request.query_params.get("customer_id")
    customer = None
    if customer_id:
        customer = next((c for c in load_customers() if c.id == customer_id), None)
    return templates.TemplateResponse(request, "web-office/create-edit-customer.html", {"customer": customer})


@app.post("/web-office/create-edit-customer")
async def create_customer_post(request: Request):
    form = await request.form()
    customer_id = form.get("id")
    payload = {
        "id": customer_id,
        "first_name": form.get("first_name", ""),
        "last_name": form.get("last_name", ""),
        "email": form.get("email", None),
        "phone": form.get("phone", None),
    }
    customer = Customer(**payload)

    if customer_id:
        update_customer(customer)
    else:
        append_customer(customer)

    return RedirectResponse(url="/web-office/web-office.html", status_code=303)


@app.get("/chatbot.html", response_class=HTMLResponse)
async def chatbot(request: Request):
    return templates.TemplateResponse(request, "/chatbot.html", {})

@app.get("/admin/admin.html", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse(request, "admin/admin.html", {})


@app.get("/admin/rag-summary.html", response_class=HTMLResponse)
async def rag_summary_page(request: Request):
    summary = get_vectorstore_summary()
    return templates.TemplateResponse(request, "admin/rag-summary.html", {"summary": summary})


@app.post("/admin/init-rag")
async def init_rag(request: Request):
    """Initialize or rebuild the RAG vector DB from workspace files.

    Expects JSON body: { "force": false }
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    force = bool(body.get("force", False))
    try:
        build_or_load_vectorstore(force_rebuild=force)
        return {"status": "ok", "message": "RAG vector DB initialized"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.get("/admin/rag-status")
async def rag_status():
    """Return whether the RAG vector DB appears initialized."""
    try:
        p = Path(DB_RAG_VECTOR_DIR)
        initialized = p.exists() and any(p.iterdir())
        return {"initialized": bool(initialized), "path": str(p)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


#REST services endpoints for orders
app.include_router(web_services_router, prefix="/ws-api", tags=["ws-api"])

#REST services endpoints for chat
app.include_router(chat_router, prefix="/chat-api", tags=["chat-api"])


@app.get("/favicon.ico")
async def favicon():
    return FileResponse(FAVICON_PATH)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Simple landing page for the web app."""
    return templates.TemplateResponse(request, "index.html", {})
