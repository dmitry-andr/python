from datetime import datetime, timezone
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.utils.config import APP_NAME, APP_VERSION, FAVICON_PATH, STATIC_DIR, TEMPLATES_DIR
from app.services.services_service import append_service, load_services
from app.services.customers_service import append_customer, load_customers
from app.services.order_service import OrderService
from app.domain import Order
from app.domain.service import Service
from app.domain.customer import Customer

from app.web_services_api.routes_order import web_services_router
from app.llm.controllers.chat_router import chat_router
from app.llm.rag.rag_retriever import build_or_load_vectorstore, get_vectorstore_summary
from pathlib import Path
from app.utils.config import BASE_DIR, VECTOR_DB_DIR
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise SystemExit("Set OPENAI_API_KEY in your environment or .env file first.")


app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Serve the web-office template at /web-office/web-office.html
@app.get("/web-office/web-office.html", response_class=HTMLResponse)
async def web_office(request: Request):
    services = load_services()
    customers = load_customers()
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

    return templates.TemplateResponse(
        request,
        "web-office/web-office.html",
        {"services": services, "customers": customers, "orders": order_items},
    )


@app.get("/web-office/create-service.html", response_class=HTMLResponse)
async def create_service(request: Request):
    return templates.TemplateResponse(request, "web-office/create-service.html", {})


@app.post("/web-office/create-service")
async def create_service_post(request: Request):
    form = await request.form()
    payload = {
        "business_id": form.get("business_id", ""),
        "service_type": form.get("service_type", ""),
        "service_sub_type": form.get("service_sub_type", ""),
        "name": form.get("name", ""),
        "description": form.get("description", ""),
    }
    service = Service(**payload)

    append_service(service)

    return RedirectResponse(url="/web-office/web-office.html", status_code=303)


@app.get("/web-office/create-order.html", response_class=HTMLResponse)
async def create_order(request: Request):
    services = load_services()
    customers = load_customers()
    return templates.TemplateResponse(
        request,
        "web-office/create-order.html",
        {"services": services, "customers": customers},
    )


@app.post("/web-office/create-order")
async def create_order_post(request: Request):
    form = await request.form()
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

    payload = {
        "customer_id": form.get("customer_id", ""),
        "service_id": form.get("service_id", ""),
        "provider_id": form.get("provider_id", ""),
        "start_time": start,
        "end_time": end,
        "details": form.get("details", ""),
    }
    order = Order(**payload)
    OrderService.create_order(order)

    return RedirectResponse(url="/web-office/web-office.html", status_code=303)


@app.get("/web-office/create-customer.html", response_class=HTMLResponse)
async def create_customer(request: Request):
    return templates.TemplateResponse(request, "web-office/create-customer.html", {})


@app.post("/web-office/create-customer")
async def create_customer_post(request: Request):
    form = await request.form()
    payload = {
        "first_name": form.get("first_name", ""),
        "last_name": form.get("last_name", ""),
        "email": form.get("email", None),
        "phone": form.get("phone", None),
    }
    customer = Customer(**payload)

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
        p = Path(VECTOR_DB_DIR)
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
