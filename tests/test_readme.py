# tests/test_readme.py
from pathlib import Path


def test_readme_contains_deployment_guides():
    readme_path = Path("README.md")
    assert readme_path.exists()
    content = readme_path.read_text(encoding="utf-8")
    assert "Deployment" in content
    assert "Docker" in content
    assert "GitHub Actions" in content
    assert "GitHub Pages" in content
    assert "CLI Usage" in content
    assert "Environment Variables" in content
