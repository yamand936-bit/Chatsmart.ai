from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal

class ChatMessageRequest(BaseModel):
    customer_platform: str  # e.g., 'whatsapp'
    external_id: str        # e.g., '+9055xxxx'
    content: str = Field(..., min_length=1, max_length=2000)
    
class ChatMessageResponse(BaseModel):
    status: str
    message_id: str
    conversation_id: str
    ai_response: str
    intent: str

# AI Contract Strict Schema
class AIIntentSchema(BaseModel):
    intent: Literal["create_order", "none", "handoff_human", "technical_support"] = Field(..., description="Action intent.")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    response: str = Field(..., description="Response message for the user")
    data: Optional[Dict[str, Any]] = Field({}, description="Extracted data. MUST contain product_id if intent is create_order")
