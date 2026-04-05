from sqlalchemy import Column, String, Text
from app.db.base import Base

class SystemSettings(Base):
    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
