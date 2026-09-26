# tests/test_synthesizer.py
from agent_ai_news.core.synthesizer import normalize_to_report_markdown, save_report


def test_save_research_report(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agent_ai_news.core.synthesizer.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(tmp_path)})(),
    )
    md_content = normalize_to_report_markdown("# Reasoning Breakthroughs\n\nFindings.", title="Reasoning")
    file_path = save_report(md_content, slug="reasoning-breakthroughs", report_type="research", date_str="2026-09-26")
    assert file_path == tmp_path / "research" / "2026-09-26-research-reasoning-breakthroughs.md"
    assert "# Reasoning Breakthroughs" in file_path.read_text()


def test_save_report_digest_naming(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agent_ai_news.core.synthesizer.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(tmp_path)})(),
    )
    file_path = save_report("# Daily AI Digest", slug="daily-digest", report_type="digest", date_str="2026-09-26")
    assert file_path == tmp_path / "digests" / "2026-09-26-ai-digest.md"
    assert file_path.exists()


def test_normalize_plain_text_output():
    raw_llm_output = "Here are the findings: DeepSeek released R1 with reinforcement learning."
    normalized = normalize_to_report_markdown(
        raw_content=raw_llm_output,
        title="Reasoning Models",
        report_type="digest",
        tags=["Reasoning"],
        date_str="2026-09-26",
    )
    assert normalized == (
        '---\ntitle: "Reasoning Models"\ndate: 2026-09-26\ntype: digest\ntags: [Reasoning]\n---\n\n'
        "# Reasoning Models\n\nHere are the findings: DeepSeek released R1 with reinforcement learning.\n"
    )


def test_title_with_quotes_is_valid_frontmatter():
    normalized = normalize_to_report_markdown(
        raw_content="Findings.",
        title='The "Bitter Lesson" revisited',
        date_str="2026-09-26",
    )
    assert 'title: "The \\"Bitter Lesson\\" revisited"' in normalized


def test_save_report_long_query_slug(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "agent_ai_news.core.synthesizer.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(tmp_path)})(),
    )
    file_path = save_report("# R", slug="what is new in reasoning " * 30, date_str="2026-09-26")
    assert file_path.exists()
    assert len(file_path.name.encode("utf-8")) < 255

    fallback = save_report("# R", slug="???", date_str="2026-09-26")
    assert fallback.name == "2026-09-26-research-report.md"


def test_normalize_keeps_structured_agent_report():
    raw = (
        "Both scouts have returned. Here is the synthesized briefing.\n\n---\n\n"
        "# Research Briefing: Test-Time Compute\n\n## Executive Summary\n- Real point\n\n"
        "## 2. Academic & Frontier Research\n- Paper A"
    )
    normalized = normalize_to_report_markdown(raw, title="Test-time compute", date_str="2026-09-26")
    assert normalized.startswith('---\ntitle: "Test-time compute"\ndate: 2026-09-26\ntype: research')
    assert "Both scouts have returned" not in normalized
    assert normalized.count("## Executive Summary") == 1
    assert "# Research Briefing: Test-Time Compute" in normalized
    assert "No new academic preprints" not in normalized


def test_normalize_adds_title_when_report_has_no_h1():
    normalized = normalize_to_report_markdown("## Findings\n- A", title="Topic", date_str="2026-09-26")
    assert "\n# Topic\n\n## Findings" in normalized


def test_normalize_replaces_frontmatter_written_by_model():
    raw = '---\ntitle: "Model title"\ntype: digest\n---\n\n# Briefing\n\nBody'
    normalized = normalize_to_report_markdown(raw, title="Real query", date_str="2026-09-26")
    assert normalized.startswith('---\ntitle: "Real query"\ndate: 2026-09-26\ntype: research')
    assert "Model title" not in normalized
    assert normalized.count("\n---\n") == 1  # only the closing line of our own frontmatter


def test_normalize_keeps_leading_horizontal_rule_content():
    raw = "---\n\nIntro paragraph without headings.\n\n---\n\nMore text."
    normalized = normalize_to_report_markdown(raw, title="Topic", date_str="2026-09-26")
    assert "Intro paragraph without headings." in normalized
    assert "More text." in normalized


def test_normalize_collapses_newlines_in_title():
    normalized = normalize_to_report_markdown("Body", title="line one\nline two", date_str="2026-09-26")
    assert 'title: "line one line two"' in normalized
    assert "\n# line one line two\n" in normalized
