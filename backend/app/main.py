"""FastAPI application entrypoint."""
from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager  # noqa: E402
from time import perf_counter  # noqa: E402

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from .api import chat, documents  # noqa: E402
from .config import get_settings  # noqa: E402
from .db.database import init_db  # noqa: E402
from .observability import metrics  # noqa: E402
from .observability.logging_config import get_logger  # noqa: E402

settings = get_settings()
logger = get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time-Ms", "X-LLM-Total-Tokens", "X-Est-Cost-USD"],
)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    m = metrics.new_request()
    start = perf_counter()
    response = await call_next(request)
    total_ms = round((perf_counter() - start) * 1000, 1)

    response.headers["X-Process-Time-Ms"] = str(total_ms)
    response.headers["X-LLM-Total-Tokens"] = str(m.total_tokens)
    response.headers["X-Est-Cost-USD"] = f"{m.est_cost_usd:.6f}"

    logger.info(
        "request",
        extra={
            "ctx": {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "total_ms": total_ms,
                "llm_calls": m.llm_calls,
                "total_tokens": m.total_tokens,
                "est_cost_usd": round(m.est_cost_usd, 6),
                "timings_ms": m.timings_ms,
            }
        },
    )
    return response


app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {
        "status": "ok",
        "llm_backend": settings.llm_backend,
        "embedding_backend": settings.embedding_backend,
    }
