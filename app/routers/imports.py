from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services import billing

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def is_hx(request: Request) -> bool:
    return request.headers.get("hx-request") == "true"

@router.get("", response_class=HTMLResponse)
def upload_page(request: Request):
    return templates.TemplateResponse("imports/upload.html", {"request": request})

@router.post("/preview", response_class=HTMLResponse)
async def preview(request: Request, file: UploadFile):
    content = await file.read()
    try:
        df = billing.parse_csv(content)
    except Exception as e:
        frag = f'<div class="p-3 bg-red-50 border border-red-300 rounded">Error: {e}</div>'
        return HTMLResponse(frag, status_code=400)
    rows = len(df)
    start = df["timestamp"].min()
    end = df["timestamp"].max()
    ctx = {"request": request, "rows": rows, "customers": "—", "start": start, "end": end, "token": "demo-token"}
    tmpl = "imports/_preview.html" if is_hx(request) else "imports/upload.html"
    return templates.TemplateResponse(tmpl, ctx)

@router.post("/commit", response_class=HTMLResponse)
async def commit(request: Request):
    # Stub: persist parsed data (out of scope for starter)
    return HTMLResponse('<div class="p-3 bg-green-50 border border-green-300 rounded">Import complete.</div>')
