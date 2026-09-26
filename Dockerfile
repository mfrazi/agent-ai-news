# Multi-stage Dockerfile for agent-ai-news
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .[web]

FROM python:3.11-slim

WORKDIR /app

# Copy installed python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY agent_ai_news/ agent_ai_news/
COPY mkdocs.yml .
COPY site_docs/ site_docs/
COPY pyproject.toml .

# Install project editable without reinstalling deps, then drop root: the server only needs
# to write reports into site_docs/ (uid 1000 matches the usual host owner of the bind mount)
RUN pip install --no-deps -e . \
    && useradd --create-home --uid 1000 app \
    && chown -R app:app /app
USER app

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# Default command: run FastAPI server
CMD ["uvicorn", "agent_ai_news.server:app", "--host", "0.0.0.0", "--port", "8000"]
