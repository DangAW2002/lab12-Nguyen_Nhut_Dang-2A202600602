"""
Production AI Agent — Final Project Complete
"""
import os
import time
import signal
import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Security, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import redis

from app.config import settings
from app.auth import verify_api_key
from app.rate_limiter import RedisRateLimiter
from app.cost_guard import RedisCostGuard
from utils.mock_llm import ask as llm_ask

from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional, Generator

from app.agent import (
    run_safety_guardrails,
    execute_mock_agent,
    OpenAIProvider,
    OpenAICompatibleProvider,
    GeminiProvider,
    VaccineAssistantAgent
)

# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

# Initialize Redis connection
r_conn = None
if settings.redis_url:
    try:
        r_conn = redis.from_url(settings.redis_url, decode_responses=True)
        r_conn.ping()
        logger.info("Connected to Redis for stateless operations")
    except Exception as e:
        logger.error(f"Failed to connect to Redis at {settings.redis_url}: {e}")
        r_conn = None

# Initialize security layers with Redis connection
rate_limiter = RedisRateLimiter(r_conn)
cost_guard = RedisCostGuard(r_conn)

# Fallback in-memory history storage
_memory_history: dict[str, list] = {}

def get_history(user_id: str) -> list:
    if r_conn:
        data = r_conn.get(f"history:{user_id}")
        return json.loads(data) if data else []
    return _memory_history.get(user_id, [])

def save_history(user_id: str, history: list):
    if r_conn:
        r_conn.setex(f"history:{user_id}", 3600, json.dumps(history))
    else:
        _memory_history[user_id] = history

def generate_answer_with_history(question: str, history: list) -> str:
    # Check if the user is asking for their name/identity based on conversation history
    q_lower = question.lower()
    if any(keyword in q_lower for keyword in ["my name", "who am i", "tên tôi là gì", "tên là gì"]):
        for msg in reversed(history):
            if msg["role"] == "user":
                content_lower = msg["content"].lower()
                # Find patterns like "my name is <name>"
                if "my name is " in content_lower:
                    idx = content_lower.find("my name is ") + 11
                    name = msg["content"][idx:].strip(" .!?")
                    return f"Your name is {name}."
                # Find patterns like "i am <name>"
                elif "i am " in content_lower:
                    idx = content_lower.find("i am ") + 5
                    name = msg["content"][idx:].strip(" .!?")
                    return f"Your name is {name}."

    # Check if we have an API key configured for the real agent
    api_key = (
        os.getenv("OPENAI_API_KEY") 
        or os.getenv("COMPATIBLE_API_KEY") 
        or os.getenv("OPENROUTER_API_KEY") 
        or os.getenv("GEMINI_API_KEY")
    )
    if api_key:
        try:
            logger.info("Executing real AI Agent for /ask endpoint...")
            if os.getenv("OPENAI_API_KEY"):
                provider = OpenAIProvider(
                    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                    api_key=os.getenv("OPENAI_API_KEY")
                )
            elif os.getenv("COMPATIBLE_API_KEY"):
                provider = OpenAICompatibleProvider(
                    model_name=os.getenv("COMPATIBLE_MODEL_NAME", "mimo-v2.5-pro"),
                    base_url=os.getenv("COMPATIBLE_BASE_URL", "http://localhost:8000/v1"),
                    api_key=os.getenv("COMPATIBLE_API_KEY")
                )
            elif os.getenv("OPENROUTER_API_KEY"):
                provider = OpenAICompatibleProvider(
                    model_name=os.getenv("OPENROUTER_MODEL_NAME", "google/gemini-2.5-flash"),
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.getenv("OPENROUTER_API_KEY")
                )
            else:
                provider = GeminiProvider(
                    model_name="gemini-2.5-flash",
                    api_key=api_key
                )
            agent = VaccineAssistantAgent(llm=provider)
            
            # Convert history to format expected by agent (list of {"from": "bot"|"user", "text": "..."})
            agent_history = []
            for h in history:
                role = "user" if h["role"] == "user" else "bot"
                agent_history.append({"from": role, "text": h["content"]})
            agent_history.append({"from": "user", "text": question})
            
            res = agent.run(agent_history)
            return res.get("text", "Dạ, trợ lý chưa tìm được câu trả lời.")
        except Exception as e:
            logger.error(f"Error calling real agent in /ask: {e}", exc_info=True)

    return llm_ask(question)

# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    _is_ready = True
    logger.info(json.dumps({"event": "ready"}))
    yield
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

# ─────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if "server" in response.headers:
            del response.headers["server"]
        
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception as e:
        _error_count += 1
        logger.error(json.dumps({"event": "exception", "error": str(e)}))
        raise

# ─────────────────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────────────────
class AskRequest(BaseModel):
    user_id: str | None = Field(default="default_user", description="Unique identifier for the user session")
    question: str = Field(..., min_length=1, max_length=2000, description="Your question for the agent")

class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    timestamp: str

class ChatMessage(BaseModel):
    from_role: str = "user" # Matches client 'from' field ('user' or 'bot')
    text: str

    class Config:
        # Allow mapping from 'from' to 'from_role'
        fields = {'from_role': 'from'}
        populate_by_name = True

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]] # Expecting list of {"from": "bot"|"user", "text": "..."}

class CallbackRequest(BaseModel):
    name: str
    phone: str
    details: Optional[str] = ""

# ─────────────────────────────────────────────────────────
# Helpers for Chat
# ─────────────────────────────────────────────────────────
def stream_mock_agent(history: List[Dict[str, Any]]) -> Generator[Dict[str, Any], None, None]:
    result = execute_mock_agent(history)
    text = result.get("text", "")
    yield {"type": "text", "content": text}
    if result.get("tool_data"):
        yield {"type": "tool_data", "content": result["tool_data"]}

def chat_stream_generator(messages: List[Dict[str, Any]], api_key: Optional[str]):
    user_messages = [m for m in messages if m.get("from") == "user"]
    if not messages or not user_messages:
        payload = {
            "type": "text",
            "content": "Chào mừng Anh/Chị đến với Tiêm chủng Long Châu. Long Châu có thể giúp gì cho mình ạ?"
        }
        yield json.dumps(payload, ensure_ascii=False) + "\n"
        return

    last_user_message = user_messages[-1].get("text", "")
    logger.info(f"Received message from user: {last_user_message}")

    # 1. Run Safety Guardrails Check on user message
    safety_result = run_safety_guardrails(last_user_message, api_key)
    
    if safety_result.get("is_dangerous"):
        logger.warning(f"Safety red flags triggered for query: {last_user_message}")
        payload = {
            "type": "safety_triggered",
            "content": True,
            "text": safety_result["warning_message"],
            "tool_data": {
                "safety_escalation": True,
                "type": safety_result["type"]
            }
        }
        yield json.dumps(payload, ensure_ascii=False) + "\n"
        return

    # 2. Run agent execution
    if api_key:
        logger.info("Executing AI Agent Stream Loop...")
        if os.getenv("OPENAI_API_KEY"):
            provider = OpenAIProvider(
                model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                api_key=os.getenv("OPENAI_API_KEY")
            )
        elif os.getenv("COMPATIBLE_API_KEY"):
            provider = OpenAICompatibleProvider(
                model_name=os.getenv("COMPATIBLE_MODEL_NAME", "mimo-v2.5-pro"),
                base_url=os.getenv("COMPATIBLE_BASE_URL", "http://localhost:8000/v1"),
                api_key=os.getenv("COMPATIBLE_API_KEY")
            )
        elif os.getenv("OPENROUTER_API_KEY"):
            provider = OpenAICompatibleProvider(
                model_name=os.getenv("OPENROUTER_MODEL_NAME", "google/gemini-2.5-flash"),
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY")
            )
        else:
            provider = GeminiProvider(
                model_name="gemini-2.5-flash",
                api_key=api_key
            )
        
        agent = VaccineAssistantAgent(llm=provider)
        stream_gen = agent.run_stream(messages)
    else:
        logger.info("No API_KEY found. Executing Mock Fallback Agent Stream...")
        stream_gen = stream_mock_agent(messages)
        
    for chunk in stream_gen:
        yield json.dumps(chunk, ensure_ascii=False) + "\n"

# ─────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────
@app.post("/api/chat", tags=["Agent"])
@app.post("/chat", tags=["Agent"])
def chat_endpoint(payload: ChatRequest):
    messages = payload.messages
    api_key = (
        os.getenv("OPENAI_API_KEY") 
        or os.getenv("COMPATIBLE_API_KEY") 
        or os.getenv("OPENROUTER_API_KEY") 
        or os.getenv("GEMINI_API_KEY")
    )
    return StreamingResponse(
        chat_stream_generator(messages, api_key),
        media_type="application/x-ndjson"
    )

@app.post("/api/callback", tags=["Agent"])
@app.post("/callback", tags=["Agent"])
async def register_callback(payload: CallbackRequest):
    logger.info(f"Registered pharmacist callback request: Name={payload.name}, Phone={payload.phone}, Details={payload.details}")
    return {
        "status": "success",
        "message": f"Dạ, trực ca đã nhận được thông tin. Hotline hỗ trợ 1800 6928 sẽ liên hệ đến số {payload.phone} trong 15 phút tới để tư vấn trực tiếp cho Anh/Chị {payload.name}."
    }

@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
        },
    }

@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    """
    Send a question to the AI agent.
    **Authentication:** Include header `X-API-Key: <your-key>`
    """
    user_id = body.user_id or "default_user"
    
    # 1. Rate limit check (stateless)
    rate_limiter.check(user_id)

    # 2. Cost budget check (stateless)
    cost_guard.check_budget(user_id)

    # Calculate input tokens estimate
    input_tokens = len(body.question.split()) * 2
    cost_guard.record_usage(user_id, input_tokens, 0)

    logger.info(json.dumps({
        "event": "agent_call",
        "user_id": user_id,
        "q_len": len(body.question),
        "client": str(request.client.host) if request.client else "unknown",
    }))

    # 3. Load conversation history
    history = get_history(user_id)

    # 4. Generate answer considering history
    answer = generate_answer_with_history(body.question, history)

    # 5. Save updated conversation history
    history.append({"role": "user", "content": body.question})
    history.append({"role": "assistant", "content": answer})
    if len(history) > 20:
        history = history[-20:]
    save_history(user_id, history)

    # Calculate output tokens estimate
    output_tokens = len(answer.split()) * 2
    cost_guard.record_usage(user_id, 0, output_tokens)

    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

@app.get("/health", tags=["Operations"])
def health():
    """Liveness probe. Platform restarts container if this fails."""
    status = "ok"
    checks = {"llm": "mock" if not settings.openai_api_key else "openai"}
    try:
        import psutil
        mem = psutil.virtual_memory()
        checks["memory"] = "ok" if mem.percent < 95 else "degraded"
        if mem.percent >= 95:
            status = "degraded"
    except ImportError:
        checks["memory"] = "ok (psutil not installed)"
        
    return {
        "status": status,
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/ready", tags=["Operations"])
def ready():
    """Readiness probe. Load balancer stops routing here if not ready."""
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    if r_conn:
        try:
            r_conn.ping()
        except Exception:
            raise HTTPException(503, "Redis not available")
    return {"ready": True}

@app.get("/metrics", tags=["Operations"])
def metrics(_key: str = Depends(verify_api_key)):
    """Basic metrics (protected)."""
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "redis_connected": r_conn is not None,
    }

# ─────────────────────────────────────────────────────────
# Graceful Shutdown
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))

signal.signal(signal.SIGTERM, _handle_signal)

if __name__ == "__main__":
    logger.info(f"Starting {settings.app_name} on {settings.host}:{settings.port}")
    logger.info(f"API Key: {settings.agent_api_key[:4]}****")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
