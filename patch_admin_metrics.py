with open("backend/app/api/routers/admin.py", "r", encoding="utf-8") as f:
    text = f.read()

# Replace get_metrics to include MRR logic
old_metrics_code = """@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    \"\"\"Admin-only global metrics endpoint.\"\"\"
    total_businesses = (await db.execute(select(func.count(Business.id)))).scalar() or 0
    active_businesses = (await db.execute(select(func.count(Business.id)).where(Business.status == "active"))).scalar() or 0
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    total_tokens = (await db.execute(select(func.sum(UsageLog.tokens_used)))).scalar() or 0
    requests_today = (await db.execute(select(func.sum(UsageLog.request_count)).where(UsageLog.date_logged == date.today()))).scalar() or 0
    
    return {
        "status": "ok", 
        "total_businesses": total_businesses, 
        "active_businesses": active_businesses,
        "total_orders": total_orders,
        "total_tokens_used": total_tokens,
        "ai_requests_today": requests_today
    }"""

new_metrics_code = """@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    \"\"\"Admin-only global metrics endpoint.\"\"\"
    total_businesses = (await db.execute(select(func.count(Business.id)))).scalar() or 0
    active_businesses = (await db.execute(select(func.count(Business.id)).where(Business.status == "active"))).scalar() or 0
    total_orders = (await db.execute(select(func.count(Order.id)))).scalar() or 0
    total_tokens = (await db.execute(select(func.sum(UsageLog.tokens_used)))).scalar() or 0
    requests_today = (await db.execute(select(func.sum(UsageLog.request_count)).where(UsageLog.date_logged == date.today()))).scalar() or 0
    
    res = await db.execute(select(Business.plan_name, func.count(Business.id)).group_by(Business.plan_name))
    plan_counts = res.all()
    
    mrr = 0
    churn_rate = 2.5 # Mock churn rate
    plan_distribution = {}
    
    for plan, count in plan_counts:
        plan_str = str(plan).lower()
        if plan_str == "free":
            pass
        elif plan_str == "starter":
            mrr += count * 49
        elif plan_str == "pro":
            mrr += count * 99
        elif plan_str == "enterprise":
            mrr += count * 299
        
        plan_distribution[plan_str] = count

    return {
        "status": "ok", 
        "total_businesses": total_businesses, 
        "active_businesses": active_businesses,
        "total_orders": total_orders,
        "total_tokens_used": total_tokens,
        "ai_requests_today": requests_today,
        "mrr": mrr,
        "churn_rate": churn_rate,
        "plan_distribution": plan_distribution
    }"""

text = text.replace(old_metrics_code, new_metrics_code)

with open("backend/app/api/routers/admin.py", "w", encoding="utf-8") as f:
    f.write(text)
