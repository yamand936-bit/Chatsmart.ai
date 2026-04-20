import re

with open("integrations_old.py", "r", encoding="utf-16le") as f:
    text = f.read()

# Extract the WhatsApp try block
wa_match = re.search(r'    try:\n        for entry in body\.get\("entry", \[\]\):(.*?)return \{"status": "success"\}\n    except Exception as e:\n        logger\.error\(f"WhatsApp core logic fail: \{e\}"\)\n        return \{"status": "error_handled"\}', text, re.DOTALL)
wa_body = wa_match.group(0) if wa_match else "    pass"

# Extract the Instagram try block
ig_match = re.search(r'    try:\n        for entry in body\.get\("entry", \[\]\):(.*?)return \{"status": "success"\}\n    except Exception as e:\n        logger\.error\(f"Instagram core logic fail: \{e\}"\)\n        return \{"status": "error_handled"\}', text, re.DOTALL)
ig_body = ig_match.group(0) if ig_match else "    pass"

# Extract the TikTok try block
tt_match = re.search(r'    try:\n        # Handling Direct Messages(.*?)return \{"status": "success"\}\n    except Exception as e:\n        logger\.error\(f"TikTok core logic fail: \{e\}"\)\n        return \{"status": "error_handled"\}', text, re.DOTALL)
tt_body = tt_match.group(0) if tt_match else "    pass"


# We need to drop "return {'status': ...}" from these blocks because they're inside an async worker now
wa_body = re.sub(r'return \{"status": "success"\}', 'pass', wa_body)
wa_body = re.sub(r'return \{"status": "error_handled"\}', 'pass', wa_body)

ig_body = re.sub(r'return \{"status": "success"\}', 'pass', ig_body)
ig_body = re.sub(r'return \{"status": "error_handled"\}', 'pass', ig_body)

tt_body = re.sub(r'return \{"status": "success"\}', 'pass', tt_body)
tt_body = re.sub(r'return \{"status": "error_handled"\}', 'pass', tt_body)


worker_code = f"""import json
import uuid
import logging
import asyncio
import httpx
from datetime import date
from sqlalchemy import select
from app.db.session import async_session_maker
from app.api.deps import redis_client
from app.services.chat_core import process_chat_core
from app.core.config import settings

logger = logging.getLogger(__name__)

async def transmit_meta_graph(phone_number_id, access_token, recipient_id, text=None, interactive_payload=None):
    from app.api.routers.integrations import transmit_meta_graph as orig_meta
    return await orig_meta(phone_number_id, access_token, recipient_id, text, interactive_payload)

async def transmit_tiktok_dm(access_token, recipient_id, text):
    from app.api.routers.integrations import transmit_tiktok_dm as orig_dm
    return await orig_dm(access_token, recipient_id, text)

async def transmit_tiktok_comment_reply(access_token, item_id, comment_id, text):
    from app.api.routers.integrations import transmit_tiktok_comment_reply as orig_cr
    return await orig_cr(access_token, item_id, comment_id, text)

async def _process_whatsapp(db, business_id, config, body):
{wa_body}

async def _process_instagram(db, business_id, config, body):
{ig_body}

async def _process_tiktok(db, business_id, config, body):
{tt_body}

async def webhook_consumer_loop():
    logger.info("Webhook consumer loop started and waiting for events...")
    while True:
        try:
            result = await redis_client.blpop("webhook_payloads", timeout=0)
            if not result:
                continue
            
            queue_name, payload_bytes = result
            payload_data = json.loads(payload_bytes)
            
            platform = payload_data.get("platform")
            business_id = uuid.UUID(payload_data.get("business_id"))
            config = payload_data.get("config", {{}})
            body = payload_data.get("body", {{}})
            
            # Spin up a dedicated DB session per background task
            async with async_session_maker() as db:
                if platform == "whatsapp":
                    await _process_whatsapp(db, business_id, config, body)
                elif platform == "instagram":
                    await _process_instagram(db, business_id, config, body)
                elif platform == "tiktok":
                    await _process_tiktok(db, business_id, config, body)
                    
        except asyncio.CancelledError:
            logger.info("Webhook consumer gracefully stopped.")
            break
        except Exception as e:
            logger.error(f"Webhook consumer processing error: {{e}}", exc_info=True)
            await asyncio.sleep(1) # Prevent hot loop crash
"""

import os
os.makedirs("backend/app/workers", exist_ok=True)
with open("backend/app/workers/webhook_worker.py", "w", encoding="utf-8") as f:
    f.write(worker_code)

print("worker generated")
