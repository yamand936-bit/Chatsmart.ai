from sqlalchemy import Column, String, Integer, Float, DateTime
from app.db.base import Base
import datetime

class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(String, primary_key=True)
    business_id = Column(String, index=True)

    provider = Column(String)
    model = Column(String)

    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)

    cost = Column(Float)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
