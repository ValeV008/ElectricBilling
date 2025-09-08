from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.config import INVOICES_DIR
from app.services.pdf import render_invoice_pdf_bytes
import io
from app.deps import get_db
from app.db.models import ConsumptionRecord, Invoice, Customer
from sqlalchemy import select, func
from datetime import datetime, timezone

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def parse_year_month(year_month: str):
    """Return (period_start_iso, period_end_iso) for a YYYY-MM string.

    If parsing fails return ("", "").
    """
    try:
        y_str, m_str = year_month.split("-")
        y = int(y_str)
        m = int(m_str)
        from datetime import datetime

        period_start_dt = datetime(y, m, 1)
        # compute first day of next month
        if m == 12:
            period_end_dt = datetime(y + 1, 1, 1)
        else:
            period_end_dt = datetime(y, m + 1, 1)
        return period_start_dt.isoformat(), period_end_dt.isoformat()
    except Exception:
        return "", ""


@router.post("/{customer_id}", response_class=HTMLResponse)
async def create_invoice(
    request: Request,
    customer_id: int,
    year_month: str = Form(...),
):
    period_start, period_end = parse_year_month(year_month)
    ps, pe = attach_timezone_to_period(period_start, period_end)

    total = 0.0
    customer_name = f"Customer {customer_id}"
    with get_db() as db:
        # try to read real customer name
        cust = db.execute(
            select(Customer).filter_by(id=customer_id)
        ).scalar_one_or_none()
        if cust:
            customer_name = cust.name

        if ps and pe:
            # convert local-aware period boundaries to UTC for DB comparisons
            try:
                ps_utc = ps.astimezone(timezone.utc)
                pe_utc = pe.astimezone(timezone.utc)
            except Exception:
                ps_utc = ps
                pe_utc = pe

            q = select(
                ConsumptionRecord.kwh,
                ConsumptionRecord.price_eur_per_kwh,
                ConsumptionRecord.ts,
            ).filter(
                ConsumptionRecord.customer_id == customer_id,
                ConsumptionRecord.ts >= ps_utc,
                ConsumptionRecord.ts < pe_utc,
            )
            rows = db.execute(q).all()
            for kwh, price, ts in rows:
                try:
                    kwh_f = float(kwh)
                    price_f = float(price)
                    line_amount = kwh_f * price_f
                    total += line_amount
                except Exception:
                    continue

            invoice_id = save_invoice(db, customer_id, ps, pe, total)

    # render PDF bytes and stream them back to the client so the browser opens
    # the PDF in a new tab
    context = {
        "invoice_number": invoice_id,
        "customer_name": customer_name,
        "period_start": period_start,
        "period_end": period_end,
        "total": round(total, 2),
    }
    pdf_bytes = render_invoice_pdf_bytes(context)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="invoice_{invoice_id}.pdf"'},
    )


def attach_timezone_to_period(period_start, period_end):
    try:
        # interpret the YYYY-MM timestamps as local (system) timezone-aware datetimes
        if period_start:
            naive_ps = datetime.fromisoformat(period_start)
        else:
            naive_ps = None
        if period_end:
            naive_pe = datetime.fromisoformat(period_end)
        else:
            naive_pe = None

        if naive_ps or naive_pe:
            local_tz = datetime.now().astimezone().tzinfo
        ps = naive_ps.replace(tzinfo=local_tz) if naive_ps else None
        pe = naive_pe.replace(tzinfo=local_tz) if naive_pe else None
    except Exception as e:
        print(f"failed to parse/attach tz to period start/end: {e}")
        ps = pe = None
    return ps, pe


def save_invoice(db, customer_id, ps, pe, total):
    """Persist an Invoice and return invoice_id.

    db: active DB session
    """
    invoice = Invoice(
        customer_id=customer_id,
        period_start=ps or datetime.now(timezone.utc),
        period_end=pe or datetime.now(timezone.utc),
        total_eur=total,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice.id


@router.get("/{invoice_id}/pdf")
def get_pdf(invoice_id: int):
    path = INVOICES_DIR / f"{invoice_id}.pdf"
    if not path.exists():
        return HTMLResponse("Not found", status_code=404)
    return StreamingResponse(open(path, "rb"), media_type="application/pdf")
