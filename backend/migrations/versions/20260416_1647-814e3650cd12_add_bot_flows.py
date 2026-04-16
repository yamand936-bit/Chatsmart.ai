"""add_bot_flows

Revision ID: 814e3650cd12
Revises: 6b21bc5eb3b1
Create Date: 2026-04-16 16:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '814e3650cd12'
down_revision: Union[str, None] = '6b21bc5eb3b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('bot_flows',
    sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('rules', sa.JSON(), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bot_flows_business_id'), 'bot_flows', ['business_id'], unique=False)
    op.create_index(op.f('ix_bot_flows_id'), 'bot_flows', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_bot_flows_id'), table_name='bot_flows')
    op.drop_index(op.f('ix_bot_flows_business_id'), table_name='bot_flows')
    op.drop_table('bot_flows')
