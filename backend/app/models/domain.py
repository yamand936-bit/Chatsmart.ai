from typing import Optional, List
from sqlalchemy import String, Boolean, ForeignKey, Float, JSON, UniqueConstraint, Date, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import BaseModel
import uuid
from datetime import date, datetime, timezone

class Customer(BaseModel):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("platform", "external_id", "business_id", name="uq_platform_ext_biz"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(50))  # e.g., 'whatsapp', 'telegram'
    external_id: Mapped[str] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[List | None] = mapped_column(JSON, default=list, nullable=True)

    business: Mapped["Business"] = relationship("Business", back_populates="customers")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="customer", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    appointments: Mapped[List["Appointment"]] = relationship("Appointment", back_populates="customer", cascade="all, delete-orphan")


class Appointment(BaseModel):
    __tablename__ = "appointments"

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    
    title: Mapped[str] = mapped_column(String(255))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(50), default="confirmed")  # pending, confirmed, cancelled
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    staff_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="appointments")
    business: Mapped["Business"] = relationship("Business", back_populates="appointments")



class Product(BaseModel):
    __tablename__ = "products"

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    item_type: Mapped[str] = mapped_column(String(50), default="product") # product, service
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True) # Duration in minutes if service
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    business: Mapped["Business"] = relationship("Business", back_populates="products")


class Order(BaseModel):
    __tablename__ = "orders"

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, confirmed, completed, cancelled
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")


class Conversation(BaseModel):
    __tablename__ = "conversations"
    __table_args__ = (
        Index('ix_conv_biz_cust', 'business_id', 'customer_id'),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="bot")  # bot, human
    lead_priority: Mapped[str | None] = mapped_column(String(50), nullable=True) # Hot, Warm, Cold, None

    customer: Mapped["Customer"] = relationship("Customer", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(BaseModel):
    __tablename__ = "messages"
    __table_args__ = (
        Index('ix_messages_conv_created', 'conversation_id', 'created_at'),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    
    sender_type: Mapped[str] = mapped_column(String(50))  # user, bot, agent
    content: Mapped[str] = mapped_column(String)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_url: Mapped[str | None] = mapped_column(String, nullable=True)
    campaign_id: Mapped[str | None] = mapped_column(String, nullable=True)
    response_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


class TemplateMessage(BaseModel):
    __tablename__ = "template_messages"

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(50), default="en")
    body_text: Mapped[str] = mapped_column(String)
    variables_count: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(50), default="MARKETING")
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)

    business: Mapped["Business"] = relationship("Business")

class UsageLog(BaseModel):
    __tablename__ = "usage_logs"
    __table_args__ = (
        UniqueConstraint("business_id", "date_logged", name="uq_biz_date"),
    )

    business_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), index=True)
    date_logged: Mapped[date] = mapped_column(Date, default=date.today)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    request_count: Mapped[int] = mapped_column(Integer, default=0)

class SystemErrorLog(BaseModel):
    __tablename__ = "system_error_logs"

    business_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True)
    error_type: Mapped[str] = mapped_column(String(100), index=True) # e.g. "webhook_failed", "ai_error", "internal"
    message: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)

    business: Mapped["Business | None"] = relationship("Business")
