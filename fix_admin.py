import re

with open(r'backend/app/api/routers/admin.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace batch_update_plan
plan_pattern = re.compile(
    r'@router\.post\("/businesses/batch/plan"\).*?def batch_update_plan.*?:\n(?:.*?)\n    await db\.commit\(\)\n    return \{"status": "ok"\}',
    re.DOTALL
)

plan_replacement = '''@router.post("/businesses/batch/plan")
async def batch_update_plan(data: BatchPlanRequest, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    from sqlalchemy import update
    u_ids = [uuid.UUID(bid) for bid in data.business_ids]
    if u_ids:
        await db.execute(update(Business).where(Business.id.in_(u_ids)).values(plan_name=data.new_plan))
        await db.commit()
    return {"status": "ok"}'''

code = plan_pattern.sub(plan_replacement, code)

# Replace batch_update_tokens
tokens_pattern = re.compile(
    r'@router\.post\("/businesses/batch/tokens"\).*?def batch_update_tokens.*?:\n(?:.*?)\n    await db\.commit\(\)\n    return \{"status": "ok"\}',
    re.DOTALL
)

tokens_replacement = '''@router.post("/businesses/batch/tokens")
async def batch_update_tokens(data: BatchTokensRequest, db: AsyncSession = Depends(get_db), admin: dict = Depends(get_current_admin)):
    from sqlalchemy import update
    u_ids = [uuid.UUID(bid) for bid in data.business_ids]
    if u_ids:
        await db.execute(update(Business).where(Business.id.in_(u_ids)).values(token_limit=data.token_limit))
        await db.commit()
    return {"status": "ok"}'''

code = tokens_pattern.sub(tokens_replacement, code)

with open(r'backend/app/api/routers/admin.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Regex replacement completed!")
