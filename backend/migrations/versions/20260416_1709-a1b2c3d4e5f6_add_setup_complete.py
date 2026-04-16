"""add setup_complete

Revision ID: a1b2c3d4e5f6
Revises: a5d8f7e6c5b4
Create Date: 2026-04-16 17:09:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'a5d8f7e6c5b4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('businesses', sa.Column('setup_complete', sa.Boolean(), server_default='false', nullable=True))
    op.execute('UPDATE businesses SET setup_complete = false')
    op.alter_column('businesses', 'setup_complete', nullable=False)


def downgrade():
    op.drop_column('businesses', 'setup_complete')
