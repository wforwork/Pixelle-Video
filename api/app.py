# Copyright (C) 2025 AIDC-AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Pixelle-Video FastAPI Application

Main FastAPI app with all routers and middleware.

Run this script to start the FastAPI server:
    uv run python api/app.py
    
Or with custom settings:
    uv run python api/app.py --host 0.0.0.0 --port 8080 --reload
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path for module imports
_script_dir = Path(__file__).resolve().parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import argparse
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from loguru import logger

from api.config import api_config
from api.tasks import task_manager
from api.dependencies import shutdown_pixelle_video
from api.rate_limit import limiter, get_client_ip


# Import routers
from api.routers import (
    health_router,
    llm_router,
    tts_router,
    image_router,
    content_router,
    video_router,
    tasks_router,
    files_router,
    resources_router,
    frame_router,
)


# ============================================================
# Lifespan Context Manager
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    logger.info("🚀 Starting Pixelle-Video API...")
    await task_manager.start()
    logger.info("✅ Pixelle-Video API started successfully\n")
    yield
    logger.info("🛑 Shutting down Pixelle-Video API...")
    await task_manager.stop()
    await shutdown_pixelle_video()
    logger.info("✅ Pixelle-Video API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Pixelle-Video API",
    description="""
    ## Pixelle-Video - AI Video Generation Platform API
    
    ### Features
    - 🤖 **LLM**: Large language model integration
    - 🔊 **TTS**: Text-to-speech synthesis
    - 🎨 **Image**: AI image generation
    - 📝 **Content**: Automated content generation
    - 🎬 **Video**: End-to-end video generation
    
    ### Security
    - 🔑 All `/api/*` endpoints require `X-API-Key` header
    - ⏱️ Rate limiting: 60/min general, 10/min video, 30/min image
    
    ### Getting Started
    1. Check health: `GET /health`
    2. Generate narrations: `POST /api/content/narration`
    3. Generate video: `POST /api/video/generate/sync` or `/async`
    4. Track task progress: `GET /api/tasks/{task_id}`
    """,
    version="0.1.0",
    docs_url=api_config.docs_url,
    redoc_url=api_config.redoc_url,
    openapi_url=api_config.openapi_url,
    lifespan=lifespan,
)


# ============================================================
# Request Logging Middleware
# ============================================================
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs all incoming requests: method, path, status, duration, client IP."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        client_ip = get_client_ip(request)
        
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            f"{request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Duration: {duration_ms:.1f}ms | "
            f"IP: {client_ip}"
        )
        return response


# ============================================================
# CORS Middleware
# ============================================================
if api_config.cors_enabled:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=api_config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info(f"CORS enabled for origins: {api_config.cors_origins}")


# ============================================================
# API Key Middleware
# ============================================================
class APIKeyMiddleware(BaseHTTPMiddleware):
    """Protects all /api/* endpoints with API key validation."""
    
    async def dispatch(self, request: Request, call_next):
        if not api_config.api_key_enabled:
            return await call_next(request)
        
        public_paths = {
            "/", "/health", "/docs", "/redoc", "/openapi.json", "/api/files/",
        }
        
        path = request.url.path
        if path in public_paths or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)
        
        if path.startswith("/api/") and not path.startswith("/api/files/"):
            api_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
            if api_key != api_config.api_key:
                logger.warning(f"Unauthorized attempt from {request.client.host} to {path}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or missing API key."}
                )
        
        return await call_next(request)


# Add middlewares
app.add_middleware(RequestLoggingMiddleware)

if api_config.api_key_enabled:
    app.add_middleware(APIKeyMiddleware)
    logger.info(f"API Key auth ENABLED (key starts with: {api_config.api_key[:8]}...)")
else:
    logger.warning("API Key auth DISABLED - not recommended for production!")


# ============================================================
# Rate Limit Exceeded Handler
# ============================================================
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Rate limit exceeded from {get_client_ip(request)} to {request.url.path}")
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )


# ============================================================
# Include Routers
# ============================================================
app.state.limiter = limiter

app.include_router(health_router)

app.include_router(llm_router, prefix=api_config.api_prefix)
app.include_router(tts_router, prefix=api_config.api_prefix)
app.include_router(image_router, prefix=api_config.api_prefix)
app.include_router(content_router, prefix=api_config.api_prefix)
app.include_router(video_router, prefix=api_config.api_prefix)
app.include_router(tasks_router, prefix=api_config.api_prefix)
app.include_router(files_router, prefix=api_config.api_prefix)
app.include_router(resources_router, prefix=api_config.api_prefix)
app.include_router(frame_router, prefix=api_config.api_prefix)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Pixelle-Video API",
        "version": "0.1.0",
        "docs": api_config.docs_url,
        "health": "/health",
        "api": {
            "llm": f"{api_config.api_prefix}/llm",
            "tts": f"{api_config.api_prefix}/tts",
            "image": f"{api_config.api_prefix}/image",
            "content": f"{api_config.api_prefix}/content",
            "video": f"{api_config.api_prefix}/video",
            "tasks": f"{api_config.api_prefix}/tasks",
            "files": f"{api_config.api_prefix}/files",
            "resources": f"{api_config.api_prefix}/resources",
            "frame": f"{api_config.api_prefix}/frame",
        },
        "security": {
            "api_key_enabled": api_config.api_key_enabled,
            "rate_limit_enabled": api_config.rate_limit_enabled,
            "cors_enabled": api_config.cors_enabled,
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    parser = argparse.ArgumentParser(description="Start Pixelle-Video API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    api_key_display = api_config.api_key[:8] + "..." if api_config.api_key_enabled else "DISABLED"
    rate_limit_display = (
        f"ON ({api_config.rate_limit_per_minute}/min general, "
        f"{api_config.rate_limit_video_per_minute}/min video, "
        f"{api_config.rate_limit_image_per_minute}/min image)"
        if api_config.rate_limit_enabled else "OFF"
    )
    cors_display = str(api_config.cors_origins[:2]) + ("..." if len(api_config.cors_origins) > 2 else "")
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║               Pixelle-Video API Server                         ║
╚══════════════════════════════════════════════════════════════╝

Starting server at http://{args.host}:{args.port}
API Docs: http://{args.host}:{args.port}/docs
ReDoc:    http://{args.host}:{args.port}/redoc

🔑 API Key:  {api_key_display}
⏱️  Rate Limit: {rate_limit_display}
🌐 CORS:     {cors_display}

Press Ctrl+C to stop the server
""")
    
    uvicorn.run(
        "api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
