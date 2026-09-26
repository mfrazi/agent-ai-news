# AI Information Research & Digest Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular AI intelligence research and digest agent using LangChain's `deepagents` harness, capable of interactive research, automated daily briefings, web publication via Material for MkDocs, and API access via FastAPI.

**Architecture:** A lead orchestrator Deep Agent dispatches tasks to two specialized subagents (News & Web Scout and Academic Paper Scout). Reports are stored in markdown and processed by a pluggable publisher pipeline into an automated MkDocs site deployed to GitHub Pages.

**Tech Stack:** Python 3.11+, deepagents, langchain, langchain-core, langchain-openai (for OpenRouter & OpenAI), langchain-google-genai, langchain-anthropic, tavily-python, duckduckgo-search, feedparser, httpx, mkdocs, mkdocs-material, fastapi, uvicorn, typer, pytest.

**Spec:** docs/superpowers/specs/2026-09-26-deepagents-ai-news-design.md

## Global Constraints
- Python 3.11+
- All code formatted and linted cleanly with strict type annotations
- OpenRouter, Gemini, OpenAI, Anthropic support via standard environment variables
- Safe fallback from Tavily to DuckDuckGo when `TAVILY_API_KEY` is absent or rate-limited
- All unit and integration test runs use `pytest` and mock external network APIs

## Review Focus
1. OpenRouter base URL or custom headers omitted in chat model factory -> verify `ChatOpenAI` always receives `base_url="https://openrouter.ai/api/v1"` and custom headers when provider is `openrouter`.
2. Tavily rate-limit / missing API key crash -> verify fallback to DuckDuckGo search runs cleanly without unhandled exceptions.
3. RSS feed parsing network error or malformed XML -> verify `fetch_ai_rss` catches network/parse errors gracefully and returns available items or empty list without crashing.
4. Report serialization failure when subagents return non-string or partial outputs -> verify report synthesizer normalizes output into the valid markdown template schema.
5. MkDocs site sync directory collision or missing index.md -> verify publisher initializes directory structure and safely appends/prepends to `index.md`.

---

### Task 1: Project Setup, Dependencies & Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `agent/__init__.py`
- Create: `agent/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: Environment variables (`OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, etc.)
- Produces: `agent_ai_news.config.Settings` (Pydantic settings object providing typed access to app configuration)

- [ ] **Step 1: Write the failing test for configuration loader**

```python
# tests/test_config.py
import os
import pytest
from agent_ai_news.config import Settings, get_settings

def test_settings_default_values(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = Settings(_env_file=None)
    assert settings.reports_dir == "reports"
    assert settings.site_docs_dir == "site_docs"
    assert settings.default_llm_provider is None

def test_settings_auto_detect_provider(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test12345")
    settings = Settings()
    assert settings.resolve_provider() == "openrouter"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'agent'`

- [ ] **Step 3: Implement `pyproject.toml`, `.env.example`, `.gitignore`, and `agent/config.py`**

Define dependencies (`deepagents`, `langchain`, `langchain-core`, `langchain-openai`, `langchain-google-genai`, `langchain-anthropic`, `pydantic-settings`, `feedparser`, `tavily-python`, `duckduckgo-search`, `httpx`, `fastapi`, `uvicorn`, `typer`, `mkdocs-material`, `pytest`) in `pyproject.toml`. Implement `agent/config.py` using `pydantic_settings.BaseSettings`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .env.example .gitignore agent/__init__.py agent/config.py tests/test_config.py
git commit -m "feat: setup project dependencies and configuration loader"
```

---

### Task 2: Provider-Agnostic LLM Factory

**Files:**
- Create: `agent/llm.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Consumes: `agent_ai_news.config.Settings`
- Produces: `get_chat_model(provider: str | None = None, model_name: str | None = None) -> BaseChatModel`

- [ ] **Step 1: Write the failing tests for LLM factory**

```python
# tests/test_llm.py
import pytest
from unittest.mock import patch, MagicMock
from agent_ai_news.llm import get_chat_model

def test_get_chat_model_openrouter(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-dummy")
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        model = get_chat_model(provider="openrouter", model_name="anthropic/claude-3.5-sonnet")
        mock_chat.assert_called_once()
        kwargs = mock_chat.call_args.kwargs
        assert str(kwargs.get("base_url")).rstrip("/") == "https://openrouter.ai/api/v1"
        assert kwargs.get("model") == "anthropic/claude-3.5-sonnet"
        assert "HTTP-Referer" in kwargs.get("default_headers", {})

def test_get_chat_model_unsupported():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_chat_model(provider="unknown_provider")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'agent_ai_news.llm'`

- [ ] **Step 3: Implement `get_chat_model` in `agent/llm.py`**

Support `openrouter`, `gemini` / `google_genai`, `openai`, and `anthropic`. Apply auto-detection if provider is not supplied.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/llm.py tests/test_llm.py
git commit -m "feat: add provider-agnostic LLM factory with OpenRouter support"
```

---

### Task 3: Information Retrieval Tools (Web, RSS, arXiv, Hugging Face)

**Files:**
- Create: `agent/tools/__init__.py`
- Create: `agent/tools/web_search.py`
- Create: `agent/tools/rss.py`
- Create: `agent/tools/arxiv.py`
- Create: `agent/tools/huggingface.py`
- Test: `tests/test_tools.py`

**Interfaces:**
- Consumes: Network HTTP endpoints / APIs
- Produces:
  - `agent_ai_news.tools.web_search.search_web(query: str, days: int = 7, max_results: int = 5) -> str`
  - `agent_ai_news.tools.rss.fetch_ai_rss(days: int = 3, max_entries_per_feed: int = 5) -> str`
  - `agent_ai_news.tools.arxiv.query_arxiv(topic: str, max_results: int = 5) -> str`
  - `agent_ai_news.tools.huggingface.query_hf_papers(limit: int = 5) -> str`

- [ ] **Step 1: Write the failing tests for source tools**

```python
# tests/test_tools.py
from unittest.mock import patch, MagicMock
from agent_ai_news.tools.web_search import search_web
from agent_ai_news.tools.rss import fetch_ai_rss
from agent_ai_news.tools.arxiv import query_arxiv
from agent_ai_news.tools.huggingface import query_hf_papers

def test_web_search_fallback_to_ddg(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    with patch("duckduckgo_search.DDGS.text") as mock_ddg:
        mock_ddg.return_value = [{"title": "AI Release", "href": "https://example.com", "body": "Summary"}]
        result = search_web("reasoning models")
        assert "AI Release" in result
        assert "https://example.com" in result

def test_arxiv_query_mock():
    mock_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Deep Reasoning in LLMs</title>
        <summary>Novel test-time compute scaling.</summary>
        <id>http://arxiv.org/abs/2609.99999</id>
        <author><name>Alice Smith</name></author>
      </entry>
    </feed>"""
    with patch("httpx.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, content=mock_xml)
        result = query_arxiv("reasoning models")
        assert "Deep Reasoning in LLMs" in result
        assert "Alice Smith" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'agent_ai_news.tools'`

- [ ] **Step 3: Implement tools in `agent/tools/`**

Implement `search_web` (Tavily with DDGS fallback), `fetch_ai_rss` (parses OpenAI, Google DeepMind, Anthropic, Hugging Face feeds), `query_arxiv` (queries arXiv Atom API), and `query_hf_papers` (calls HF Daily Papers API). Ensure all network errors are caught cleanly.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/tools/ tests/test_tools.py
git commit -m "feat: implement web, rss, arxiv, and huggingface tools with fallbacks"
```

---

### Task 4: Subagent & DeepAgent Orchestration

**Files:**
- Create: `agent/core/__init__.py`
- Create: `agent/core/scouts.py`
- Create: `agent/core/orchestrator.py`
- Test: `tests/test_scouts.py`

**Interfaces:**
- Consumes: `agent_ai_news.llm.get_chat_model`, `agent_ai_news.tools.*`
- Produces:
  - `agent_ai_news.core.scouts.create_news_scout_subagent(model) -> DeepAgent / Runnable`
  - `agent_ai_news.core.scouts.create_paper_scout_subagent(model) -> DeepAgent / Runnable`
  - `agent_ai_news.core.orchestrator.create_lead_research_agent(model) -> DeepAgent`

- [ ] **Step 1: Write the failing test for subagent builders**

```python
# tests/test_scouts.py
from unittest.mock import MagicMock
from agent_ai_news.core.scouts import create_news_scout_subagent, create_paper_scout_subagent
from agent_ai_news.core.orchestrator import create_lead_research_agent

def test_scout_agents_creation():
    mock_model = MagicMock()
    news_scout = create_news_scout_subagent(mock_model)
    paper_scout = create_paper_scout_subagent(mock_model)
    lead_agent = create_lead_research_agent(mock_model)
    assert news_scout is not None
    assert paper_scout is not None
    assert lead_agent is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scouts.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'agent_ai_news.core'`

- [ ] **Step 3: Implement `scouts.py` and `orchestrator.py`**

Use `deepagents.create_deep_agent` to construct the lead research agent equipped with planning (`todo`), workspace isolation, and delegation tools for the News Scout and Academic Paper Scout.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scouts.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/core/ tests/test_scouts.py
git commit -m "feat: build news and academic scout subagents with deepagents orchestrator"
```

---

### Task 5: Report Synthesis & Storage Engine

**Files:**
- Create: `agent/core/synthesizer.py`
- Test: `tests/test_synthesizer.py`

**Interfaces:**
- Consumes: Raw findings from subagents / research runs
- Produces:
  - `agent_ai_news.core.synthesizer.ResearchReport` (Pydantic model)
  - `agent_ai_news.core.synthesizer.format_report_markdown(report: ResearchReport) -> str`
  - `agent_ai_news.core.synthesizer.save_report(report_md: str, topic: str, report_type: str = "research") -> Path`

- [ ] **Step 1: Write the failing test for report synthesis and storage**

```python
# tests/test_synthesizer.py
import os
from pathlib import Path
from agent_ai_news.core.synthesizer import ResearchReport, format_report_markdown, save_report

def test_format_and_save_report(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_ai_news.config.get_settings", lambda: type("Dummy", (), {"reports_dir": str(tmp_path)})())
    report = ResearchReport(
        title="Reasoning Breakthroughs",
        date="2026-09-26",
        report_type="research",
        tags=["Reasoning", "LLMs"],
        executive_summary=["Test-time compute shows major gains."],
        industry_news=[{"title": "Lab A Release", "url": "https://example.com", "details": "New model"}],
        academic_papers=[{"title": "Paper 1", "authors": ["Alice"], "url": "https://arxiv.org/abs/1", "contribution": "New method"}],
        open_source=[],
        synthesis="The landscape is shifting to verification."
    )
    md_content = format_report_markdown(report)
    assert "# Reasoning Breakthroughs" in md_content
    assert "Test-time compute shows major gains." in md_content
    
    file_path = save_report(md_content, slug="reasoning-breakthroughs", report_type="research")
    assert file_path.exists()
    assert "Reasoning Breakthroughs" in file_path.read_text()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_synthesizer.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'agent_ai_news.core.synthesizer'`

- [ ] **Step 3: Implement `ResearchReport`, `format_report_markdown`, and `save_report` in `agent/core/synthesizer.py`**

Follow the frontmatter + markdown template defined in spec Section 5.3.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_synthesizer.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/core/synthesizer.py tests/test_synthesizer.py
git commit -m "feat: implement report formatting and persistence engine"
```

---

### Task 6: Static Web Publishing Pipeline (Material for MkDocs)

**Files:**
- Create: `mkdocs.yml`
- Create: `site_docs/index.md`
- Create: `site_docs/stylesheets/extra.css`
- Create: `agent/publishers/__init__.py`
- Create: `agent/publishers/mkdocs_publisher.py`
- Test: `tests/test_publisher.py`

**Interfaces:**
- Consumes: Generated markdown reports from `reports/`
- Produces:
  - `agent_ai_news.publishers.mkdocs_publisher.publish_to_site(report_path: Path, report_type: str = "research") -> Path`
  - `agent_ai_news.publishers.mkdocs_publisher.rebuild_site_index() -> None`

- [ ] **Step 1: Write the failing test for MkDocs publisher**

```python
# tests/test_publisher.py
from pathlib import Path
from agent_ai_news.publishers.mkdocs_publisher import publish_to_site, rebuild_site_index

def test_publish_to_site(tmp_path, monkeypatch):
    site_docs = tmp_path / "site_docs"
    site_docs.mkdir()
    (site_docs / "index.md").write_text("# AI Intelligence Portal\n\n## Archive\n")
    monkeypatch.setattr("agent_ai_news.config.get_settings", lambda: type("Dummy", (), {"site_docs_dir": str(site_docs)})())
    
    sample_report = tmp_path / "2026-09-26-ai-digest.md"
    sample_report.write_text("---\ntitle: Daily AI Digest\ndate: 2026-09-26\n---\n# Daily AI Digest\nContent")
    
    dest_file = publish_to_site(sample_report, report_type="digest")
    assert dest_file.exists()
    assert (site_docs / "digests" / "2026-09-26-ai-digest.md").exists()
    
    rebuild_site_index()
    index_content = (site_docs / "index.md").read_text()
    assert "Daily AI Digest" in index_content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_publisher.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'agent_ai_news.publishers'`

- [ ] **Step 3: Implement `mkdocs.yml`, `site_docs/` structure, and `agent/publishers/mkdocs_publisher.py`**

Configure Material theme with search, dark/light palette, and tags in `mkdocs.yml`. Implement `publish_to_site` and `rebuild_site_index` to sync reports and refresh the archive table.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_publisher.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add mkdocs.yml site_docs/ agent/publishers/ tests/test_publisher.py
git commit -m "feat: add MkDocs Material configuration and web publishing pipeline"
```

---

### Task 7: CLI & FastAPI Entrypoints

**Files:**
- Create: `agent/cli.py`
- Create: `agent/server.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_server.py`

**Interfaces:**
- Consumes: `agent_ai_news.core.orchestrator`, `agent_ai_news.core.synthesizer`, `agent_ai_news.publishers.mkdocs_publisher`
- Produces:
  - CLI commands: `research`, `digest`, `publish`
  - FastAPI routes: `/api/research`, `/api/digest`, `/api/reports`, `/health`

- [ ] **Step 1: Write the failing tests for CLI and FastAPI**

```python
# tests/test_server.py
from fastapi.testclient import TestClient
from unittest.mock import patch
from agent_ai_news.server import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_api_research_endpoint():
    with patch("agent_ai_news.core.orchestrator.run_research_query") as mock_run:
        mock_run.return_value = "reports/2026-09-26-research-test.md"
        response = client.post("/api/research", json={"query": "Test AI", "publish": False})
        assert response.status_code == 200
        assert "report_path" in response.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_server.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'agent_ai_news.server'`

- [ ] **Step 3: Implement `agent/cli.py` (with Typer) and `agent/server.py` (with FastAPI)**

Provide commands for `research`, `digest`, `publish [--serve]`, and endpoints for `/api/research`, `/api/digest`, `/api/reports`, `/health`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_server.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/cli.py agent/server.py tests/test_cli.py tests/test_server.py
git commit -m "feat: add Typer CLI commands and FastAPI REST server"
```

---

### Task 8: Docker Containerization & GitHub Actions Automated Briefing Workflow

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.github/workflows/ai-digest.yml`
- Test: `tests/test_workflow_syntax.py`

**Interfaces:**
- Consumes: Python 3.11 environment, Docker runtime, GitHub Actions runner
- Produces:
  - Deployable Docker image
  - Scheduled daily cron action (`08:00 UTC`) running digest and deploying static site to GitHub Pages

- [ ] **Step 1: Write the verification test for workflow and docker configuration**

```python
# tests/test_workflow_syntax.py
from pathlib import Path
import yaml

def test_workflow_file_valid():
    workflow_path = Path(".github/workflows/ai-digest.yml")
    assert workflow_path.exists()
    content = yaml.safe_load(workflow_path.read_text())
    assert "on" in content
    assert "schedule" in content["on"] or "workflow_dispatch" in content["on"]
    assert "jobs" in content

def test_dockerfile_exists():
    assert Path("Dockerfile").exists()
    assert Path("docker-compose.yml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_workflow_syntax.py -v`  
Expected: FAIL with `FileNotFoundError: .github/workflows/ai-digest.yml`

- [ ] **Step 3: Implement `Dockerfile`, `docker-compose.yml`, and `.github/workflows/ai-digest.yml`**

Ensure `Dockerfile` has multi-stage build, and GitHub Actions workflow runs the digest, updates the MkDocs index, commits reports, and deploys to GitHub Pages via `actions/deploy-pages`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_workflow_syntax.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml .github/workflows/ai-digest.yml tests/test_workflow_syntax.py
git commit -m "ci: add Dockerfile and GitHub Actions cron workflow for daily digest and pages deployment"
```

---

### Task 9: Project & Deployment Documentation (`README.md`)

**Files:**
- Create: `README.md`
- Test: `tests/test_readme.py`

**Interfaces:**
- Consumes: Environment configuration, CLI commands, Docker setup, and GitHub Actions cron workflow.
- Produces: `README.md` containing project overview, setup guide, API key configuration, CLI usage, and step-by-step deployment instructions (Local, Docker, GitHub Actions + GitHub Pages, and Cloud Run / Railway).

- [ ] **Step 1: Write verification test for README**

```python
# tests/test_readme.py
from pathlib import Path

def test_readme_contains_deployment_guides():
    readme_path = Path("README.md")
    assert readme_path.exists()
    content = readme_path.read_text()
    assert "Deployment" in content
    assert "Docker" in content
    assert "GitHub Actions" in content
    assert "GitHub Pages" in content
    assert "CLI Usage" in content
    assert "Environment Variables" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_readme.py -v`  
Expected: FAIL with `AssertionError: assert False (readme does not exist)`

- [ ] **Step 3: Implement `README.md`**

Write a clear, beginner-friendly `README.md` with:
1. Overview & Features.
2. Prerequisites & Installation (`pip install -e .` or `pip install -e ".[web]"`).
3. Environment variables guide (`OPENROUTER_API_KEY`, `GOOGLE_API_KEY`, `TAVILY_API_KEY`, etc.).
4. CLI Commands (`research`, `digest`, `publish --serve`).
5. How to Deploy:
   - **Option A: GitHub Actions & GitHub Pages** (zero-maintenance automated daily briefings).
   - **Option B: Docker / Docker Compose** (running containerized CLI or API server).
   - **Option C: Cloud Hosting (Google Cloud Run / Railway / Fly.io)** for the FastAPI endpoint.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_readme.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_readme.py
git commit -m "docs: add comprehensive README with local setup and deployment guides"
```

