"""token limits

Revision ID: 83d9b824e483
Revises: b696a069079d
Create Date: 2026-04-04 16:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83d9b824e483'
down_revision = 'b696a069079d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # We don't actually need to run anything here, because the DB is already upgraded exactly.
    # But for a fresh DB, we need the actual commands!
    op.add_column('businesses', sa.Column('business_type', sa.String(length=50), nullable=True))
    op.add_column('businesses', sa.Column('owner_password', sa.String(length=255), nullable=True))
    op.add_column('businesses', sa.Column('owner_email', sa.String(length=255), nullable=True))
    op.add_column('businesses', sa.Column('status', sa.String(length=50), nullable=True))
    op.add_column('businesses', sa.Column('token_limit', sa.Integer(), nullable=True))
    op.add_column('businesses', sa.Column('monthly_quota', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('businesses', 'monthly_quota')
    op.drop_column('businesses', 'token_limit')
    op.drop_column('businesses', 'status')
    op.drop_column('businesses', 'owner_email')
    op.drop_column('businesses', 'owner_password')
    op.drop_column('businesses', 'business_type')
