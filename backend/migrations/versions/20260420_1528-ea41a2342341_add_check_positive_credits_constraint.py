"""Add check positive credits constraint

Revision ID: ea41a2342341
Revises: 2688ae71947e
Create Date: 2026-04-20 15:28:33.572809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea41a2342341'
down_revision: Union[str, None] = '2688ae71947e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Manual Add for CheckConstraint
    op.execute("ALTER TABLE businesses ADD CONSTRAINT check_credits_positive CHECK (message_credits >= 0);")

def downgrade() -> None:
    op.execute("ALTER TABLE businesses DROP CONSTRAINT check_credits_positive;")
