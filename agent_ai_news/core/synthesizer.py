"""Report markdown normalization and storage."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from agent_ai_news.config import get_settings


def _frontmatter(title: str, date: str, report_type: str, tags: List[str]) -> str:
    """YAML frontmatter block read by the MkDocs publisher."""
    return (
        f"---\ntitle: {json.dumps(title, ensure_ascii=False)}\ndate: {date}\n"
        f"type: {report_type}\ntags: [{', '.join(tags)}]\n---\n"
    )


# report_type -> site_docs subfolder; mkdocs.yml nav lists these folders
REPORT_SUBFOLDERS = {"research": "research", "digest": "digests"}

MAX_SLUG_LENGTH = 60
MARKDOWN_HEADING = re.compile(r"^#{1,2} \S", re.MULTILINE)
# A leading YAML block of `key: value` lines; a bare horizontal rule (---) must not match
LEADING_FRONTMATTER = re.compile(r"\A---[ \t]*\n(?:[A-Za-z_][\w-]*[ \t]*:.*\n)+---[ \t]*(?:\n|\Z)")


def slugify(text: str) -> str:
    """Convert a title/string into a safe URL slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    # Keep filenames well under filesystem limits (255 bytes) for long queries
    return text[:MAX_SLUG_LENGTH].rstrip("-")


def normalize_to_report_markdown(
    raw_content: str,
    title: str = "AI Intelligence Report",
    report_type: str = "research",
    tags: Optional[List[str]] = None,
    date_str: Optional[str] = None,
) -> str:
    """Wrap the agent's markdown report in the frontmatter the MkDocs publisher reads."""
    today = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    title = " ".join(title.split())  # a newline would break the heading and the index table row
    frontmatter = _frontmatter(title, today, report_type, tags or ["AI", "Research"])

    # Frontmatter written by the model is replaced, so title/date/type always come from us
    content = LEADING_FRONTMATTER.sub("", raw_content, count=1)

    # The agent usually writes a complete markdown report. Keep its structure and drop any
    # conversational preamble before the first heading.
    first_heading = MARKDOWN_HEADING.search(content)
    body = content[first_heading.start():].strip() if first_heading else content.strip()
    if not body.startswith("# "):
        body = f"# {title}\n\n{body}"
    return f"{frontmatter}\n{body}\n"


def save_report(
    report_md: str,
    slug: str = "report",
    report_type: str = "research",
    date_str: Optional[str] = None,
) -> Path:
    """Save report markdown into the MkDocs site under site_docs/<research|digests>/."""
    settings = get_settings()
    out_dir = Path(settings.site_docs_dir) / REPORT_SUBFOLDERS.get(report_type, "research")
    out_dir.mkdir(parents=True, exist_ok=True)

    today = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    clean_slug = slugify(slug) or "report"

    if report_type == "digest":
        filename = f"{today}-ai-digest.md"
    else:
        filename = f"{today}-research-{clean_slug}.md"

    target_path = out_dir / filename
    target_path.write_text(report_md, encoding="utf-8")
    return target_path
