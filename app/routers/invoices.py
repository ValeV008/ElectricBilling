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
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# module logger
logger = logging.getLogger(__name__)


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
    logger.debug(
        "create_invoice called: customer_id=%s year_month=%s -> period_start=%s period_end=%s",
        customer_id,
        year_month,
        period_start,
        period_end,
    )

    # Query DB for consumption records in the period and compute total
    # period_start/period_end are ISO strings; convert to datetimes for DB compare
    try:
        ps = datetime.fromisoformat(period_start) if period_start else None
        pe = datetime.fromisoformat(period_end) if period_end else None
    except Exception as e:
        logger.debug("failed to parse period start/end: %s", e)
        ps = pe = None

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
            q = select(
                ConsumptionRecord.kwh,
                ConsumptionRecord.price_eur_per_kwh,
            ).filter(
                ConsumptionRecord.customer_id == customer_id,
                ConsumptionRecord.ts >= ps,
                ConsumptionRecord.ts < pe,
            )
            rows = db.execute(q).all()
            logger.debug("consumption rows fetched: %d", len(rows))
            line_index = 0
            for kwh, price in rows:
                line_index += 1
                try:
                    kwh_f = float(kwh)
                    price_f = float(price)
                    line_amount = kwh_f * price_f
                    total += line_amount
                    logger.debug(
                        "line %d: kwh=%s price=%s line_amount=%s running_total=%s",
                        line_index,
                        kwh,
                        price,
                        line_amount,
                        total,
                    )
                except Exception as e:
                    logger.debug(
                        "skipping row %d due to conversion error: %s (kwh=%r price=%r)",
                        line_index,
                        e,
                        kwh,
                        price,
                    )
                    continue

        # persist invoice record
        logger.debug("subtotal before persist: %s", total)

        invoice = Invoice(
            customer_id=customer_id,
            period_start=ps or datetime.now(timezone.utc),
            period_end=pe or datetime.now(timezone.utc),
            total_eur=total,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        invoice_id = invoice.id
        logger.debug(
            "invoice persisted: id=%s stored_total=%s rounded_display=%s",
            invoice_id,
            invoice.total_eur,
            round(total, 2),
        )
        rounded_total = round(total, 2)
        try:
            rounding_diff = rounded_total - total
            logger.debug(
                "rounding diff: %s (rounded %s - raw %s)",
                rounding_diff,
                rounded_total,
                total,
            )
        except Exception:
            pass

    # render PDF bytes and stream them back to the client so the browser opens
    # the PDF in a new tab (no server-side file required)
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


@router.get("/{invoice_id}/pdf")
def get_pdf(invoice_id: int):
    path = INVOICES_DIR / f"{invoice_id}.pdf"
    if not path.exists():
        return HTMLResponse("Not found", status_code=404)
    return StreamingResponse(open(path, "rb"), media_type="application/pdf")
