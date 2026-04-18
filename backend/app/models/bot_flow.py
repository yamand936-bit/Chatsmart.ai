from sqlalchemy import String, Boolean, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import BaseModel
import uuid

class BotFlow(BaseModel):
    __tablename__ = 'bot_flows'

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('businesses.id', ondelete='CASCADE'), index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Legacy rules for backwards compatibility
    rules: Mapped[list] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Phase 3: Visual Builder States
    flow_ui_state: Mapped[dict] = mapped_column(JSONB, nullable=True)
    flow_logic_state: Mapped[dict] = mapped_column(JSONB, nullable=True)
