# tests/test_workflow_syntax.py
import re
from pathlib import Path
import yaml

# Resolve from this file, not the working directory: IDE runners may start pytest inside tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "ai-digest.yml"


def _load_workflow() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def test_workflow_file_valid():
    assert WORKFLOW_PATH.exists()
    content = _load_workflow()
    triggers = content.get("on") or content.get(True) or {}  # YAML 1.1 parses a bare `on` key as True
    assert "schedule" in triggers or "workflow_dispatch" in triggers
    assert "jobs" in content


def test_dockerfile_exists():
    dockerfile = PROJECT_ROOT / "Dockerfile"
    assert dockerfile.exists()
    assert "FROM python:3.11-slim" in dockerfile.read_text()
    assert (PROJECT_ROOT / "docker-compose.yml").exists()


def test_workflow_hardening():
    content = _load_workflow()
    assert content["permissions"] == {"contents": "write"}
    for step in content["jobs"]["digest-and-publish"]["steps"]:
        # ${{ }} inside a shell script is expanded before the shell runs: a script-injection vector
        assert "${{" not in step.get("run", ""), step["name"]
        if "uses" in step:
            assert re.search(r"@[0-9a-f]{40}$", step["uses"]), f"{step['uses']} is not pinned to a commit SHA"


def test_workflow_passes_model_override_and_variable():
    content = _load_workflow()
    triggers = content.get("on") or content.get(True)
    assert triggers["workflow_dispatch"]["inputs"]["model"]["default"] == ""
    digest = next(s for s in content["jobs"]["digest-and-publish"]["steps"] if s["name"].startswith("Generate"))
    assert digest["env"]["AGENT_MODEL_NAME"] == "${{ inputs.model || vars.AGENT_MODEL_NAME || '' }}"
    # empty provider lets Settings auto-detect it from whichever API key secret is set
    assert digest["env"]["AGENT_LLM_PROVIDER"] == "${{ secrets.AGENT_LLM_PROVIDER || '' }}"
