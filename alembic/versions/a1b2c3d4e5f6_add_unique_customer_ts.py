"""add unique constraint on consumption_records (customer_id, ts)

Revision ID: a1b2c3d4e5f6
Revises: 9f1a2b3c4d5e
Create Date: 2025-09-08 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "9f1a2b3c4d5e"
branch_labels = None
depends_on = None


def upgrade():
    # Remove exact duplicate rows (keep lowest id) to allow creating the unique index
    op.execute(
        """
        DELETE FROM consumption_records a
        USING consumption_records b
        WHERE a.id > b.id
          AND a.customer_id = b.customer_id
          AND a.ts = b.ts;
        """
    )

    # Create a unique index on (customer_id, ts)
    op.create_index(
        "ux_consumption_customer_ts",
        "consumption_records",
        ["customer_id", "ts"],
        unique=True,
    )


def downgrade():
    op.drop_index("ux_consumption_customer_ts", table_name="consumption_records")
