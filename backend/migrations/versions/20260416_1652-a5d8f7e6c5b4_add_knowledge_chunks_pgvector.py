"""add_knowledge_chunks_pgvector

Revision ID: a5d8f7e6c5b4
Revises: 814e3650cd12
Create Date: 2026-04-16 16:52:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector

# revision identifiers, used by Alembic.
revision: str = 'a5d8f7e6c5b4'
down_revision: Union[str, None] = '814e3650cd12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # First ensure the pgvector extension exists
    op.execute('CREATE EXTENSION IF NOT EXISTS vector;')

    op.create_table('knowledge_chunks',
    sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('source', sa.String(length=500), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.Vector(1536), nullable=False),
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_chunks_business_id'), 'knowledge_chunks', ['business_id'], unique=False)
    op.create_index(op.f('ix_knowledge_chunks_id'), 'knowledge_chunks', ['id'], unique=False)
    
    # Add HNSW index for fast similarity search
    op.execute('CREATE INDEX ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)')

def downgrade() -> None:
    op.drop_index(op.f('ix_knowledge_chunks_id'), table_name='knowledge_chunks')
    op.drop_index(op.f('ix_knowledge_chunks_business_id'), table_name='knowledge_chunks')
    op.drop_table('knowledge_chunks')
    # Intentionally not dropping 'vector' extension as it might be used by others
