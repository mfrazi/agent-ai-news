"""Command line interface for agent-ai-news."""

from typing import Optional
import logging
import subprocess
import sys
import typer
from langgraph.errors import GraphRecursionError
from rich.console import Console
from agent_ai_news.config import output_base_dir
from agent_ai_news.core.orchestrator import DEFAULT_DIGEST_TOPIC, build_digest_query, run_research_query
from agent_ai_news.llm import MissingCredentialsError
from agent_ai_news.core.synthesizer import save_report
from agent_ai_news.publishers.mkdocs_publisher import rebuild_site_index

app = typer.Typer(
    help="agent-ai-news: Autonomous research and briefing generator using deepagents.",
    add_completion=False,
)
console = Console()


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show debug logs, including every HTTP request"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Hide agent progress logs"),
):
    """Configure logging so long agent runs report what they are doing."""
    level = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)-7s %(message)s", datefmt="%H:%M:%S")
    if not verbose:
        # One line per HTTP request drowns out the agent progress lines
        # openai>=2 ships its own httpx2/httpcore2 copies with separate logger names
        for noisy in ("httpx", "httpcore", "httpx2", "httpcore2", "openai", "anthropic", "google_genai"):
            logging.getLogger(noisy).setLevel(logging.WARNING)


def _run_query(query: str, **kwargs) -> str:
    """Run the research agent, turning expected failures into clean CLI errors."""
    try:
        return run_research_query(query, **kwargs)
    except MissingCredentialsError as exc:
        console.print(f"[bold red]✗ {exc}[/bold red]")
        raise typer.Exit(code=1) from None
    except GraphRecursionError:
        console.print(
            "[bold red]✗ Agent hit its step limit without finishing. "
            "Raise AGENT_RECURSION_LIMIT in .env or narrow the query.[/bold red]"
        )
        raise typer.Exit(code=1) from None


@app.command()
def research(
    query: str = typer.Argument(..., help="Topic or question to research in-depth"),
    openrouter_provider: Optional[str] = typer.Option(
        None,
        "--openrouter-provider",
        "--openrouter-providers",
        help="Preferred OpenRouter inference provider(s), e.g. 'Together,DeepInfra'",
    ),
):
    """Run an ad-hoc research deep dive on an AI topic."""
    console.print(f"[bold cyan]🔍 Starting research on:[/bold cyan] {query}")
    report_content = _run_query(query, openrouter_providers=openrouter_provider)
    saved_path = save_report(report_content, slug=query, report_type="research")
    rebuild_site_index()
    console.print(f"[bold green]✓ Report saved and added to site index:[/bold green] {saved_path}")

    console.print("\n" + "=" * 50 + "\n")
    console.print(report_content)


@app.command()
def digest(
    days: int = typer.Option(1, "--days", "-d", min=1, help="Lookback window in days (e.g. 1 for daily, 7 for weekly)"),
    topic: str = typer.Option(DEFAULT_DIGEST_TOPIC, "--topic", "-t", help="Topics of interest"),
    openrouter_provider: Optional[str] = typer.Option(
        None,
        "--openrouter-provider",
        "--openrouter-providers",
        help="Preferred OpenRouter inference provider(s), e.g. 'Together,DeepInfra'",
    ),
):
    """Compile an automated AI intelligence briefing across web, lab RSS, and Hugging Face."""
    query = build_digest_query(days, topic)
    console.print(f"[bold cyan]📰 Compiling {days}-day intelligence briefing...[/bold cyan]")
    report_content = _run_query(query, report_type="digest", openrouter_providers=openrouter_provider)
    saved_path = save_report(report_content, slug="daily-digest", report_type="digest")
    rebuild_site_index()
    console.print(f"[bold green]✓ Briefing saved and added to site index:[/bold green] {saved_path}")

    console.print("\n" + "=" * 50 + "\n")
    console.print(report_content)


@app.command()
def publish(
    serve: bool = typer.Option(False, "--serve", "-s", help="Start local MkDocs preview server after rebuilding index"),
):
    """Rebuild site_docs/index.md from existing reports (e.g. after editing or deleting one)."""
    rebuild_site_index()
    console.print("[bold green]✓ MkDocs archive index rebuilt successfully.[/bold green]")

    if serve:
        console.print("[bold cyan]🌐 Starting MkDocs preview server at http://127.0.0.1:8000 ...[/bold cyan]")
        # This interpreter's mkdocs (not whatever is first on PATH), run from the project root where mkdocs.yml lives
        subprocess.run([sys.executable, "-m", "mkdocs", "serve"], cwd=output_base_dir())


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host; use 0.0.0.0 to accept remote connections"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
):
    """Start the FastAPI server. API calls need the X-API-Key header (see AGENT_API_KEY)."""
    import uvicorn

    console.print(f"[bold green]🚀 Launching API server on {host}:{port}...[/bold green]")
    uvicorn.run("agent_ai_news.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
