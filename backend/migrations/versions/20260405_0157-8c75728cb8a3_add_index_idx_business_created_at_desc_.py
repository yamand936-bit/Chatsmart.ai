"""Add index idx_business_created_at_desc on businesses

Revision ID: 8c75728cb8a3
Revises: 0fdeb581e327
Create Date: 2026-04-05 01:57:37.978649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c75728cb8a3'
down_revision: Union[str, None] = '0fdeb581e327'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX idx_business_created_at_desc ON businesses (created_at DESC)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_business_created_at_desc")
