"""add_user_is_active_column

Revision ID: 1fd4d3264425
Revises: c7bf8a0ae3a8
Create Date: 2026-04-20 14:33:29.200992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1fd4d3264425'
down_revision: Union[str, None] = 'c7bf8a0ae3a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False))

def downgrade() -> None:
    op.drop_column('users', 'is_active')
