with open("backend/app/api/routers/merchant.py", "a", encoding="utf-8") as f:
    f.write("""

@router.post("/conversations/{conversation_id}/takeover")
async def takeover_conversation(
    conversation_id: str,
    business_id: uuid.UUID = Depends(get_merchant_tenant),
    db: AsyncSession = Depends(get_db)
):
    from app.models.domain import Conversation
    c_res = await db.execute(select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.business_id == business_id
    ))
    conv = c_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)
    conv.status = "human"
    db.add(conv)
    await db.commit()
    return {"status": "ok", "message": "You are now handling this conversation. AI paused."}

@router.post("/conversations/{conversation_id}/handback")
async def handback_conversation(
    conversation_id: str,
    business_id: uuid.UUID = Depends(get_merchant_tenant),
    db: AsyncSession = Depends(get_db)
):
    from app.models.domain import Conversation
    c_res = await db.execute(select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.business_id == business_id
    ))
    conv = c_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)
    conv.status = "bot"
    db.add(conv)
    await db.commit()
    return {"status": "ok", "message": "AI resumed."}

class AgentReplyRequest(BaseModel):
    content: str

@router.post("/conversations/{conversation_id}/reply")
async def agent_reply(
    conversation_id: str,
    payload: AgentReplyRequest,
    business_id: uuid.UUID = Depends(get_merchant_tenant),
    db: AsyncSession = Depends(get_db)
):
    from app.models.domain import Conversation, Message, Customer
    from app.api.routers.integrations import transmit_meta_graph, transmit_telegram, get_feature_config

    c_res = await db.execute(select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.business_id == business_id
    ))
    conv = c_res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)

    cust_res = await db.execute(select(Customer).where(Customer.id == conv.customer_id))
    customer = cust_res.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Save the agent message to DB
    msg = Message(
        business_id=business_id,
        conversation_id=conv.id,
        sender_type="agent",
        content=payload.content
    )
    db.add(msg)
    await db.commit()

    # Transmit to the customer's platform
    try:
        if customer.platform == "whatsapp":
            w_config = await get_feature_config(db, business_id, "whatsapp")
            if w_config.get("access_token"):
                await transmit_meta_graph(
                    w_config.get("phone_number_id", ""),
                    w_config.get("access_token", ""),
                    customer.external_id,
                    text=payload.content
                )
        elif customer.platform == "telegram":
            t_config = await get_feature_config(db, business_id, "telegram")
            if t_config.get("bot_token"):
                await transmit_telegram(t_config.get("bot_token"), customer.external_id, payload.content)
    except Exception as e:
        logger.warning(f"Agent reply transmit failed: {e}")

    return {"status": "ok", "message_id": str(msg.id)}

class BotFlowRuleSchema(BaseModel):
    trigger: str
    match: str = "contains"   # exact | contains | starts_with
    response: str
    language: Optional[str] = None

class BotFlowCreate(BaseModel):
    name: str
    is_active: bool = True
    priority: int = 0
    rules: List[BotFlowRuleSchema] = []

@router.get("/flows")
async def list_flows(business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    from app.models.bot_flow import BotFlow
    res = await db.execute(select(BotFlow).where(BotFlow.business_id == business_id).order_by(BotFlow.priority.desc()))
    flows = res.scalars().all()
    return {"status": "ok", "data": [
        {"id": str(f.id), "name": f.name, "is_active": f.is_active,
         "priority": f.priority, "rules": f.rules, "created_at": str(f.created_at)}
        for f in flows
    ]}

@router.post("/flows")
async def create_flow(payload: BotFlowCreate, business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    from app.models.bot_flow import BotFlow
    flow = BotFlow(
        business_id=business_id,
        name=payload.name,
        is_active=payload.is_active,
        priority=payload.priority,
        rules=[r.dict() for r in payload.rules]
    )
    db.add(flow)
    await db.commit()
    return {"status": "ok", "data": {"id": str(flow.id)}}

@router.put("/flows/{flow_id}")
async def update_flow(flow_id: str, payload: BotFlowCreate, business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    from app.models.bot_flow import BotFlow
    res = await db.execute(select(BotFlow).where(BotFlow.id == uuid.UUID(flow_id), BotFlow.business_id == business_id))
    flow = res.scalar_one_or_none()
    if not flow:
        raise HTTPException(status_code=404)
    flow.name = payload.name
    flow.is_active = payload.is_active
    flow.priority = payload.priority
    flow.rules = [r.dict() for r in payload.rules]
    db.add(flow)
    await db.commit()
    return {"status": "ok"}

@router.delete("/flows/{flow_id}")
async def delete_flow(flow_id: str, business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    from app.models.bot_flow import BotFlow
    res = await db.execute(select(BotFlow).where(BotFlow.id == uuid.UUID(flow_id), BotFlow.business_id == business_id))
    flow = res.scalar_one_or_none()
    if not flow:
        raise HTTPException(status_code=404)
    await db.delete(flow)
    await db.commit()
    return {"status": "ok"}

from fastapi import UploadFile, File

@router.post("/knowledge")
async def upload_knowledge(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = None,
    business_id: uuid.UUID = Depends(get_merchant_tenant),
    db: AsyncSession = Depends(get_db)
):
    \"\"\"Upload a document or paste text to populate the vector knowledge base.\"\"\"
    from app.services.knowledge_service import ingest_text

    raw_text = ""
    source = "manual_text"

    if file:
        source = file.filename or "uploaded_file"
        content_bytes = await file.read()
        ext = (file.filename or "").lower().split(".")[-1]
        if ext == "pdf":
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content_bytes))
            raw_text = "\\n".join(p.extract_text() or "" for p in reader.pages)
        elif ext in ("txt", "md", "csv"):
            raw_text = content_bytes.decode("utf-8", errors="replace")
        else:
            raise HTTPException(status_code=400, detail="Supported file types: .pdf, .txt, .md, .csv")
    elif text:
        raw_text = text
    else:
        raise HTTPException(status_code=400, detail="Provide either a file or a text field.")

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="No text content found in the provided input.")

    await ingest_text(db, business_id, raw_text, source)
    word_count = len(raw_text.split())
    chunks = max(1, word_count // 350)
    return {"status": "ok", "source": source, "words_ingested": word_count, "chunks_created": chunks}

class TemplateCreate(BaseModel):
    name: str
    language: str = "ar"
    category: str = "MARKETING"
    body_text: str
    variables_count: int = 0

@router.get("/templates")
async def list_templates(business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    from app.models.domain import TemplateMessage
    res = await db.execute(select(TemplateMessage).where(TemplateMessage.business_id == business_id))
    templates = res.scalars().all()
    return {"status": "ok", "data": [
        {"id": str(t.id), "name": t.name, "language": t.language,
         "category": t.category, "body_text": t.body_text,
         "variables_count": t.variables_count, "is_approved": t.is_approved}
        for t in templates
    ]}

@router.post("/templates")
async def create_template(payload: TemplateCreate, business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    from app.models.domain import TemplateMessage
    tmpl = TemplateMessage(
        business_id=business_id,
        name=payload.name,
        language=payload.language,
        category=payload.category,
        body_text=payload.body_text,
        variables_count=payload.variables_count,
        is_approved=False   # requires admin approval
    )
    db.add(tmpl)
    await db.commit()
    return {"status": "ok", "data": {"id": str(tmpl.id)}}

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    from app.models.domain import TemplateMessage
    res = await db.execute(select(TemplateMessage).where(
        TemplateMessage.id == uuid.UUID(template_id),
        TemplateMessage.business_id == business_id
    ))
    tmpl = res.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404)
    await db.delete(tmpl)
    await db.commit()
    return {"status": "ok"}
""")
