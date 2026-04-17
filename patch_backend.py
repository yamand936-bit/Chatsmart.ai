import re

def patch_system():
    path = r'backend/app/api/routers/system.py'
    code = open(path, 'r', encoding='utf-8').read()
    if 'from app.api.deps import redis_client' not in code:
        code = code.replace('from app.api.deps import get_current_admin', 'from app.api.deps import get_current_admin, redis_client')
    
    if '@router.get("/announcement")' not in code:
        announcement_code = """
@router.get("/announcement")
async def get_announcement():
    try:
        msg = await redis_client.get("system:announcement")
        if isinstance(msg, bytes):
            msg = msg.decode("utf-8")
        return {"status": "ok", "message": msg if msg else ""}
    except Exception:
        return {"status": "ok", "message": ""}
"""
        code += announcement_code
        open(path, 'w', encoding='utf-8').write(code)

def patch_admin_metrics():
    path = r'backend/app/api/routers/admin.py'
    code = open(path, 'r', encoding='utf-8').read()
    
    # 1. Add POST /system/announcement
    if '@router.post("/system/announcement")' not in code:
        anc_post = """
class AnnouncementRequest(BaseModel):
    message: str

@router.post("/system/announcement")
async def broadcast_announcement(data: AnnouncementRequest, admin: dict = Depends(get_current_admin)):
    try:
        if data.message:
            await redis_client.set("system:announcement", data.message)
        else:
            await redis_client.delete("system:announcement")
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=500, detail="Redis connection failed")
"""
        code = code.replace('class MaintenanceRequest(BaseModel):', anc_post + '\nclass MaintenanceRequest(BaseModel):')

    # 2. Add webhook_health
    if 'webhook_delivery_rate' not in code:
        # find the return block in get_metrics
        inject_loc = '    return {\n        "status": "ok",'
        calc_code = """
    from app.models.domain import SystemErrorLog
    target_datetime = datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc).replace(tzinfo=None)
    webhook_fails = (await db.execute(select(func.count(SystemErrorLog.id)).where(SystemErrorLog.error_type == 'webhook_failed', SystemErrorLog.timestamp >= target_datetime))).scalar() or 0
    webhook_delivery_rate = 100.0 if webhook_fails == 0 else max(0.0, 100.0 - (float(webhook_fails) / (float(requests_today) + float(webhook_fails)) * 100))
    webhook_delivery_rate = round(webhook_delivery_rate, 2)
"""
        code = code.replace(inject_loc, calc_code + inject_loc)
        code = code.replace('"ai_requests_today": requests_today,', '"ai_requests_today": requests_today,\n        "webhook_delivery_rate": webhook_delivery_rate,')

    # 3. Add Last Active
    if 'func.max(UsageLog.date_logged)' not in code:
        code = code.replace(
            'func.max(User.email).label("owner_email"), func.sum(UsageLog.tokens_used).label("tokens_used")',
            'func.max(User.email).label("owner_email"), func.sum(UsageLog.tokens_used).label("tokens_used"), func.max(UsageLog.date_logged).label("last_active")'
        )
        
        # In the loop:
        code = code.replace(
            'for row in rows:\n        b = row[0]\n        email = row[1]\n        t_used = row[2] or 0',
            'for row in rows:\n        b = row[0]\n        email = row[1]\n        t_used = row[2] or 0\n        last_active = row[3]'
        )
        code = code.replace(
            '"owner_email": email,',
            '"owner_email": email,\n            "last_active": last_active.isoformat() if last_active else None,'
        )

    open(path, 'w', encoding='utf-8').write(code)

patch_system()
patch_admin_metrics()
print("Backend patched")
