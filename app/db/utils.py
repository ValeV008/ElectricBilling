from app.db.session import SessionLocal
from app.db import models
import pandas as pd
import app.routers.customers
from app.routers.customers import (
    customer_exists_by_name,
    create_customer,
    get_customer_by_name,
)
from sqlalchemy import insert
from datetime import datetime
import pytz
from sqlalchemy.dialects.postgresql import insert as pg_insert


def parse_timestamp(value: str):
    """Parse timestamps coming from uploaded file. Accepts ISO-like strings with timezone names
    'Časovna Značka (CEST/CET)' may contain values like '2025-09-01 12:00:00 CEST'. We'll try
    common formats and fallback to pandas parsing.
    """
    if value is None:
        return None
    try:
        # Try pandas first (handles many formats)
        ts = pd.to_datetime(value)
        if ts.tzinfo is None:
            # assume local Europe/Prague timezone if no tz info (CEST/CET is central european)
            tz = pytz.timezone("Europe/Prague")
            ts = tz.localize(ts)
        # convert to naive UTC-aware datetime in DB (SQLAlchemy DateTime without timezone)
        return ts.astimezone(pytz.UTC).replace(tzinfo=None)
    except Exception:
        try:
            # last resort: parse with datetime.fromisoformat
            ts = datetime.fromisoformat(value)
            if ts.tzinfo is not None:
                return ts.astimezone(pytz.UTC).replace(tzinfo=None)
            else:
                tz = pytz.timezone("Europe/Prague")
                return tz.localize(ts).astimezone(pytz.UTC).replace(tzinfo=None)
        except Exception:
            return None


def save_df_to_db(df: pd.DataFrame, customer_name: str):
    session = SessionLocal()
    try:
        # create or get customer
        customer_id = None
        if customer_exists_by_name(customer_name):
            print(f"Customer '{customer_name}' exists.")
            customer_id = get_customer_by_name(customer_name)
        else:
            print(f"Customer '{customer_name}' does not exist. Creating new customer.")
            customer_id = create_customer(customer_name)

        if customer_id is None:
            raise RuntimeError("Failed to determine or create customer")

        # add customer_id to each record
        records = df.to_dict(orient="records")
        rows_to_insert = []
        for record in records:
            ts_raw = record.get("Časovna Značka (CEST/CET)")
            ts = parse_timestamp(ts_raw)
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

        if rows_to_insert:
            stmt = pg_insert(models.ConsumptionRecord).values(rows_to_insert)
            stmt = stmt.on_conflict_do_nothing(index_elements=["customer_id", "ts"])
            session.execute(stmt)
            session.commit()
            print(
                f"Inserted {len(rows_to_insert)} consumption_records for customer {customer_id}"
            )

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
