from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.api.deps import get_merchant_tenant, redis_client
from app.db.session import get_db
from app.models.domain import Customer, Message, Conversation
from app.services.ai_router import AIRouter
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class CampaignRequest(BaseModel):
    tag: str
    instructions: str

@router.post("/send")
async def send_smart_campaign(
    request: CampaignRequest,
    background_tasks: BackgroundTasks,
    business_id: uuid.UUID = Depends(get_merchant_tenant),
    db: AsyncSession = Depends(get_db)
):
    """
    Kicks off a smart AI campaign targeting customers with a specific tag.
    """
    all_customers = await db.execute(select(Customer).where(Customer.business_id == business_id))
    matched_customers = []
    
    for c in all_customers.scalars().all():
        if c.tags and isinstance(c.tags, list):
            if any(request.tag.lower() in t.lower() for t in c.tags):
                matched_customers.append(c)
                
    if not matched_customers:
        raise HTTPException(status_code=404, detail=f"No customers found matching tag: {request.tag}")

    background_tasks.add_task(process_campaign_batch, str(business_id), [str(c.id) for c in matched_customers], request.instructions)
    
    return {"status": "success", "message": f"Campaign queued for {len(matched_customers)} customers."}

async def process_campaign_batch(business_id: str, customer_ids: list, instructions: str):
    from app.db.session import async_session_maker
    
    async with async_session_maker() as session:
        for cid in customer_ids:
            try:
                cust_res = await session.execute(select(Customer).where(Customer.id == uuid.UUID(cid)))
                customer = cust_res.scalar_one_or_none()
                if not customer: continue
                
                conv_res = await session.execute(
                    select(Conversation).where(
                        Conversation.customer_id == customer.id
                    ).order_by(Conversation.created_at.desc()).limit(1)
                )
                conv = conv_res.scalar_one_or_none()
                if not conv: continue
                
                msg_res = await session.execute(
                    select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at.asc())
                )
                messages = msg_res.scalars().all()
                history_text = "\n".join([f"{'User' if m.sender_type=='user' else 'AI'}: {m.content}" for m in messages[-10:]])
                
                prompt = f"""
                You are a smart marketing assistant.
                Write a highly personalized short message for this customer based on their past conversation.
                
                Marketing Instructions / Offer: "{instructions}"
                Customer Platform: {customer.platform}
                Language: Match the language of the conversation.
                
                Past Conversation Context:
                {history_text}
                
                Format: Respond ONLY with the finalized message text. Keep it friendly, persuasive, and relevant.
                """
                
                ai_req = [{"role": "user", "content": prompt}]
                result = await AIRouter.generate(session, ai_req)
                personalized_message = result["text"].strip()
                
                camp_msg = Message(
                    business_id=uuid.UUID(business_id),
                    conversation_id=conv.id,
                    sender_type="campaign",
                    content=personalized_message,
                    campaign_id="smart_campaign"
                )
                session.add(camp_msg)
                
                try:
                    if customer.platform == "whatsapp":
                        from app.api.routers.integrations import transmit_meta_graph, get_feature_config
                        w_config = await get_feature_config(session, uuid.UUID(business_id), "whatsapp")
                        if w_config.get("access_token"):
                            await transmit_meta_graph(
                                w_config.get("phone_number_id", ""),
                                w_config.get("access_token", ""),
                                customer.external_id,
                                personalized_message
                            )
                    elif customer.platform == "telegram":
                        from app.api.routers.integrations import transmit_telegram, get_feature_config
                        t_config = await get_feature_config(session, uuid.UUID(business_id), "telegram")
                        if t_config.get("bot_token"):
                            await transmit_telegram(t_config.get("bot_token"), customer.external_id, personalized_message)
                except Exception as ex:
                    logger.error(f"Failed to transmit campaign message to {customer.platform}: {ex}")
                    
            except Exception as e:
                logger.error(f"Campaign failed for customer {cid}: {e}")
            
        await session.commit()
