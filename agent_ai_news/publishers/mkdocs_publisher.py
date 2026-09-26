"""MkDocs Material web publishing and archive indexer."""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from agent_ai_news.config import get_settings


def parse_frontmatter(file_path: Path) -> Dict[str, str]:
    """Extract frontmatter title, date, and type from a markdown report."""
    content = file_path.read_text(encoding="utf-8")
    title = file_path.stem
    date = "Unknown Date"
    report_type = "research"

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            for line in fm_text.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip().strip('"').strip("'")
                    if key == "title" and val:
                        title = val
                    elif key == "date" and val:
                        date = val
                    elif key == "type" and val:
                        report_type = val

    return {"title": title, "date": date, "type": report_type}


def publish_to_site(report_path: Path, report_type: str = "research") -> Path:
    """Copy a generated report from reports/ into the appropriate site_docs subfolder."""
    settings = get_settings()
    site_docs_root = Path(settings.site_docs_dir)

    target_subdir = "digests" if report_type == "digest" else "research"
    dest_dir = site_docs_root / target_subdir
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_file = dest_dir / report_path.name
    shutil.copy2(report_path, dest_file)
    return dest_file


def rebuild_site_index() -> None:
    """Scan all reports in site_docs/ and update site_docs/index.md archive table."""
    settings = get_settings()
    site_docs_root = Path(settings.site_docs_dir)
    site_docs_root.mkdir(parents=True, exist_ok=True)

    all_reports: List[Dict[str, str]] = []

    for subfolder in ("digests", "research"):
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
                    "type": subfolder[:-1].capitalize(),
                    "link": rel_link,
                }
            )

    # Sort descending by date, then title
    all_reports.sort(key=lambda x: (x["date"], x["title"]), reverse=True)

    # Build the Markdown table
    if all_reports:
        rows = [
            f"| {r['date']} | `{r['type']}` | [{r['title']}]({r['link']}) | [Read Report]({r['link']}) |"
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
    replacement = rf"\1{table_content}\3"

    if re.search(pattern, existing_content):
        updated_content = re.sub(pattern, replacement, existing_content)
    else:
        updated_content = f"""# AI Intelligence Portal

Welcome to the **AI Intelligence Portal**. This knowledge archive is continuously updated by an autonomous research agent built on LangChain's **`deepagents`** harness.

---

## Latest Briefings & Research Archive

{table_content}

---

## How It Works
1. **Scouts**: News Scout scans breaking web & AI lab RSS feeds; Academic Scout queries arXiv & Hugging Face daily papers.
2. **Orchestrator**: Lead DeepAgent plans research steps and synthesizes findings into structured markdown.
3. **Publisher**: Generates searchable reports and updates this static archive.
"""

    index_file.write_text(updated_content, encoding="utf-8")
