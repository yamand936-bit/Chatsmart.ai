from typing import List, Optional, Dict
from sqlalchemy import String, JSON, Boolean, ForeignKey, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import BaseModel
import uuid

class Business(BaseModel):
    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(String(255), index=True)
    business_type: Mapped[str] = mapped_column(String(100), default="retail")
    status: Mapped[str] = mapped_column(String(50), default="active")
    token_limit: Mapped[int] = mapped_column(Integer, default=100000)
    monthly_quota: Mapped[int] = mapped_column(Integer, default=100000)
    
    plan_name: Mapped[str] = mapped_column(String(50), default="free")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[str] = mapped_column(String(50), default="trial")
    ai_tone: Mapped[str] = mapped_column(String(50), default="Professional")
    bank_details: Mapped[Dict | None] = mapped_column(JSON, nullable=True)
    knowledge_base: Mapped[str | None] = mapped_column(String, nullable=True)
    sheet_url: Mapped[str | None] = mapped_column(String, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    primary_color: Mapped[str | None] = mapped_column(String(50), nullable=True, default="#2563eb")
    language: Mapped[str] = mapped_column(String(50), default="ar", server_default="ar")
    notification_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notification_telegram: Mapped[str | None] = mapped_column(String(255), nullable=True)
    staff_members: Mapped[List | None] = mapped_column(JSON, default=list, nullable=True)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    features: Mapped[List["BusinessFeature"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    products: Mapped[List["Product"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    customers: Mapped[List["Customer"]] = relationship(back_populates="business", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship(back_populates="business", cascade="all, delete-orphan")


class BusinessFeature(BaseModel):
    __tablename__ = "business_features"

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    feature_type: Mapped[str] = mapped_column(String(50), index=True)  # e.g., 'whatsapp', 'telegram'
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    business: Mapped["Business"] = relationship(back_populates="features")
