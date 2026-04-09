"""Add logs

Revision ID: 5f1b2c3d4e5f
Revises: 83d9b824e483
Create Date: 2026-04-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5f1b2c3d4e5f'
down_revision = '83d9b824e483'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('ai_usage_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('business_id', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_usage_logs_business_id'), 'ai_usage_logs', ['business_id'], unique=False)

    op.create_table('system_error_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=False),
        sa.Column('message', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_error_logs_business_id'), 'system_error_logs', ['business_id'], unique=False)
    op.create_index(op.f('ix_system_error_logs_error_type'), 'system_error_logs', ['error_type'], unique=False)
    op.create_index(op.f('ix_system_error_logs_timestamp'), 'system_error_logs', ['timestamp'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_system_error_logs_timestamp'), table_name='system_error_logs')
    op.drop_index(op.f('ix_system_error_logs_error_type'), table_name='system_error_logs')
    op.drop_index(op.f('ix_system_error_logs_business_id'), table_name='system_error_logs')
    op.drop_table('system_error_logs')
    
    op.drop_index(op.f('ix_ai_usage_logs_business_id'), table_name='ai_usage_logs')
    op.drop_table('ai_usage_logs')
