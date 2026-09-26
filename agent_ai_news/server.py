"""FastAPI web server for agent-ai-news."""

import logging
import secrets
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Dict, List, Optional
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from agent_ai_news import __version__
from agent_ai_news.config import get_settings
from agent_ai_news.core.orchestrator import run_research_query
from agent_ai_news.core.synthesizer import REPORT_SUBFOLDERS, save_report
from agent_ai_news.publishers.mkdocs_publisher import rebuild_site_index

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


@lru_cache()
def _api_key() -> str:
    """Key clients must send; a random one is generated for this process when AGENT_API_KEY is unset."""
    configured = get_settings().agent_api_key
    if configured:
        return configured
    generated = secrets.token_urlsafe(32)
    logger.warning(
        "AGENT_API_KEY is not set; generated a temporary API key for this server process: %s", generated
    )
    return generated


def require_api_key(provided: Optional[str] = Security(API_KEY_HEADER)) -> None:
    """Reject requests without the API key: every /api call can spend LLM credits or read reports."""
    if not provided or not secrets.compare_digest(provided.encode(), _api_key().encode()):
        raise HTTPException(status_code=401, detail="Missing or invalid API key (X-API-Key header).")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _api_key()  # resolve at startup so a generated key is logged before the first request
    yield


app = FastAPI(
    title="agent-ai-news API",
    description="Autonomous AI research and digest API powered by LangChain deepagents",
    version=__version__,
    lifespan=lifespan,
)
api = APIRouter(prefix="/api", dependencies=[Depends(require_api_key)])

Topic = Annotated[str, Field(min_length=1, max_length=100)]


class ResearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    openrouter_provider: Optional[str] = Field(default=None, max_length=200)


class DigestRequest(BaseModel):
    days: int = Field(default=1, ge=1, le=365)
    topics: List[Topic] = Field(default_factory=list, max_length=10)
    openrouter_provider: Optional[str] = Field(default=None, max_length=200)


@app.get("/health")
def health_check():
    """Service health verification endpoint."""
    return {"status": "ok"}


@api.post("/research")
def research_endpoint(req: ResearchRequest):
    """Execute on-demand research on an AI topic."""
    result_content = run_research_query(req.query, openrouter_providers=req.openrouter_provider)
    saved_path = save_report(result_content, slug=req.query, report_type="research")
    rebuild_site_index()

    return {
        "status": "success",
        "report_path": str(saved_path),
        "content": result_content,
    }


@api.post("/digest")
def digest_endpoint(req: DigestRequest):
    """Generate a scheduled or on-demand intelligence briefing."""
    topic_str = ", ".join(req.topics) if req.topics else "General AI, LLMs, and Open Source"
    query = f"Compile an AI intelligence digest for the past {req.days} days covering: {topic_str}"
    result_content = run_research_query(query, report_type="digest", openrouter_providers=req.openrouter_provider)
    saved_path = save_report(result_content, slug="daily-digest", report_type="digest")
    rebuild_site_index()

    return {
        "status": "success",
        "report_path": str(saved_path),
        "content": result_content,
    }


def _report_dirs() -> Dict[str, Path]:
    """report_type -> resolved site_docs subfolder holding that type of report."""
    site_docs = Path(get_settings().site_docs_dir)
    return {report_type: (site_docs / sub).resolve() for report_type, sub in REPORT_SUBFOLDERS.items()}


@api.get("/reports")
def list_reports():
    """List all reports published in the MkDocs site."""
    reports = [
        {"filename": p.name, "type": report_type, "size_bytes": p.stat().st_size}
        for report_type, folder in _report_dirs().items()
        if folder.is_dir()
        for p in folder.glob("*.md")
    ]
    return {"reports": sorted(reports, key=lambda x: x["filename"], reverse=True)}


@api.get("/reports/{filename}")
def get_report(filename: str):
    """Retrieve the content of a specific report."""
    for folder in _report_dirs().values():
        target_path = (folder / filename).resolve()
        # Only files directly inside a report folder; blocks ../ traversal
        if target_path.parent == folder and target_path.is_file():
            return {"filename": filename, "content": target_path.read_text(encoding="utf-8")}
    raise HTTPException(status_code=404, detail=f"Report '{filename}' not found.")


app.include_router(api)
