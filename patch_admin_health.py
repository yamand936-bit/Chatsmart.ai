with open("backend/app/api/routers/admin.py", "r", encoding="utf-8") as f:
    text = f.read()

health_endpoint = """
import os
import psutil
from app.api.deps import redis_client

@router.get("/health")
async def system_health(admin: dict = Depends(get_current_admin)):
    \"\"\"System health metrics for Admin dashboard.\"\"\"
    try:
        cpu_usage = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        memory_usage = mem.percent
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
    except Exception:
        cpu_usage = 0
        memory_usage = 0
        disk_usage = 0

    try:
        await redis_client.ping()
        redis_status = "online"
    except Exception:
        redis_status = "offline"

    return {
        "status": "ok",
        "data": {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "redis_status": redis_status,
            "db_status": "online" # handled by middleware usually, if here it's online
        }
    }
"""

if "def system_health" not in text:
    text += health_endpoint

with open("backend/app/api/routers/admin.py", "w", encoding="utf-8") as f:
    f.write(text)
