with open("backend/app/api/routers/merchant.py", "r", encoding="utf-8") as f:
    text = f.read()

kanban_endpoint = """
@router.get("/kanban")
async def get_kanban(business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Conversation)
        .where(Conversation.business_id == business_id)
        .order_by(Conversation.updated_at.desc())
        .limit(100)
    )
    convos = res.scalars().all()
    
    board = {
        "Cold": [],
        "Warm": [],
        "Hot": [],
        "Ordered": []
    }
    
    for c in convos:
        prio = c.lead_priority or "Cold"
        if prio not in board:
             prio = "Cold"
        
        board[prio].append({
            "id": str(c.id),
            "customer_phone": c.customer_phone,
            "last_message": c.last_message,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        })
        
    return {"status": "ok", "data": board}

class UpdatePriorityRequest(BaseModel):
    new_priority: str

@router.put("/kanban/{conversation_id}")
async def update_kanban_priority(
    conversation_id: uuid.UUID,
    payload: UpdatePriorityRequest,
    business_id: uuid.UUID = Depends(get_merchant_tenant),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.business_id == business_id
    ))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404)
        
    if payload.new_priority not in ["Cold", "Warm", "Hot", "Ordered"]:
        raise HTTPException(status_code=400, detail="Invalid priority")
        
    c.lead_priority = payload.new_priority
    await db.commit()
    return {"status": "ok"}
"""

if "def get_kanban" not in text:
    text += kanban_endpoint

with open("backend/app/api/routers/merchant.py", "w", encoding="utf-8") as f:
    f.write(text)
