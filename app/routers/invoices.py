from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from app.config import INVOICES_DIR
from app.services.pdf import render_invoice_pdf
import io

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.post("/{customer_id}", response_class=HTMLResponse)
async def create_invoice(
    request: Request,
    customer_id: int,
    period_start: str = Form(...),
    period_end: str = Form(...),
):
    # Stub: compute total and persist invoice, here we just create a PDF with dummy data
    invoice_id = 1_000 + customer_id
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = INVOICES_DIR / f"{invoice_id}.pdf"
    context = {
        "invoice_number": invoice_id,
        "customer_name": f"Customer {customer_id}",
        "period_start": period_start,
        "period_end": period_end,
        "total": 123.45,
    }
    render_invoice_pdf(context, str(out_path))
    # Return a row fragment (minimal)
    return templates.TemplateResponse(
        "customers/_row_generated.html",
        {
            "request": request,
            "c": {
                "id": customer_id,
                "name": f"Customer {customer_id}",
                "invoice_total": 123.45,
                "invoice_id": invoice_id,
            },
            "period_start": period_start,
            "period_end": period_end,
        },
    )


@router.get("/{invoice_id}/pdf")
def get_pdf(invoice_id: int):
    path = INVOICES_DIR / f"{invoice_id}.pdf"
    if not path.exists():
        return HTMLResponse("Not found", status_code=404)
    return StreamingResponse(open(path, "rb"), media_type="application/pdf")
