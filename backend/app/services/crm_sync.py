import logging
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.domain import Customer
from copy import deepcopy

logger = logging.getLogger(__name__)

async def sync_crm_variables(db: AsyncSession, customer_id: str, crm_vars: dict):
    if not crm_vars:
        return
        
    try:
        res = await db.execute(select(Customer).where(Customer.id == uuid.UUID(customer_id)))
        customer = res.scalar_one_or_none()
        
        if not customer:
            return
            
        fields_updated = False
        custom_fields = deepcopy(customer.custom_fields) if customer.custom_fields else {}
        
        for k, v in crm_vars.items():
            if k in ["name", "guest_name", "first_name"]:
                if customer.name != v:
                    customer.name = v
                    fields_updated = True
            elif k in ["phone", "phone_number"]:
                if customer.phone != v:
                    customer.phone = v
                    fields_updated = True
            elif k in ["email", "email_address"]:
                if customer.email != v:
                    customer.email = v
                    fields_updated = True
            else:
                if custom_fields.get(k) != v:
                    custom_fields[k] = v
                    fields_updated = True
                
        if fields_updated:
            customer.custom_fields = custom_fields
            db.add(customer)
            await db.commit()
            logger.info(f"CRM variables synced natively for Customer {customer_id}")
            
    except Exception as e:
        logger.error(f"CRM sync failed for Customer {customer_id}: {e}", exc_info=True)
