import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
INVOICES_DIR = Path(os.getenv("INVOICES_DIR", DATA_DIR / "invoices"))
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", DATA_DIR / "uploads"))
for p in (DATA_DIR, INVOICES_DIR, UPLOADS_DIR):
    p.mkdir(parents=True, exist_ok=True)
