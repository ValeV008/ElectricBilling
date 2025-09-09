"""Billing related services."""

from datetime import datetime
import io
import pandas as pd


def validate_csv(df: pd.DataFrame) -> bool:
    """Validate the structure and content of the CSV file."""
    if df.empty:
        return False

    required = ["Časovna Značka (CEST/CET)", "Poraba [kWh]", "Dinamične Cene [EUR/kWh]"]
    cols_missing = any(r not in df.columns for r in required)
    if cols_missing:
        return False
    if df["Poraba [kWh]"].isnull().any():
        return False
    if df["Dinamične Cene [EUR/kWh]"].isnull().any():
        return False
    if df["Časovna Značka (CEST/CET)"].isnull().any():
        return False

    return True


def parse_csv(file_bytes: bytes) -> pd.DataFrame:
    """Parse the uploaded CSV file and return a DataFrame."""
    df = pd.read_csv(io.BytesIO(file_bytes), sep=";", decimal=",", encoding="utf-8")
    is_valid = validate_csv(df)
    if not is_valid:
        raise ValueError("CSV validation failed")
    return df


def compute_total(df, start: datetime, end: datetime) -> tuple[float, int]:
    """Compute the total cost and number of records in the given date range."""
    mask = (df["timestamp"] >= pd.to_datetime(start)) & (
        df["timestamp"] <= pd.to_datetime(end)
    )
    sel = df.loc[mask].copy()
    sel["cost"] = sel["Poraba [kWh]"] * sel["Dinamične Cene [EUR/kWh]"]
    return float(sel["cost"].sum()), len(sel)
