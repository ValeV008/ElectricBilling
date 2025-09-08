"""seed customers

Revision ID: 9f1a2b3c4d5e
Revises: 7d48833d0e21
Create Date: 2025-09-08 13:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9f1a2b3c4d5e"
down_revision = "7d48833d0e21"
branch_labels = None
depends_on = None


def upgrade():
    # Insert demo customers if they don't already exist
    op.execute(
        """
    INSERT INTO customers (name)
    SELECT 'ACME d.o.o.'
    WHERE NOT EXISTS (SELECT 1 FROM customers WHERE name='ACME d.o.o.');
    """
    )
    op.execute(
        """
    INSERT INTO customers (name)
    SELECT 'Beta d.o.o.'
    WHERE NOT EXISTS (SELECT 1 FROM customers WHERE name='Beta d.o.o.');
    """
    )

    op.execute(
        """SELECT setval(pg_get_serial_sequence('customers','id'), (SELECT COALESCE(MAX(id),0) FROM customers), true);"""
    )


def downgrade():
    op.execute("DELETE FROM customers WHERE id IN (1,2);")
