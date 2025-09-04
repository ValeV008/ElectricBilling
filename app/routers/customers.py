from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def is_hx(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"

# Demo dataset
CUSTOMERS = [
    {"id": 1, "name": "ACME d.o.o.", "meter_code": "MTR-001", "last_period": "2025-08"},
    {"id": 2, "name": "Beta d.o.o.", "meter_code": "MTR-002", "last_period": "2025-08"},
]

@router.get("", response_class=HTMLResponse)
def list_customers(request: Request):
    tmpl = "customers/_table.html" if is_hx(request) else "customers/list.html"
    return templates.TemplateResponse(tmpl, {"request": request, "customers": CUSTOMERS, "period_start": "2025-08-01", "period_end": "2025-08-31"})
