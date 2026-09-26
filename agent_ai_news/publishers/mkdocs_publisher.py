"""MkDocs Material archive indexer."""

import html
import json
import re
from pathlib import Path
from typing import Dict, List
from agent_ai_news.config import get_settings
from agent_ai_news.core.synthesizer import REPORT_SUBFOLDERS


def _unquote(val: str) -> str:
    """Strip YAML-style quotes, decoding escapes in double-quoted strings."""
    if len(val) >= 2 and val[0] == val[-1] == '"':
        try:
            return json.loads(val)
        except ValueError:
            return val[1:-1]
    if len(val) >= 2 and val[0] == val[-1] == "'":
        return val[1:-1].replace("''", "'")
    return val


def parse_frontmatter(file_path: Path) -> Dict[str, str]:
    """Extract frontmatter title and date from a markdown report."""
    content = file_path.read_text(encoding="utf-8")
    title = file_path.stem
    date = "Unknown Date"

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            for line in fm_text.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = _unquote(val.strip())
                    if key == "title" and val:
                        title = val
                    elif key == "date" and val:
                        date = val

    return {"title": title, "date": date}


def _table_cell(text: str) -> str:
    """Escape a title for a markdown table link label: HTML, table and link syntax render as plain text."""
    text = html.escape(text, quote=False)
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def rebuild_site_index() -> None:
    """Scan all reports in site_docs/ and update site_docs/index.md archive table."""
    settings = get_settings()
    site_docs_root = Path(settings.site_docs_dir)
    site_docs_root.mkdir(parents=True, exist_ok=True)

    all_reports: List[Dict[str, str]] = []

    for report_type, subfolder in REPORT_SUBFOLDERS.items():
        folder_path = site_docs_root / subfolder
        if not folder_path.exists():
            continue

        for md_file in folder_path.glob("*.md"):
            meta = parse_frontmatter(md_file)
            rel_link = f"{subfolder}/{md_file.name}"
            all_reports.append(
                {
                    "title": meta["title"],
                    "date": meta["date"],
                    "type": report_type.capitalize(),
                    "link": rel_link,
                }
            )

    # Sort descending by date, then title
    all_reports.sort(key=lambda x: (x["date"], x["title"]), reverse=True)

    # Build the Markdown table
    if all_reports:
        rows = [
            f"| {_table_cell(r['date'])} | `{r['type']}` | [{_table_cell(r['title'])}]({r['link']}) | [Read Report]({r['link']}) |"
            for r in all_reports
        ]
        table_content = "| Date | Type | Title | Link |\n| :--- | :--- | :--- | :--- |\n" + "\n".join(rows)
    else:
        table_content = (
            "| Date | Type | Topic / Title | Link |\n"
            "| :--- | :--- | :--- | :--- |\n"
            "| *No reports published yet. Run `python -m agent_ai_news.cli digest` to generate your first briefing.* | - | - | - |"
        )

    index_file = site_docs_root / "index.md"
    existing_content = index_file.read_text(encoding="utf-8") if index_file.exists() else ""

    # Replace table section between '## Latest Briefings & Research Archive' and '## How It Works'
    pattern = r"(## Latest Briefings & Research Archive\s*\n\n)([\s\S]*?)(\n\n---|\n\n## How It Works|$)"

    if re.search(pattern, existing_content):
        # Callable replacement: report titles may contain backslashes that re.sub would treat as escapes
        updated_content = re.sub(
            pattern, lambda m: f"{m.group(1)}{table_content}{m.group(3)}", existing_content, count=1
        )
    else:
        updated_content = f"""# AI Intelligence Portal

Welcome to the **AI Intelligence Portal**. This knowledge archive is continuously updated by an autonomous research agent built on LangChain's **`deepagents`** harness.

---

## Latest Briefings & Research Archive

{table_content}

---

## How It Works
1. **Scouts**: News Scout scans breaking web & AI lab RSS feeds; Academic Scout queries Hugging Face daily papers & searches the web for research papers.
2. **Orchestrator**: Lead DeepAgent plans research steps and synthesizes findings into structured markdown.
3. **Publisher**: Generates searchable reports and updates this static archive.
"""

    index_file.write_text(updated_content, encoding="utf-8")
