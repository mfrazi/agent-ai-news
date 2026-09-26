"""FastAPI web server for AI Intelligence Agent."""

from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from agent.config import get_settings
from agent.core.orchestrator import run_research_query
from agent.core.synthesizer import save_report
from agent.publishers.mkdocs_publisher import publish_to_site, rebuild_site_index

app = FastAPI(
    title="AI Intelligence Agent API",
    description="Autonomous AI research and digest API powered by LangChain deepagents",
    version="0.1.0",
)


class ResearchRequest(BaseModel):
    query: str
    publish: bool = False


class DigestRequest(BaseModel):
    days: int = 1
    topics: List[str] = Field(default_factory=list)
    publish: bool = False


@app.get("/health")
def health_check():
    """Service health verification endpoint."""
    return {"status": "ok"}


@app.post("/api/research")
def research_endpoint(req: ResearchRequest):
    """Execute on-demand research on an AI topic."""
    result_content = run_research_query(req.query)
    saved_path = save_report(result_content, slug=req.query, report_type="research")

    if req.publish:
        publish_to_site(saved_path, report_type="research")
        rebuild_site_index()

    return {
        "status": "success",
        "report_path": str(saved_path),
        "content": result_content,
    }


@app.post("/api/digest")
def digest_endpoint(req: DigestRequest):
    """Generate a scheduled or on-demand intelligence briefing."""
    topic_str = ", ".join(req.topics) if req.topics else "General AI, LLMs, and Open Source"
    query = f"Compile an AI intelligence digest for the past {req.days} days covering: {topic_str}"
    result_content = run_research_query(query)
    saved_path = save_report(result_content, slug="daily-digest", report_type="digest")

    if req.publish:
        publish_to_site(saved_path, report_type="digest")
        rebuild_site_index()

    return {
        "status": "success",
        "report_path": str(saved_path),
        "content": result_content,
    }


@app.get("/api/reports")
def list_reports():
    """List all available reports in the reports directory."""
    settings = get_settings()
    reports_dir = Path(settings.reports_dir)
    if not reports_dir.exists():
        return {"reports": []}

    reports = [
        {"filename": p.name, "size_bytes": p.stat().st_size}
        for p in reports_dir.glob("*.md")
    ]
    return {"reports": sorted(reports, key=lambda x: x["filename"], reverse=True)}


@app.get("/api/reports/{filename}")
def get_report(filename: str):
    """Retrieve the content of a specific report."""
    settings = get_settings()
    target_path = Path(settings.reports_dir) / filename
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail=f"Report '{filename}' not found.")
    return {"filename": filename, "content": target_path.read_text(encoding="utf-8")}
