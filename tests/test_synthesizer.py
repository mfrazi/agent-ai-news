# tests/test_synthesizer.py
import os
from pathlib import Path
from agent.core.synthesizer import (
    ResearchReport,
    format_report_markdown,
    normalize_to_report_markdown,
    save_report,
)


def test_format_and_save_report(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agent.core.synthesizer.get_settings",
        lambda: type("Dummy", (), {"reports_dir": str(tmp_path)})(),
    )
    report = ResearchReport(
        title="Reasoning Breakthroughs",
        date="2026-09-26",
        report_type="research",
        tags=["Reasoning", "LLMs"],
        executive_summary=["Test-time compute shows major gains."],
        industry_news=[
            {"title": "Lab A Release", "url": "https://example.com", "details": "New model"}
        ],
        academic_papers=[
            {
                "title": "Paper 1",
                "authors": ["Alice"],
                "url": "https://arxiv.org/abs/1",
                "contribution": "New method",
            }
        ],
        open_source=[
            {"name": "OpenWeights-70B", "url": "https://huggingface.co/model", "details": "Apache 2.0 weights"}
        ],
        synthesis="The landscape is shifting to verification.",
    )
    md_content = format_report_markdown(report)
    assert "# Reasoning Breakthroughs" in md_content
    assert "Test-time compute shows major gains." in md_content
    assert "Lab A Release" in md_content
    assert "Paper 1" in md_content
    assert "OpenWeights-70B" in md_content

    file_path = save_report(md_content, slug="reasoning-breakthroughs", report_type="research")
    assert file_path.exists()
    assert "Reasoning Breakthroughs" in file_path.read_text()


def test_save_report_digest_naming(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agent.core.synthesizer.get_settings",
        lambda: type("Dummy", (), {"reports_dir": str(tmp_path)})(),
    )
    file_path = save_report("# Daily AI Digest", slug="daily-digest", report_type="digest", date_str="2026-09-26")
    assert file_path.name == "2026-09-26-ai-digest.md"
    assert file_path.exists()


def test_normalize_raw_content_to_report_markdown():
    raw_llm_output = "Here are the findings: DeepSeek released R1 with reinforcement learning."
    normalized = normalize_to_report_markdown(
        raw_content=raw_llm_output,
        title="Reasoning Models",
        report_type="research",
        tags=["Reasoning"],
        date_str="2026-09-26",
    )
    assert normalized.startswith("---")
    assert 'title: "Reasoning Models"' in normalized
    assert "date: 2026-09-26" in normalized
    assert "type: research" in normalized
    assert "## Executive Summary" in normalized
    assert "DeepSeek released R1" in normalized
