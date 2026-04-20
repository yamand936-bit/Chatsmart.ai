"""enforce_message_credits_check_constraint

Revision ID: 2688ae71947e
Revises: c7bf8a0ae3a8
Create Date: 2026-04-20 14:33:29.201000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2688ae71947e'
down_revision: Union[str, None] = '1fd4d3264425'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint('ck_businesses_message_credits_positive', 'businesses', 'message_credits >= 0')


def downgrade() -> None:
    op.drop_constraint('ck_businesses_message_credits_positive', 'businesses', type_='check')
