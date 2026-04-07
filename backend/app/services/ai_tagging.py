import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.domain import Customer, Message
from app.services.ai_router import AIRouter

logger = logging.getLogger(__name__)

async def auto_tag_customer(db: AsyncSession, customer_id: str, conversation_id: str):
    """
    Evaluates the conversation and applies a basic+dynamic hybrid tag to the customer.
    Runs asynchronously, decoupled from the critical response path.
    """
    try:
        # 1. Fetch conversation messages
        msg_res = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        messages = msg_res.scalars().all()
        if not messages:
            return
            
        history_text = "\n".join([f"{'User' if m.sender_type=='user' else 'AI'}: {m.content}" for m in messages])
        
        system_prompt = """
        You are an auto-tagging CRM AI.
        Analyze the following conversation and return a JSON object with a single 'tag'.
        The tag MUST combine one of these base intents:
        [interested, purchased, inquisitive, angry]
        followed by a short, descriptive dynamic sub-tag.
        Format: "base_intent - dynamic detail".
        Examples: 
        "interested - Rolex watches"
        "purchased - 2 T-shirts"
        "inquisitive - delivery time"
        "angry - delayed order"
        
        Respond ONLY with valid JSON: {"tag": "..."}
        """
        
        prompt_msgs = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Conversation:\n{history_text}"}
        ]
        
        result = await AIRouter.generate(db, prompt_msgs, force_model="openai")
        text_resp = result["text"].replace("```json", "").replace("```", "").strip()
        resp_json = json.loads(text_resp)
        new_tag = resp_json.get("tag")
        
        if new_tag:
            # Update customer
            cust_res = await db.execute(select(Customer).where(Customer.id == customer_id))
            customer = cust_res.scalar_one_or_none()
            if customer:
                current_tags = list(customer.tags) if customer.tags else []
                if new_tag not in current_tags:
                    current_tags.append(new_tag)
                    customer.tags = current_tags
                    db.add(customer)
                    await db.commit()
    except Exception as e:
        logger.error(f"Auto-tagging failed for customer {customer_id}: {e}")
