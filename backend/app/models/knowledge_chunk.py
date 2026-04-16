from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from app.db.base import BaseModel
import uuid

class KnowledgeChunk(BaseModel):
    __tablename__ = 'knowledge_chunks'

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('businesses.id', ondelete='CASCADE'), index=True)
    source: Mapped[str] = mapped_column(String(500))   # filename or URL
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(Vector(1536))  # OpenAI ada-002 dimensions
