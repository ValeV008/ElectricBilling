"""initial tables

Revision ID: 0001_initial
Revises:
Create Date: 2025-09-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
    )

    op.create_table(
        "consumption_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False
        ),
        sa.Column("ts", sa.DateTime(), nullable=False),
        sa.Column("kwh", sa.Float(), nullable=False),
        sa.Column("price_eur_per_kwh", sa.Float(), nullable=False),
    )

    op.create_index(
        "ix_consumption_customer_ts", "consumption_records", ["customer_id", "ts"]
    )

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False
        ),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("total_eur", sa.Float(), nullable=False),
    )


def downgrade():
    op.drop_table("invoices")
    op.drop_index("ix_consumption_customer_ts", table_name="consumption_records")
    op.drop_table("consumption_records")
    op.drop_table("customers")
