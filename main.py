import os
import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.adapters.controllers.v1 import chat, portfolio, projects, insights
from app.core.config import get_settings
from app.core.logger import ServerLogger, trace_id_var
from app.core.security import limiter
from app.core.dependencies import get_audit
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.telemetry import init_telemetry
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

ServerLogger.setup()
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_telemetry("walter-ai")
    audit = get_audit()
    if audit is not None:
        await audit.init_db()
    yield

app = FastAPI(
    title="WALTER-AI_API",
    description="AI Backend for Walter Ambriz's Portfolio",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

FastAPIInstrumentor.instrument_app(app)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    trace_id = uuid.uuid4().hex
    start_time = time.time()
    
    # Set ContextVar trace ID
    token = trace_id_var.set(trace_id)
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logging.info(
            f"{request.method} {request.url.path} completed in {process_time:.2f}ms | Status: {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round(process_time, 2),
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        response.headers["X-Trace-ID"] = trace_id
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logging.error(
            f"{request.method} {request.url.path} failed in {process_time:.2f}ms | Error: {e}",
            exc_info=True,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "latency_ms": round(process_time, 2),
                "client_ip": request.client.host if request.client else "unknown"
            }
        )
        raise e
    finally:
        trace_id_var.reset(token)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

app.include_router(chat.router, prefix="/api/v1", tags=["AI"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["Data"])
app.include_router(projects.router, prefix="/api/v1/assets", tags=["Assets"])
app.include_router(insights.router, prefix="/api/v1", tags=["AIOps"])

@app.get("/")
async def root():
    """Root endpoint to check system status."""
    return {
        "message": "WALTER-AI",
        "documentation": "/docs",
        "status": "ready"
    }

@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {
        "status": "operational",
        "version": settings.APP_VERSION,
        "environment": "production"
    }

@app.get("/ui", response_class=HTMLResponse)
async def serve_ui():
    """Serves a premium chat frontend UI to test and interact with Walter AI."""
    template_path = os.path.join(os.path.dirname(__file__), "app/templates/chat_ui.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
