"""add_template_message

Revision ID: 6b21bc5eb3b1
Revises: 74ac0aafb09e
Create Date: 2026-04-16 16:36:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '6b21bc5eb3b1'
down_revision: Union[str, None] = '74ac0aafb09e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('template_messages',
    sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('language', sa.String(length=50), nullable=False),
    sa.Column('body_text', sa.String(), nullable=False),
    sa.Column('variables_count', sa.Integer(), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('is_approved', sa.Boolean(), nullable=False),
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_template_messages_business_id'), 'template_messages', ['business_id'], unique=False)
    op.create_index(op.f('ix_template_messages_id'), 'template_messages', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_template_messages_id'), table_name='template_messages')
    op.drop_index(op.f('ix_template_messages_business_id'), table_name='template_messages')
    op.drop_table('template_messages')
