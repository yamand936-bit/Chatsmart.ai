import logging
import sys
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.db.session import engine

from app.api.routers import auth, admin, merchant, chat, integrations, system, analytics, campaigns

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ENV VALIDATION
    if not settings.JWT_SECRET or settings.JWT_SECRET == "supersecretkey":
        logger.error("CRITICAL: JWT_SECRET is not securely set. Crashing!")
        sys.exit(1)
        
    if not settings.OPENAI_API_KEY and not settings.GEMINI_API_KEY:
        logger.warning("WARNING: No AI API keys set. System will use fallback stubs.")

    # Verify DB connection on startup
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to the database.")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}. Crashing!")
        sys.exit(1)
        
    from app.workers.webhook_worker import webhook_consumer_loop
    import asyncio
    
    # Start the async queue consumer for webhooks in the background
    worker_task = asyncio.create_task(webhook_consumer_loop(), name="WebhookConsumer")

    yield
    # Cleanup on shutdown
    worker_task.cancel()
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Multi-Tenant AI SaaS Platform API",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        str(origin).rstrip('/')
        for origin in settings.BACKEND_CORS_ORIGINS
    ] if settings.BACKEND_CORS_ORIGINS else [],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    # Generates a globally unique Request ID strictly tracked per API call
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"[REQ:{request_id[:8]}] {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    
    # Security headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin System"])
app.include_router(merchant.router, prefix="/api/merchant", tags=["Merchant System"])
app.include_router(campaigns.router, prefix="/api/merchant/campaigns", tags=["Campaigns"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat Engine"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(system.router, prefix="/api/system", tags=["System Configuration"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

import traceback
from fastapi.responses import JSONResponse
from app.services.notification_service import NotificationService
from app.core.utils import safe_create_task

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb_str = traceback.format_exc()
    logger.error(f"Global unhandled exception at {request.url}: {exc}\n{tb_str}")
    
    # Fire off notification without waiting
    error_context = f"Unhandled Exception at {request.method} {request.url.path}"
    safe_create_task(NotificationService.dispatch_admin_error(error_context, f"Exception: {str(exc)}\n\nTraceback:\n{tb_str}"), "GlobalErrorDispatch")
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. The admin has been notified."}
    )
