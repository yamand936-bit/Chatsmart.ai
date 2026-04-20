from typing import Optional
from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import BaseModel
import uuid

class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="merchant")  # admin, merchant
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    business_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)

    business: Mapped["Business | None"] = relationship("Business", back_populates="users")
