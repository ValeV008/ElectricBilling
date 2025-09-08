"""convert ts to timestamptz

Revision ID: c2d3e4f5g6h7
Revises: 0001_initial
Create Date: 2025-09-08 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c2d3e4f5g6h7"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # Interpret existing naive timestamps in ts as Europe/Prague local wall time
    # and convert them to timestamptz (stored in UTC).
    op.execute(
        """
        ALTER TABLE consumption_records
        ALTER COLUMN ts TYPE timestamptz
        USING (ts AT TIME ZONE 'Europe/Prague')
        """
    )


def downgrade():
    # Convert timestamptz back to naive timestamp, expressing values in UTC
    op.execute(
        """
        ALTER TABLE consumption_records
        ALTER COLUMN ts TYPE timestamp without time zone
        USING (ts AT TIME ZONE 'UTC')
        """
    )
