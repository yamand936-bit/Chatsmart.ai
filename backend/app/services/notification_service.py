import logging
import asyncio
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    async def dispatch_merchant_alert(business, event_type: str, message: str, custom_bot_token: str = None):
        """
        Dispatches an alert to the merchant via Telegram and/or Email if configured.
        """
        promises = []

        if business.notification_telegram:
            promises.append(
                NotificationService.send_telegram(business.notification_telegram, f"🚨 [{event_type}] {business.name}\n\n{message}", bot_token=custom_bot_token)
            )
            
        if business.notification_email:
            promises.append(
                NotificationService.send_email(
                    to_email=business.notification_email, 
                    subject=f"ChatSmart {event_type} - {business.name}", 
                    body=message
                )
            )
            
        if promises:
            # AWAIT the gather to actually execute the promises in the event loop!
            await asyncio.gather(*promises, return_exceptions=True)

    @staticmethod
    async def dispatch_admin_error(error_context: str, error_message: str):
        """
        Dispatches a critical error alert to the Super Admin via Telegram.
        """
        if not settings.ADMIN_TELEGRAM_CHAT_ID:
            logger.warning("ADMIN_TELEGRAM_CHAT_ID not set. Skipping Admin error notification.")
            return

        # Format Telegram HTML nicely (with max limit safety)
        safe_msg = error_message[:3500] if len(error_message) > 3500 else error_message
        text = f"⚙️ <b>CRITICAL SYSTEM ERROR</b> ⚙️\n\n<b>Context:</b> {error_context}\n<pre><code class=\"language-python\">{safe_msg}</code></pre>"
        
        asyncio.create_task(NotificationService.send_telegram(settings.ADMIN_TELEGRAM_CHAT_ID, text, parse_mode="HTML"))
            
    @staticmethod
    async def send_telegram(chat_id: str, text: str, parse_mode: str = None, bot_token: str = None):
        token = bot_token or settings.TELEGRAM_BOT_TOKEN
        if not token:
            logger.warning("Telegram Bot Token is not set globally or locally. Skipping Telegram alert.")
            return

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
            
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, json=payload, timeout=10.0)
                res.raise_for_status()
                logger.info(f"Telegram notification sent to chat_id: {chat_id}")
            except Exception as e:
                logger.error(f"Failed to send Telegram notification to {chat_id}: {e}")

    @staticmethod
    async def send_email(to_email: str, subject: str, body: str):
        if not settings.SMTP_HOST or not settings.SMTP_PORT:
            logger.warning("SMTP configuration is incomplete. Skipping Email alert.")
            return
            
        def _send():
            try:
                msg = MIMEMultipart()
                msg['From'] = settings.SMTP_USER or "noreply@chatsmartai.com"
                msg['To'] = to_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    # Upgrade to secure connection if standard port 587
                    server.starttls()
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
                logger.info(f"Email notification sent to {to_email}")
            except Exception as e:
                logger.error(f"Failed to send Email notification to {to_email}: {e}")
                
        # Run synchronous SMTP sending in a background thread to prevent blocking
        await asyncio.to_thread(_send)
