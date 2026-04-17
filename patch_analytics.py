with open("backend/app/api/routers/analytics.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("from fastapi import APIRouter, Depends", "from fastapi import APIRouter, Depends, Request")

old_func = """@router.get("/merchant/summary")
async def merchant_summary(business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    key = f'analytics:merchant:{business_id}'
    try:
        cached = await redis_client.get(key)
        if cached: 
            return json.loads(cached)
    except Exception:
        pass

    thirty_days_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)"""

new_func = """@router.get("/merchant/summary")
async def merchant_summary(request: Request, business_id: uuid.UUID = Depends(get_merchant_tenant), db: AsyncSession = Depends(get_db)):
    period = request.query_params.get('period', '30d')
    key = f'analytics:merchant:{business_id}:{period}'
    try:
        cached = await redis_client.get(key)
        if cached: 
            return json.loads(cached)
    except Exception:
        pass

    days = {'7d': 7, '30d': 30, '90d': 90}.get(period, 30)
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)"""

text = text.replace(old_func, new_func)

text = text.replace("thirty_days_ago", "cutoff")

with open("backend/app/api/routers/analytics.py", "w", encoding="utf-8") as f:
    f.write(text)
