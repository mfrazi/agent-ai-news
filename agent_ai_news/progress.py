"""Progress logging for long-running agent executions."""

import logging
import threading
import time
from typing import Any, Dict, Optional
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger("agent_ai_news.progress")

MAX_PREVIEW_CHARS = 120


def _preview(value: Any) -> str:
    """Single-line, truncated representation of a tool input for logs."""
    text = " ".join(str(value).split())
    return text if len(text) <= MAX_PREVIEW_CHARS else text[: MAX_PREVIEW_CHARS - 3] + "..."


def _agent_name(metadata: Optional[Dict[str, Any]]) -> str:
    """Name of the (sub)agent that owns a run, as tagged by deepagents/langchain."""
    return (metadata or {}).get("lc_agent_name") or "lead_agent"


class ProgressCallbackHandler(BaseCallbackHandler):
    """Log every LLM call and tool call, plus a periodic heartbeat for slow steps.

    Callbacks propagate from the lead agent into subagents, so one handler covers the whole run.
    """

    def __init__(self, heartbeat_interval: float = 30.0):
        self.heartbeat_interval = heartbeat_interval
        self._active: Dict[UUID, tuple] = {}
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._started_at = time.monotonic()
        self.llm_calls = 0
        self.tool_calls = 0

    # -- lifecycle -----------------------------------------------------------

    def __enter__(self) -> "ProgressCallbackHandler":
        self._started_at = time.monotonic()
        if self.heartbeat_interval > 0:
            self._thread = threading.Thread(target=self._heartbeat, name="agent-heartbeat", daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        logger.info(
            "Agent run ended after %.0fs (%d LLM calls, %d tool calls)",
            time.monotonic() - self._started_at,
            self.llm_calls,
            self.tool_calls,
        )

    def _heartbeat(self) -> None:
        while not self._stop.wait(self.heartbeat_interval):
            now = time.monotonic()
            with self._lock:
                active = list(self._active.values())
            if not active:
                logger.info("Still running (%.0fs elapsed), between steps", now - self._started_at)
                continue
            waiting = "; ".join(f"{label} for {now - started:.0f}s" for label, started in active)
            logger.info("Still running (%.0fs elapsed), waiting on: %s", now - self._started_at, waiting)

    def _begin(self, run_id: UUID, label: str) -> None:
        with self._lock:
            self._active[run_id] = (label, time.monotonic())

    def _end(self, run_id: UUID) -> tuple:
        with self._lock:
            label, started = self._active.pop(run_id, ("step", time.monotonic()))
        return label, time.monotonic() - started

    # -- LLM callbacks -------------------------------------------------------

    def on_chat_model_start(self, serialized, messages, *, run_id, metadata=None, **kwargs) -> None:
        self.llm_calls += 1
        label = f"LLM call #{self.llm_calls} ({_agent_name(metadata)})"
        self._begin(run_id, label)
        logger.info("%s started", label)

    def on_llm_end(self, response, *, run_id, **kwargs) -> None:
        label, elapsed = self._end(run_id)
        tool_names = []
        for generations in getattr(response, "generations", []) or []:
            for generation in generations:
                message = getattr(generation, "message", None)
                tool_names += [call.get("name", "?") for call in getattr(message, "tool_calls", None) or []]
        next_step = f", requested tools: {', '.join(tool_names)}" if tool_names else ", no tool calls"
        logger.info("%s finished in %.1fs%s", label, elapsed, next_step)

    def on_llm_error(self, error, *, run_id, **kwargs) -> None:
        label, elapsed = self._end(run_id)
        logger.warning("%s failed after %.1fs: %s", label, elapsed, error)

    # -- tool callbacks ------------------------------------------------------

    def on_tool_start(self, serialized, input_str, *, run_id, metadata=None, inputs=None, **kwargs) -> None:
        self.tool_calls += 1
        name = (serialized or {}).get("name") or kwargs.get("name") or "tool"
        if name == "task" and isinstance(inputs, dict):
            # deepagents delegates to subagents through the `task` tool
            label = f"subagent '{inputs.get('subagent_type', '?')}'"
            detail = inputs.get("description", "")
        else:
            label = f"tool '{name}' ({_agent_name(metadata)})"
            detail = inputs if inputs is not None else input_str
        self._begin(run_id, label)
        logger.info("%s started: %s", label, _preview(detail))

    def on_tool_end(self, output, *, run_id, **kwargs) -> None:
        label, elapsed = self._end(run_id)
        content = getattr(output, "content", output)
        logger.info("%s finished in %.1fs (%d chars)", label, elapsed, len(str(content)))

    def on_tool_error(self, error, *, run_id, **kwargs) -> None:
        label, elapsed = self._end(run_id)
        logger.warning("%s failed after %.1fs: %s", label, elapsed, error)
