import time
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import chat, portfolio, projects
from app.core.config import get_settings
from app.core.logger import ServerLogger
from app.core.security import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Initialize logging system
ServerLogger.setup()
settings = get_settings()

app = FastAPI(
    title="WALTER_AI_API",
    description="AI Backend for Walter Ambriz's Portfolio",
    version=settings.APP_VERSION
)

# Configure Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log requests, measure time and inject Trace ID."""
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    # Standard log with trace_id in extra
    logging.info(
        f"{request.method} {request.url.path} | Status: {response.status_code} | Time: {process_time:.2f}ms",
        extra={"trace_id": trace_id}
    )
    
    response.headers["X-Trace-ID"] = trace_id
    return response

# Optimized CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://amnotwallas.github.io", 
        "http://localhost:4200"
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# Routes registration
app.include_router(chat.router, prefix="/api/v1", tags=["AI"])
app.include_router(portfolio.router, prefix="/api/v1", tags=["Data"])
app.include_router(projects.router, prefix="/api/v1/assets", tags=["Assets"])

@app.get("/")
async def root():
    """Root endpoint to check system status."""
    return {
        "message": "WALTER_AI_NEURAL_CORE_ONLINE",
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
