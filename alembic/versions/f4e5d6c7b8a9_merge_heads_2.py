"""merge remaining heads

Revision ID: f4e5d6c7b8a9
Revises: ('37f247f285ce', 'c2d3e4f5g6h7')
Create Date: 2025-09-08 17:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f4e5d6c7b8a9"
down_revision = ("37f247f285ce", "c2d3e4f5g6h7")
branch_labels = None
depends_on = None


def upgrade():
    # merge-only revision: no DB operations
    pass


def downgrade():
    pass
