# tests/test_workflow_syntax.py
from pathlib import Path
import yaml


def test_workflow_file_valid():
    workflow_path = Path(".github/workflows/ai-digest.yml")
    assert workflow_path.exists()
    content = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    assert "on" in content or True  # YAML parser parses `on` as boolean True in 1.1 unless quoted
    triggers = content.get("on") or content.get(True) or {}
    assert "schedule" in triggers or "workflow_dispatch" in triggers
    assert "jobs" in content


def test_dockerfile_exists():
    dockerfile = Path("Dockerfile")
    assert dockerfile.exists()
    assert "FROM python:3.11-slim" in dockerfile.read_text()
    assert Path("docker-compose.yml").exists()
