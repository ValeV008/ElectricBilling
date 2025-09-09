from app.db import models
import pandas as pd
from app.deps import get_db
from app.routers.customers import (
    customer_exists_by_name,
    create_customer,
    get_customer_id_by_name,
)
from sqlalchemy import cast, insert
from datetime import datetime
from typing import Optional
import pytz
from app import config
from sqlalchemy.dialects.postgresql import insert as pg_insert


def parse_timestamp(value: Optional[str]):
    """Parse timestamps coming from uploaded file. Accepts ISO-like strings with timezone names
    'Časovna Značka (CEST/CET)' may contain values like '2025-09-01 12:00:00 CEST'. We'll try
    common formats and fallback to pandas parsing.
    """
    if value is None:
        return None
    try:
        # Try pandas first (handles many formats)
        ts = pd.to_datetime(value)
        # convert to python datetime for consistent tzinfo handling
        try:
            dt = ts.to_pydatetime()
        except Exception:
            dt = ts

        # If the parsed datetime has timezone info, convert to UTC
        if getattr(dt, "tzinfo", None) is not None:
            return dt.astimezone(pytz.UTC)

        # If no tzinfo was present, assume local configured timezone and
        # convert to UTC for canonical storage.
        tz = pytz.timezone(config.TZ)
        localized = tz.localize(dt)
        return localized.astimezone(pytz.UTC)
    except Exception:
        try:
            # last resort: parse with datetime.fromisoformat
            ts = datetime.fromisoformat(value)
            if ts.tzinfo is not None:
                return ts.astimezone(pytz.UTC)
            else:
                tz = pytz.timezone(config.TZ)
                localized = tz.localize(ts)
                return localized.astimezone(pytz.UTC)
        except Exception:
            return None


def ensure_utc(dt):
    """Ensure a datetime is timezone-aware in UTC.

    If dt is None, returns None. If dt has tzinfo, convert to UTC.
    If dt is naive, assume configured local timezone (`app.config.TZ`) and convert to UTC.
    """
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is None:
        tz = pytz.timezone(config.TZ)
        dt = tz.localize(dt)
    return dt.astimezone(pytz.UTC)


def save_df_to_db(df: pd.DataFrame, customer_name: str):
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


def insert_or_update_consumption_records(records: list[dict]):
    if not records:
        return

    with get_db() as db:
        stmt = pg_insert(models.ConsumptionRecord).values(records)
        stmt = stmt.on_conflict_do_update(
            index_elements=["customer_id", "ts"],
            set_={
                "kwh": stmt.excluded.kwh,
                "price_eur_per_kwh": stmt.excluded.price_eur_per_kwh,
            },
        )
        db.execute(stmt)
        db.commit()
        print(f"Upserted {len(records)} consumption_records")
