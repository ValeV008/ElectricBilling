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
    INSERT INTO customers (id, name)
    SELECT 1, 'ACME d.o.o.'
    WHERE NOT EXISTS (SELECT 1 FROM customers WHERE id=1);
    """
    )
    op.execute(
        """
    INSERT INTO customers (id, name)
    SELECT 2, 'Beta d.o.o.'
    WHERE NOT EXISTS (SELECT 1 FROM customers WHERE id=2);
    """
    )


def downgrade():
    op.execute("DELETE FROM customers WHERE id IN (1,2);")
