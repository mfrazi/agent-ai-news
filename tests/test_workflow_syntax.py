# tests/test_workflow_syntax.py
import re
from pathlib import Path
import pytest
import yaml

# Resolve from this file, not the working directory: IDE runners may start pytest inside tests/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
DIGEST_WORKFLOW = WORKFLOWS_DIR / "ai-digest.yml"
DEPLOY_WORKFLOW = WORKFLOWS_DIR / "deploy-site.yml"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _triggers(content: dict) -> dict:
    return content.get("on") or content.get(True) or {}  # YAML 1.1 parses a bare `on` key as True


def test_workflow_file_valid():
    assert DIGEST_WORKFLOW.exists()
    content = _load(DIGEST_WORKFLOW)
    triggers = _triggers(content)
    assert "schedule" in triggers or "workflow_dispatch" in triggers
    assert "jobs" in content


def test_dockerfile_exists():
    dockerfile = PROJECT_ROOT / "Dockerfile"
    assert dockerfile.exists()
    assert "FROM python:3.11-slim" in dockerfile.read_text()
    assert (PROJECT_ROOT / "docker-compose.yml").exists()


@pytest.mark.parametrize("workflow", [DIGEST_WORKFLOW, DEPLOY_WORKFLOW], ids=lambda p: p.name)
def test_workflow_hardening(workflow):
    content = _load(workflow)
    for job_name, job in content["jobs"].items():
        if "uses" in job:
            # a reusable workflow call must stay inside this repository
            assert job["uses"].startswith("./.github/workflows/"), job_name
        for step in job.get("steps", []):
            # ${{ }} inside a shell script is expanded before the shell runs: a script-injection vector
            assert "${{" not in step.get("run", ""), step["name"]
            if "uses" in step:
                assert re.search(r"@[0-9a-f]{40}$", step["uses"]), f"{step['uses']} is not pinned to a commit SHA"
            if step.get("uses", "").startswith("actions/setup-python@") and step["with"].get("cache") == "pip":
                # the default cache key file is requirements.txt, which does not exist here
                assert step["with"]["cache-dependency-path"] == "pyproject.toml", step["name"]


def test_digest_workflow_permissions_and_deploy_call():
    content = _load(DIGEST_WORKFLOW)
    assert content["permissions"] == {"contents": "write"}
    deploy = content["jobs"]["deploy-site"]
    assert deploy["uses"] == "./.github/workflows/deploy-site.yml"
    assert deploy["needs"] == "digest-and-publish"
    assert deploy["permissions"] == {"contents": "read", "pages": "write", "id-token": "write"}


def test_deploy_workflow_triggers_and_artifact():
    content = _load(DEPLOY_WORKFLOW)
    triggers = _triggers(content)
    assert {"push", "workflow_dispatch", "workflow_call"} <= set(triggers)
    assert triggers["push"]["branches"] == ["main"]
    assert {"site_docs/**", "mkdocs.yml"} <= set(triggers["push"]["paths"])
    assert content["permissions"] == {"contents": "read", "pages": "write", "id-token": "write"}
    upload = next(s for s in content["jobs"]["build"]["steps"] if "upload-pages-artifact" in s.get("uses", ""))
    assert upload["with"]["path"] == "site"  # mkdocs build output directory


def test_digest_runs_weekly_on_sunday_morning_utc_plus_7():
    content = _load(DIGEST_WORKFLOW)
    triggers = _triggers(content)
    # 08:00 UTC+7 on Sunday == 01:00 UTC on Sunday (GitHub cron is always UTC)
    assert triggers["schedule"] == [{"cron": "0 1 * * 0"}]
    assert triggers["workflow_dispatch"]["inputs"]["days"]["default"] == 7
    digest = next(s for s in content["jobs"]["digest-and-publish"]["steps"] if s["name"].startswith("Generate"))
    assert digest["env"]["DIGEST_DAYS"] == "${{ inputs.days || 7 }}"


def test_workflow_passes_model_override_and_variable():
    content = _load(DIGEST_WORKFLOW)
    assert _triggers(content)["workflow_dispatch"]["inputs"]["model"]["default"] == ""
    digest = next(s for s in content["jobs"]["digest-and-publish"]["steps"] if s["name"].startswith("Generate"))
    assert digest["env"]["AGENT_MODEL_NAME"] == "${{ inputs.model || vars.AGENT_MODEL_NAME || '' }}"
    # empty provider lets Settings auto-detect it from whichever API key secret is set
    assert digest["env"]["AGENT_LLM_PROVIDER"] == "${{ secrets.AGENT_LLM_PROVIDER || '' }}"
