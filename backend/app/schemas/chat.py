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
    intent: Literal["create_order", "book_appointment", "suggest_product", "none", "handoff_human", "technical_support"] = Field(..., description="Action intent.")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    response: str = Field("", description="Response message for the user")
    public_reply: Optional[str] = Field(None, description="Public reply for TikTok")
    private_dm: Optional[str] = Field(None, description="Private DM for TikTok")
    lead_priority: Literal["Hot", "Warm", "Cold", "None"] = Field("None", description="Priority of the lead.")
    booking_in_progress: bool = Field(False, description="Set this to true to track when you are actively answering questions about a booking or collecting info for a booking.")
    funnel_stage: Literal["objection_handling", "negotiation", "closing", "gathering_info", "none"] = Field("none", description="The current sales funnel stage.")
    data: Optional[Dict[str, Any]] = Field({}, description="Extracted data. MUST contain product_id if intent is create_order or book_appointment. For book_appointment, must contain appointment_time and staff_name (if applicable). For hotel bookings, include check_in and check_out.")
