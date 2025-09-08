from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from app.routers import imports, customers, invoices
from app.deps import get_db
from app.db.models import Customer

app = FastAPI(title="Electricity Billing")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(imports.router, prefix="/imports", tags=["imports"])
app.include_router(customers.router, prefix="/customers", tags=["customers"])
app.include_router(invoices.router, prefix="/invoices", tags=["invoices"])


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/healthz")
def healthz():
    return {"ok": True}
