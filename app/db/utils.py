from app.db.session import SessionLocal
from app.db import models
import pandas as pd
import app.routers.customers
from app.routers.customers import (
    customer_exists_by_name,
    create_customer,
    get_customer_by_name,
)


def save_df_to_db(df: pd.DataFrame, customer_name: str):
    session = SessionLocal()
    try:
        customer_id = (
            get_customer_by_name(customer_name)
            if customer_exists_by_name(customer_name) is not None
            else create_customer(customer_name)
        )

        records = df.to_dict(orient="records")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
