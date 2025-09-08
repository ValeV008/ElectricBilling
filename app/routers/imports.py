from fastapi import APIRouter, Request, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services import billing
import os
import uuid
from app.db.utils import save_df_to_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# in-memory store to hold uploaded file bytes between preview -> commit
# token -> bytes
TEMP_UPLOADS = {}


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
        frag = (
            f'<div class="p-3 bg-red-50 border border-red-300 rounded">Error: {e}</div>'
        )
        return HTMLResponse(frag, status_code=400)
    rows = len(df)
    start = df["Časovna Značka (CEST/CET)"].min()
    end = df["Časovna Značka (CEST/CET)"].max()
    customer = os.path.splitext(file.filename)[0]

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
async def commit(request: Request, token: str = Form(...), customer: str = Form(...)):
    # Look up the previously uploaded bytes by token (in-memory)
    if token not in TEMP_UPLOADS:
        raise HTTPException(status_code=400, detail="Upload token not found or expired")
    content = TEMP_UPLOADS.pop(token)

    try:
        df = billing.parse_csv(content)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to parse uploaded file: {e}"
        )

    save_df_to_db(df, customer)

    return HTMLResponse(
        '<div class="p-3 bg-green-50 border border-green-300 rounded">Import complete.</div>'
    )
