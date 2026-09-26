# Design Specification: AI Information Research & Digest Agent

**Date:** 2026-09-26  
**Status:** Draft / Pending Review  
**Target Package:** `agent`  
**Harness:** LangChain `deepagents`  

---

## 1. Overview & Goals

The goal of this project is to create an autonomous research and intelligence agent specialized in finding, analyzing, and synthesizing the latest developments in Artificial Intelligence (frontier models, research papers, open-source releases, and industry news).

The system uses LangChain's **`deepagents`** harness, utilizing its built-in planning (`todo`), subagent delegation with isolated contexts, and filesystem-backed working memory.

### Core Capabilities
* **Interactive Deep-Dive Research:** Ask ad-hoc technical questions (e.g. *"What are the latest breakthroughs in test-time compute for reasoning models?"*) and receive comprehensive, cited reports.
* **Automated Periodic Digest:** Run scheduled briefings (e.g. daily or weekly) tracking breaking lab releases, top trending arXiv papers, and Hugging Face models.
* **Multi-Provider Support:** Provider-agnostic LLM factory supporting **OpenRouter**, **Google Gemini**, **OpenAI**, and **Anthropic**.
* **Dual Interface & Deployment:** 
  - Rich CLI for local interactive research and scheduled runs.
  - FastAPI server for remote/API-driven research and integration.
  - Automated deployment support via Docker and GitHub Actions cron schedule.

---

## 2. System Architecture & Component Design

The architecture centers on an orchestrating **Lead Research Deep Agent** coordinating two specialized subagents:

```
                            ┌──────────────────────────────────┐
                            │    User / CLI / FastAPI Endpoint │
                            └────────────────┬─────────────────┘
                                             │
                                             ▼
                            ┌──────────────────────────────────┐
                            │      Lead Research Agent         │
                            │      (DeepAgent Harness)         │
                            │  - Planning (todo tool)          │
                            │  - Workspace Manager             │
                            │  - Report Synthesizer            │
                            └────────┬─────────────────┬───────┘
                                     │                 │
                   ┌─────────────────┘                 └──────────────────┐
                   ▼                                                      ▼
       ┌────────────────────────┐                             ┌────────────────────────┐
       │   News & Web Scout     │                             │  Academic Paper Scout  │
       │       Subagent         │                             │        Subagent        │
       │  - Tavily Web Search   │                             │  - arXiv Search API    │
       │  - DuckDuckGo fallback │                             │  - HF Daily Papers API │
       │  - AI Lab RSS Reader   │                             │  - Paper Extraction    │
       └────────────────────────┘                             └────────────────────────┘
```

### 2.1 Subagents & Roles

1. **Lead Research Agent (Orchestrator):**
   - Instantiated via `deepagents.create_deep_agent`.
   - Breaks down research goals or digest criteria into structured sub-tasks.
   - Dispatches tasks to subagents without polluting its main reasoning loop with raw search/HTML dumps.
   - Integrates findings from both subagents, validates citations, and formats the final markdown report.

2. **News & Web Scout Subagent:**
   - Focus: Breaking industry news, corporate lab announcements, product launches, benchmarks.
   - Tools:
     - `web_search`: Primary Tavily search; automatic DuckDuckGo fallback.
     - `fetch_ai_rss`: Curated RSS feeds for Google DeepMind, OpenAI, Anthropic, Meta AI, Mistral AI, Hugging Face blog.

3. **Academic Paper Scout Subagent:**
   - Focus: Frontier research, novel architectures, theoretical advancements, open weights.
   - Tools:
     - `query_arxiv`: Queries `cs.AI`, `cs.CL`, `cs.LG`, `cs.CV` sorted by submission date.
     - `query_hf_papers`: Queries Hugging Face Daily Papers API (`/api/daily_papers`) with upvote filtering.

---

## 3. LLM Provider Architecture (Factory Pattern)

The agent connects to LLMs through a unified factory (`agent.llm.get_chat_model`) configured via environment variables.

### Supported Providers
1. **OpenRouter (`openrouter`):**
   - Uses `langchain-openai.ChatOpenAI` pointing to `https://openrouter.ai/api/v1`.
   - Headers: `HTTP-Referer: https://github.com/langchain-ai/deepagents`, `X-Title: AI Intelligence Agent`.
   - Default Model: `anthropic/claude-3.5-sonnet` or `deepseek/deepseek-r1`.
   - Env: `OPENROUTER_API_KEY`.
2. **Google Gemini (`gemini` / `google_genai`):**
   - Uses `langchain-google-genai.ChatGoogleGenerativeAI`.
   - Default Model: `gemini-2.5-pro` or `gemini-2.0-flash`.
   - Env: `GOOGLE_API_KEY`.
3. **OpenAI (`openai`):**
   - Uses `langchain-openai.ChatOpenAI`.
   - Default Model: `gpt-4o` or `o3-mini`.
   - Env: `OPENAI_API_KEY`.
4. **Anthropic (`anthropic`):**
   - Uses `langchain-anthropic.ChatAnthropic`.
   - Default Model: `claude-3-5-sonnet-latest`.
   - Env: `ANTHROPIC_API_KEY`.

### Auto-Detection & Fallback
If `AGENT_LLM_PROVIDER` is not explicitly set, the factory inspects available keys in priority order:
`OPENROUTER_API_KEY` $\rightarrow$ `GOOGLE_API_KEY` $\rightarrow$ `OPENAI_API_KEY` $\rightarrow$ `ANTHROPIC_API_KEY`.

---

## 4. Tools & Connectors Specification

### 4.1 Web Search (`agent.tools.web_search`)
* **Signature:** `search_web(query: str, days: int = 7, max_results: int = 5) -> str`
* **Behavior:**
  - If `TAVILY_API_KEY` is set, uses Tavily Search API with `topic="news"` or `time_range`.
  - If missing or if Tavily returns a quota/rate-limit error, catches the error and executes `DuckDuckGoSearchRun`.
  - Returns sanitized snippets, title, and source URL.

### 4.2 RSS Feed Ingestion (`agent.tools.rss`)
* **Signature:** `fetch_ai_rss(days: int = 3, max_entries_per_feed: int = 5) -> str`
* **Sources:**
  - OpenAI News (`https://openai.com/news/rss.xml`)
  - Google DeepMind Blog (`https://deepmind.google/blog/rss.xml`)
  - Anthropic News (`https://www.anthropic.com/news/feed`)
  - Hugging Face Blog (`https://huggingface.co/blog/feed.xml`)
  - Meta AI Blog RSS
* **Behavior:**
  - Parses publication dates (`parsedatetime` or `feedparser`).
  - Filters entries older than `days`.
  - Returns title, lab, summary snippet, and URL.

### 4.3 arXiv Query (`agent.tools.arxiv`)
* **Signature:** `query_arxiv(topic: str, max_results: int = 5, categories: list[str] = ["cs.AI", "cs.LG", "cs.CL"]) -> str`
* **Behavior:**
  - Queries `http://export.arxiv.org/api/query`.
  - Sorts by `submittedDate` descending.
  - Extracts title, authors, abstract summary, and PDF/abstract URLs.

### 4.4 Hugging Face Daily Papers (`agent.tools.huggingface`)
* **Signature:** `query_hf_papers(limit: int = 5) -> str`
* **Behavior:**
  - Fetches `https://huggingface.co/api/daily_papers`.
  - Sorts by upvotes and recency.
  - Returns paper title, authors, upvotes, summary, and Hugging Face link.

---

## 5. Output Schema & Memory Management

### 5.1 Working Filesystem Memory
* Uses `deepagents`' native filesystem integration.
* Working scratchpad lives in `.agent_workspace/` (ignored in `.gitignore`).
* Subagents write intermediate synthesis notes to disk, enabling long-context retention without token overflow.

### 5.2 Report Storage & Naming
Reports are persistently written to `reports/`:
* Research Deep Dives: `reports/YYYY-MM-DD-research-<slug>.md`
* Periodic Digests: `reports/YYYY-MM-DD-ai-digest.md`

### 5.3 Report Markdown Template
```markdown
# [Title: AI Intelligence Briefing / Research Topic]
**Date:** YYYY-MM-DD | **Period:** Past N Days | **Generated By:** DeepAgents AI Researcher

## Executive Summary
- 3–5 bullet points summarizing the most critical takeaways.

## 1. Industry & Lab Announcements
- **[Announcement Title]** - *Source: [Lab](URL)*
  - Core announcement details and benchmark claims.
  - Industry implications.

## 2. Academic & Frontier Research
- **[Paper Title]** - *Authors* ([arXiv:XXXX.XXXXX](URL) / [Hugging Face](URL))
  - Core problem tackled & technical contribution.
  - Methodological breakthroughs and test results.

## 3. Open Source Releases & Weights
- Open model weights, code repositories, or datasets with direct links.

## 4. Synthesis & Emerging Trends
- Synthesis of where the field is heading and open questions.
```

---

## 6. Interfaces & Entrypoints

### 6.1 CLI (`agent.cli`)
Built using `typer` or `argparse`:
```bash
# Ad-hoc interactive research
python -m agent.cli research "Emerging approaches to test-time reasoning and verification"

# Daily digest (past 24h)
python -m agent.cli digest --days 1 --topic "Frontier LLMs, Multimodal, Open Weights"

# Weekly digest (past 7 days)
python -m agent.cli digest --days 7 --output "reports/weekly-digest.md"
```

### 6.2 FastAPI Service (`agent.server`)
Lightweight web interface for remote trigger and integration:
* `POST /api/research` (`{ "query": string, "max_sources": int }`)
* `POST /api/digest` (`{ "days": int, "topics": string[] }`)
* `GET /api/reports` (Lists generated reports)
* `GET /api/reports/{filename}` (Downloads/reads report)
* `GET /health` (Healthcheck endpoint)

---

## 7. Deployment & Hosting Strategy

### 7.1 Docker (`Dockerfile` & `docker-compose.yml`)
* Base Image: `python:3.11-slim`
* Multi-stage build for minimal image size.
* Can be run as:
  - Background server (`uvicorn agent.server:app --host 0.0.0.0 --port 8000`).
  - One-off CLI command (`docker run --env-file .env ai-agent digest --days 1`).

### 7.2 GitHub Actions Cron Workflow (`.github/workflows/ai-digest.yml`)
* Automated daily briefing at `08:00 UTC`.
* Steps:
  1. Checkout repository.
  2. Set up Python 3.11 with dependencies cached.
  3. Run `python -m agent.cli digest --days 1`.
  4. Automatically commit new briefing in `reports/` back to repository branch.
  5. *(Optional)* Send summary notification to Slack/Discord webhook if configured.

### 7.3 Cloud Serverless / Container Targets
* **Google Cloud Run / Railway / Fly.io:** Ready out-of-the-box using the provided `Dockerfile`.
* **Modal:** Compatible script export (`deploy_modal.py`) for serverless cron execution.

---

## 8. Error Handling & Resilience

1. **Tool Fallbacks:** If Tavily search fails (invalid key or rate limit), log a warning and seamlessly execute DuckDuckGo search.
2. **Graceful Partial Failures:** If arXiv or an RSS feed fails to respond, proceed with available sources rather than aborting.
3. **API Rate Limiting & Retries:** LLM and search calls implement exponential backoff with jitter (tenacity / langchain built-in retry).
4. **Input Validation:** Pydantic schemas for all CLI and FastAPI inputs.

---

## 9. Testing & Quality Assurance Plan

* **Unit Tests (`tests/test_tools.py`):**
  - Web search with mock Tavily and fallback to DDG.
  - RSS parser with sample mock XML feed.
  - arXiv API parser with sample response.
  - HF Daily Papers API parser with mock JSON.
* **Factory Tests (`tests/test_llm.py`):**
  - Verify OpenRouter client creation with correct base URL and custom headers.
  - Verify Gemini, OpenAI, and Anthropic initialization.
* **Agent Integration Tests (`tests/test_agent.py`):**
  - End-to-end dry-run with mock LLM and mock tool returns, verifying report structure and filesystem writes.
