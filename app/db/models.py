from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from .base import Base


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class ConsumptionRecord(Base):
    __tablename__ = "consumption_records"
    id = Column(Integer, primary_key=True)
    customer_id = Column(
        Integer, ForeignKey("customers.id"), index=True, nullable=False
    )
    ts = Column(
        TIMESTAMP(timezone=True), index=True, nullable=False
    )  # timestamp with timezone
    kwh = Column(Float, nullable=False)  # Poraba [kWh]
    price_eur_per_kwh = Column(Float, nullable=False)  # Dinamične Cene [EUR/kWh]
    customer = relationship("Customer")


Index(
    "ix_consumption_customer_ts",
    ConsumptionRecord.customer_id,
    ConsumptionRecord.ts,
    unique=True,
)


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True)
    customer_id = Column(
        Integer, ForeignKey("customers.id"), index=True, nullable=False
    )
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_eur = Column(Float, nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
