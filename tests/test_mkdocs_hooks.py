# tests/test_mkdocs_hooks.py
from types import SimpleNamespace
from agent_ai_news.publishers.mkdocs_hooks import on_page_content, on_page_markdown, sanitize_html


def test_sanitize_removes_script_handlers_and_dangerous_urls():
    dirty = (
        "<p>ok <strong>bold</strong></p><script>alert(1)</script>"
        '<img src="x" onerror="alert(2)">'
        '<a href="javascript:alert(3)">js</a>'
        '<a href="data:text/html,<script>alert(4)</script>">data</a>'
        '<iframe src="https://evil.example"></iframe>'
        '<form action="https://evil.example"><input type="submit"></form>'
    )
    clean = sanitize_html(dirty)
    assert "<script" not in clean and "alert(1)" not in clean
    assert "onerror" not in clean
    assert "javascript:" not in clean and "data:" not in clean
    assert "<iframe" not in clean and "<form" not in clean and 'type="submit"' not in clean
    assert "<p>ok <strong>bold</strong></p>" in clean


def test_sanitize_keeps_markdown_extension_output():
    rendered = (
        '<h2 id="findings">Findings</h2>'
        '<table><thead><tr><th style="text-align: left;">A</th></tr></thead></table>'
        '<div class="admonition note"><p class="admonition-title">Note</p></div>'
        '<details><summary>More</summary><p>x</p></details>'
        '<ul class="task-list"><li class="task-list-item"><label class="task-list-control">'
        '<input type="checkbox" disabled checked><span class="task-list-indicator"></span></label> done</li></ul>'
        '<div class="highlight"><pre><span></span><code><span class="n">x</span></code></pre></div>'
        '<a href="https://example.com/paper">paper</a> <a href="#findings">anchor</a>'
    )
    clean = sanitize_html(rendered)
    for kept in (
        '<h2 id="findings">',
        'style="text-align:left"',
        'class="admonition note"',
        "<details><summary>More</summary>",
        'type="checkbox"',
        '<span class="n">x</span>',
        'href="https://example.com/paper"',
        'href="#findings"',
    ):
        assert kept in clean, kept


def test_only_checkbox_inputs_survive():
    assert 'type="text"' not in sanitize_html('<input type="text" value="x">')


def test_page_title_is_escaped_and_content_sanitized():
    page = SimpleNamespace(meta={"title": "<img src=x onerror=alert(1)> & more"})
    assert on_page_markdown("# body", page=page) == "# body"
    assert page.meta["title"] == "&lt;img src=x onerror=alert(1)&gt; &amp; more"
    assert "<script" not in on_page_content("<script>alert(1)</script><p>x</p>", page=page)


def test_mkdocs_config_registers_hook():
    import yaml
    from pathlib import Path

    mkdocs_yml = Path(__file__).resolve().parent.parent / "mkdocs.yml"  # independent of the working directory
    config = yaml.safe_load(mkdocs_yml.read_text(encoding="utf-8"))
    assert "agent_ai_news/publishers/mkdocs_hooks.py" in config["hooks"]


def test_site_builds_strict(tmp_path):
    """The real site builds without warnings (e.g. nav entries pointing at missing pages)."""
    import subprocess
    import sys
    import pytest
    from pathlib import Path

    pytest.importorskip("mkdocs")
    project_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(tmp_path / "site")],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert (tmp_path / "site" / "index.html").exists()
