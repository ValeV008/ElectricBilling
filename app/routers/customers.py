from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from app.deps import get_db
from app.db.models import Customer
from sqlalchemy import select, func
from app.db.models import ConsumptionRecord
from sqlalchemy import extract
from app import config

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def is_hx(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"


@router.get("", response_class=HTMLResponse)
def list_customers(request: Request):
    try:
        with get_db() as db:
            customers = db.execute(select(Customer)).scalars().all()
            customers_data = []
            for c in customers:
                months = get_customer_months(c.id)
                customers_data.append({"id": c.id, "name": c.name, "months": months})
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


# Helper functions (return raw Python types) -------------------------------------------------


def customer_exists_by_name(customer_name: str) -> bool:
    """Return True if a customer with given name exists. Pure function usable by other modules."""
    print(f"Checking if customer exists by name: {customer_name}")
    try:
        with get_db() as db:
            exists = (
                db.execute(select(Customer).filter_by(name=customer_name)).first()
                is not None
            )
            print(f"Exists: {exists}")
    except Exception as e:
        print(f"Exception in customer_exists_by_name: {e}")
        exists = False
    return exists


def get_customer_by_name(customer_name: str):
    """Return customer id if found, else None."""
    print(f"Getting customer by name: {customer_name}")
    try:
        with get_db() as db:
            customer = db.execute(
                select(Customer).filter_by(name=customer_name)
            ).scalar_one_or_none()
            print(f"Customer: {customer}")
            return customer.id if customer else None
    except Exception as e:
        print(f"Exception in get_customer_by_name: {e}")
        return None


def create_customer(customer_name: str):
    """Create a customer and return its id, or None on failure."""
    print(f"Creating customer with name: {customer_name}")
    try:
        with get_db() as db:
            customer = Customer(name=customer_name)
            db.add(customer)
            db.commit()
            db.refresh(customer)
            print(f"Created customer with id: {customer.id}")
            return customer.id
    except Exception as e:
        print(f"Exception in create_customer: {e}")
        return None


def get_customer_months(customer_id: int):
    """Return a sorted list of month strings 'YYYY-MM' for which the customer has consumption records.

    Returns an empty list on error or if no records found.
    """
    try:
        with get_db() as db:
            # Extract year and month from ts adjusted to configured timezone so months
            # reflect local wall time rather than UTC storage.
            local_ts = func.timezone(config.TZ, ConsumptionRecord.ts)
            q = (
                select(
                    extract("year", local_ts).label("y"),
                    extract("month", local_ts).label("m"),
                )
                .filter(ConsumptionRecord.customer_id == customer_id)
                .group_by("y", "m")
                .order_by("y", "m")
            )
            rows = db.execute(q).all()
            months = []
            for y, m in rows:
                # extract() may return Decimal/float depending on DB driver; convert to int
                try:
                    yi = int(y)
                    mi = int(m)
                except Exception:
                    continue
                months.append(f"{yi:04d}-{mi:02d}")
            return months
    except Exception as e:
        print(f"Exception in get_customer_months: {e}")
        return []


# Route wrappers (call helpers and return PlainTextResponse) --------------------------------


@router.get("/exists/{customer_name}", response_class=PlainTextResponse)
def customer_exists_route(customer_name: str):
    print(f"Route: check if customer exists: {customer_name}")
    exists = customer_exists_by_name(customer_name)
    print(f"Route result: {exists}")
    return PlainTextResponse("1" if exists else "0")


@router.get("/{customer_name}", response_class=PlainTextResponse)
def get_customer_route(customer_name: str):
    print(f"Route: get customer id by name: {customer_name}")
    cid = get_customer_by_name(customer_name)
    print(f"Route result: {cid}")
    return PlainTextResponse(str(cid) if cid is not None else "")


@router.post("/create", response_class=PlainTextResponse)
def create_customer_route(name: str) -> PlainTextResponse:
    print(f"Route: create customer with name: {name}")
    if customer_exists_by_name(name):
        print("Customer already exists.")
        return PlainTextResponse("exists")
    cid = create_customer(name)
    if cid is None:
        print("Failed to create customer.")
        return PlainTextResponse("")
    print(f"Customer created with id: {cid}")
    return PlainTextResponse(str(cid))
