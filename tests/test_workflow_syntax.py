# tests/test_workflow_syntax.py
from pathlib import Path
import yaml


def test_workflow_file_valid():
    workflow_path = Path(".github/workflows/ai-digest.yml")
    assert workflow_path.exists()
    content = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    triggers = content.get("on") or content.get(True) or {}  # YAML 1.1 parses a bare `on` key as True
    assert "schedule" in triggers or "workflow_dispatch" in triggers
    assert "jobs" in content


def test_dockerfile_exists():
    dockerfile = Path("Dockerfile")
    assert dockerfile.exists()
    assert "FROM python:3.11-slim" in dockerfile.read_text()
    assert Path("docker-compose.yml").exists()


def test_workflow_hardening():
    import re

    content = yaml.safe_load(Path(".github/workflows/ai-digest.yml").read_text(encoding="utf-8"))
    assert content["permissions"] == {"contents": "write"}
    for step in content["jobs"]["digest-and-publish"]["steps"]:
        # ${{ }} inside a shell script is expanded before the shell runs: a script-injection vector
        assert "${{" not in step.get("run", ""), step["name"]
        if "uses" in step:
            assert re.search(r"@[0-9a-f]{40}$", step["uses"]), f"{step['uses']} is not pinned to a commit SHA"
