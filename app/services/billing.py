from datetime import datetime
import io
import pandas as pd

def parse_csv(file_bytes: bytes):
    df = pd.read_csv(io.BytesIO(file_bytes))
    # Expect columns: timestamp, Poraba [kWh], Dinamične Cene [EUR/kWh], customer_id (or location)
    # Normalize headers (example)
    cols = {c.lower().strip(): c for c in df.columns}
    # Basic validation
    required = ["timestamp", "poraba [kwh]", "dinamične cene [eur/kwh]"]
    missing = [r for r in required if r not in [c.lower() for c in df.columns]]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    # Parse dates
    df["timestamp"] = pd.to_datetime(df[cols.get("timestamp", "timestamp")])
    return df

def compute_total(df, start: datetime, end: datetime):
    mask = (df["timestamp"] >= pd.to_datetime(start)) & (df["timestamp"] <= pd.to_datetime(end))
    sel = df.loc[mask].copy()
    sel["cost"] = sel["Poraba [kWh]"] * sel["Dinamične Cene [EUR/kWh]"]
    return float(sel["cost"].sum()), len(sel)
