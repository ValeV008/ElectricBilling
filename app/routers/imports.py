"""Routes for importing consumption data from CSV files."""

from fastapi import APIRouter, Request, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services import billing
import os
import pandas as pd
import uuid
from app.db.utils import (
    insert_or_update_consumption_records,
    parse_timestamp,
    ensure_utc,
)
from app.routers.customers import (
    customer_exists_by_name,
    create_customer,
    get_customer_id_by_name,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# in-memory store to hold uploaded file bytes between preview -> commit
TEMP_UPLOADS = {}


def is_hx(request: Request) -> bool:
    """Return True if the request is an HTMX request."""
    return request.headers.get("hx-request") == "true"


@router.get("", response_class=HTMLResponse)
def upload_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("imports/upload.html", {"request": request})


@router.post("/preview", response_class=HTMLResponse)
async def preview(request: Request, file: UploadFile):
    """Handle uploaded CSV file, parse and validate it, and show a preview."""
    content = await file.read()
    try:
        df = billing.parse_csv(content)
    except Exception as e:
        frag = (
            f'<div class="p-3 bg-red-50 border border-red-300 rounded">Error: {e}</div>'
        )
        return HTMLResponse(frag, status_code=400)
    rows = len(df)
    start = df["Časovna Značka (CEST/CET)"].min()
    end = df["Časovna Značka (CEST/CET)"].max()
    customer = os.path.splitext(file.filename)[0]  # type: ignore

    # persist raw bytes in-memory and return a token the client will send to commit()
    token = str(uuid.uuid4())
    TEMP_UPLOADS[token] = content

    ctx = {
        "request": request,
        "rows": rows,
        "customer": customer,
        "start": start,
        "end": end,
        "token": token,
    }
    tmpl = "imports/_preview.html" if is_hx(request) else "imports/upload.html"
    return templates.TemplateResponse(tmpl, ctx)


@router.post("/commit", response_class=HTMLResponse)
async def commit(request: Request):
    """Commit the previously previewed upload to the database."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing JSON body")

    token = body.get("token")
    customer = body.get("customer")

    if not token or not customer:
        raise HTTPException(status_code=400, detail="Missing upload token or customer")

    # Look up the previously uploaded bytes by token (in-memory)
    if token not in TEMP_UPLOADS:
        raise HTTPException(status_code=400, detail="Upload token not found or expired")
    content = TEMP_UPLOADS.pop(token)

    # already validated, no need to try/except
    df = billing.parse_csv(content)

    save_df_to_db(df, customer)

    return HTMLResponse(
        '<div class="p-3 bg-green-50 border border-green-300 rounded">Import complete.</div>'
    )


def save_df_to_db(df: pd.DataFrame, customer_name: str):
    """Save the given DataFrame to the database, creating the customer if needed."""
    customer_id = None
    if customer_exists_by_name(customer_name):
        customer_id = get_customer_id_by_name(customer_name)
    else:
        customer_id = create_customer(customer_name)

    if customer_id is None:
        raise RuntimeError("Failed to get or create customer")

    # add customer_id to each record
    records = df.to_dict(orient="records")

    rows_to_insert = []
    for record in records:
        ts_raw = record.get("Časovna Značka (CEST/CET)")
        ts = parse_timestamp(ts_raw)
        ts = ensure_utc(ts)
        kwh = record.get("Poraba [kWh]")
        price = record.get("Dinamične Cene [EUR/kWh]")

        # ensure numeric
        try:
            kwh = float(kwh) if kwh is not None and kwh != "" else 0.0
        except Exception:
            kwh = 0.0
        try:
            price = float(price) if price is not None and price != "" else 0.0
        except Exception:
            price = 0.0

        row = {
            "customer_id": customer_id,
            "ts": ts,
            "kwh": kwh,
            "price_eur_per_kwh": price,
        }
        rows_to_insert.append(row)

    insert_or_update_consumption_records(rows_to_insert)
