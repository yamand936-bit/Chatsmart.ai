import httpx
import os
import openai
import base64
import tempfile
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def download_whatsapp_media(media_id: str, access_token: str) -> bytes:
    """Downloads media from Meta Graph API using the Access Token."""
    url_req = f"https://graph.facebook.com/v20.0/{media_id}"
    async with httpx.AsyncClient() as http_client:
        r = await http_client.get(url_req, headers={"Authorization": f"Bearer {access_token}"})
        r.raise_for_status()
        url = r.json().get("url")
        if not url:
            raise ValueError(f"No url found for media_id {media_id}")
        
        # Download Binary
        r_media = await http_client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        r_media.raise_for_status()
        return r_media.content

async def download_instagram_media(url: str) -> bytes:
    """Downloads media from Instagram attachment URL."""
    async with httpx.AsyncClient() as http_client:
        r = await http_client.get(url)
        r.raise_for_status()
        return r.content

async def download_telegram_media(file_id: str, bot_token: str) -> bytes:
    """Downloads media from Telegram Bot API using the Bot Token."""
    async with httpx.AsyncClient() as http_client:
        # Get relative file path
        url_req = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
        r = await http_client.get(url_req)
        r.raise_for_status()
        res_json = r.json()
        if not res_json.get("ok"):
            raise ValueError(f"Failed to get file info from Telegram: {res_json}")
            
        file_path = res_json["result"]["file_path"]
        
        # Download Binary
        dl_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        r_media = await http_client.get(dl_url)
        r_media.raise_for_status()
        return r_media.content

async def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribes audio bytes to text using OpenAI Whisper API."""
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ogg")
        tmp.write(audio_bytes)
        tmp.close()

        with open(tmp.name, "rb") as f:
            transcript = await client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        return transcript.text
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return ""
    finally:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

def encode_image_base64(image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    """Encodes image bytes as base64 data URI for GPT Vision."""
    encoded = base64.b64encode(image_bytes).decode('utf-8')
    return f"data:{mime_type};base64,{encoded}"
