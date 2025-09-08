from fastapi import APIRouter, Request, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services import billing
import os
import uuid
from pathlib import Path
from app.db.utils import save_df_to_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# directory to hold uploaded file bytes between preview -> commit
TMP_DIR = Path("tmp_uploads")
TMP_DIR.mkdir(exist_ok=True)


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
    # Extract customer from file name (without extension)

    # persist raw bytes to a temp file and return a token the client will send to commit()
    token = str(uuid.uuid4())
    tmp_path = TMP_DIR / token
    tmp_path.write_bytes(content)

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
    # Look up the previously uploaded bytes by token
    tmp_path = TMP_DIR / token
    if not tmp_path.exists():
        raise HTTPException(status_code=400, detail="Upload token not found or expired")

    content = tmp_path.read_bytes()

    # Optionally remove the temp file now that we've read it
    try:
        tmp_path.unlink()
    except Exception:
        pass

    # Re-parse and persist (this is still a stub for actual persistence)
    try:
        df = billing.parse_csv(content)
        # TODO: persist `df` into DB or other storage
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to parse uploaded file: {e}"
        )

    save_df_to_db(df, customer)

    return HTMLResponse(
        '<div class="p-3 bg-green-50 border border-green-300 rounded">Import complete.</div>'
    )
