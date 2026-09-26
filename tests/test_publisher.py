# tests/test_publisher.py
from pathlib import Path
from agent.publishers.mkdocs_publisher import publish_to_site, rebuild_site_index


def test_publish_to_site(tmp_path, monkeypatch):
    site_docs = tmp_path / "site_docs"
    site_docs.mkdir()
    (site_docs / "index.md").write_text("# AI Intelligence Portal\n\n## Archive\n")
    monkeypatch.setattr(
        "agent.publishers.mkdocs_publisher.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(site_docs)})(),
    )

    sample_report = tmp_path / "2026-09-26-ai-digest.md"
    sample_report.write_text(
        '---\ntitle: "Daily AI Digest"\ndate: 2026-09-26\ntype: digest\n---\n\n# Daily AI Digest\n\nContent details...',
        encoding="utf-8",
    )

    dest_file = publish_to_site(sample_report, report_type="digest")
    assert dest_file.exists()
    assert (site_docs / "digests" / "2026-09-26-ai-digest.md").exists()

    rebuild_site_index()
    index_content = (site_docs / "index.md").read_text()
    assert "Daily AI Digest" in index_content
    assert "2026-09-26" in index_content


def test_publish_creates_missing_directories(tmp_path, monkeypatch):
    site_docs = tmp_path / "missing_site_docs"
    monkeypatch.setattr(
        "agent.publishers.mkdocs_publisher.get_settings",
        lambda: type("Dummy", (), {"site_docs_dir": str(site_docs)})(),
    )

    sample_report = tmp_path / "2026-09-26-research-reasoning.md"
    sample_report.write_text(
        '---\ntitle: "Reasoning Deep Dive"\ndate: 2026-09-26\ntype: research\n---\n\n# Reasoning Deep Dive\n\nAnalysis...',
        encoding="utf-8",
    )

    dest_file = publish_to_site(sample_report, report_type="research")
    assert dest_file.exists()
    assert (site_docs / "research" / "2026-09-26-research-reasoning.md").exists()

    rebuild_site_index()
    assert (site_docs / "index.md").exists()
    assert "Reasoning Deep Dive" in (site_docs / "index.md").read_text()
