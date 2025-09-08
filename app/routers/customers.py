from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from app.deps import get_db
from app.db.models import Customer
from sqlalchemy import select, func

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def is_hx(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"


@router.get("", response_class=HTMLResponse)
def list_customers(request: Request):
    try:
        with get_db() as db:
            customers = db.execute(select(Customer)).scalars().all()
            customers_data = [{"id": c.id, "name": c.name} for c in customers]
    except Exception:
        customers_data = []

    tmpl = "customers/_table.html" if is_hx(request) else "customers/list.html"
    return templates.TemplateResponse(
        tmpl,
        {
            "request": request,
            "customers": customers_data,
        },
    )


@router.get("/count", response_class=PlainTextResponse)
def customers_count():
    try:
        with get_db() as db:
            total = db.scalar(select(func.count()).select_from(Customer)) or 0
    except Exception:
        total = 0
    return PlainTextResponse(str(total))


@router.get("/exists/{customer_name}", response_class=PlainTextResponse)
def customer_exists_by_name(customer_name: str):
    try:
        with get_db() as db:
            exists = (
                db.execute(
                    select(Customer).filter_by(Customer.name == customer_name)
                ).first()
                is not None
            )
    except Exception:
        exists = False
    return PlainTextResponse(exists)


@router.get("/{customer_name}", response_class=PlainTextResponse)
def get_customer_by_name(name: str):
    with get_db() as db:
        return db.execute(select(Customer).filter_by(name=name)).scalar_one_or_none()


@router.post("/create", response_class=PlainTextResponse)
def create_customer(name: str) -> PlainTextResponse:
    if customer_exists_by_name(name):
        return PlainTextResponse("exists")
    try:
        with get_db() as db:
            customer = Customer(name=name)
            db.add(customer)
            db.commit()
            db.refresh(customer)
            return PlainTextResponse(str(customer.id))
    except Exception:
        return Exception("Failed to create customer")
