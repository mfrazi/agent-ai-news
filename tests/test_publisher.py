# tests/test_publisher.py
from agent_ai_news.publishers.mkdocs_publisher import rebuild_site_index


def test_rebuild_index_lists_reports(tmp_path, monkeypatch):
    site_docs = tmp_path / "site_docs"
    (site_docs / "digests").mkdir(parents=True)
    (site_docs / "index.md").write_text("# AI Intelligence Portal\n\n## Archive\n")
    monkeypatch.setattr(
        "agent_ai_news.publishers.mkdocs_publisher.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(site_docs)})(),
    )
    (site_docs / "digests" / "2026-09-26-ai-digest.md").write_text(
        '---\ntitle: "Daily AI Digest"\ndate: 2026-09-26\ntype: digest\n---\n\n# Daily AI Digest\n\nContent details...',
        encoding="utf-8",
    )

    rebuild_site_index()
    index_content = (site_docs / "index.md").read_text()
    assert "Daily AI Digest" in index_content
    assert "2026-09-26" in index_content
    assert "`Digest`" in index_content


def test_rebuild_index_creates_missing_site_docs(tmp_path, monkeypatch):
    site_docs = tmp_path / "missing_site_docs"
    monkeypatch.setattr(
        "agent_ai_news.publishers.mkdocs_publisher.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(site_docs)})(),
    )
    (site_docs / "research").mkdir(parents=True)
    (site_docs / "research" / "2026-09-26-research-reasoning.md").write_text(
        '---\ntitle: "Reasoning Deep Dive"\ndate: 2026-09-26\ntype: research\n---\n\n# Reasoning Deep Dive\n\nAnalysis...',
        encoding="utf-8",
    )

    rebuild_site_index()
    assert (site_docs / "index.md").exists()
    assert "Reasoning Deep Dive" in (site_docs / "index.md").read_text()
    assert "`Research`" in (site_docs / "index.md").read_text()


def test_rebuild_index_with_special_character_titles(tmp_path, monkeypatch):
    site_docs = tmp_path / "site_docs"
    monkeypatch.setattr(
        "agent_ai_news.publishers.mkdocs_publisher.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(site_docs)})(),
    )
    (site_docs / "research").mkdir(parents=True)
    (site_docs / "index.md").write_text(
        "# Portal\n\n## Latest Briefings & Research Archive\n\n| old |\n\n---\n\n## How It Works\n",
        encoding="utf-8",
    )
    (site_docs / "research" / "2026-09-26-research-x.md").write_text(
        '---\ntitle: "What is \\\\alpha | \\"beta\\"?"\ndate: 2026-09-26\ntype: research\n---\n\nBody',
        encoding="utf-8",
    )

    rebuild_site_index()

    index = (site_docs / "index.md").read_text()
    assert "| old |" not in index
    assert 'What is \\\\alpha \\| "beta"?' in index
    assert "## How It Works" in index


def test_rebuild_index_escapes_html_in_titles(tmp_path, monkeypatch):
    site_docs = tmp_path / "site_docs"
    (site_docs / "research").mkdir(parents=True)
    monkeypatch.setattr(
        "agent_ai_news.publishers.mkdocs_publisher.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(site_docs)})(),
    )
    (site_docs / "research" / "2026-09-26-research-x.md").write_text(
        '---\ntitle: "<img src=x onerror=alert(1)>"\ndate: 2026-09-26\n---\n\nBody', encoding="utf-8"
    )
    rebuild_site_index()
    index = (site_docs / "index.md").read_text()
    assert "<img" not in index
    assert "&lt;img src=x onerror=alert(1)&gt;" in index


def test_rebuild_index_placeholder_uses_same_header(tmp_path, monkeypatch):
    site_docs = tmp_path / "site_docs"
    monkeypatch.setattr(
        "agent_ai_news.publishers.mkdocs_publisher.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(site_docs)})(),
    )
    rebuild_site_index()
    index = (site_docs / "index.md").read_text()
    assert "| Date | Type | Title | Link |" in index
    assert "No reports published yet" in index
