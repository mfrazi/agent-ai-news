"""Command line interface for AI Intelligence Agent."""

import subprocess
import typer
from rich.console import Console
from agent.core.orchestrator import run_research_query
from agent.core.synthesizer import save_report
from agent.publishers.mkdocs_publisher import publish_to_site, rebuild_site_index

app = typer.Typer(
    help="AI Intelligence Agent: Autonomous research and briefing generator using deepagents.",
    add_completion=False,
)
console = Console()


@app.command()
def research(
    query: str = typer.Argument(..., help="Topic or question to research in-depth"),
    publish: bool = typer.Option(True, "--publish/--no-publish", help="Publish report to MkDocs static site"),
):
    """Run an ad-hoc research deep dive on an AI topic."""
    console.print(f"[bold cyan]🔍 Starting research on:[/bold cyan] {query}")
    report_content = run_research_query(query)
    saved_path = save_report(report_content, slug=query, report_type="research")
    console.print(f"[bold green]✓ Report saved to:[/bold green] {saved_path}")

    if publish:
        site_path = publish_to_site(saved_path, report_type="research")
        rebuild_site_index()
        console.print(f"[bold blue]✓ Published to static site archive:[/bold blue] {site_path}")

    console.print("\n" + "=" * 50 + "\n")
    console.print(report_content)


@app.command()
def digest(
    days: int = typer.Option(1, "--days", "-d", help="Lookback window in days (e.g. 1 for daily, 7 for weekly)"),
    topic: str = typer.Option("General AI, Frontier Models, Open Weights", "--topic", "-t", help="Topics of interest"),
    publish: bool = typer.Option(True, "--publish/--no-publish", help="Publish digest to MkDocs static site"),
):
    """Compile an automated AI intelligence briefing across web, lab RSS, arXiv, and Hugging Face."""
    query = f"Compile an AI intelligence digest for the past {days} days covering: {topic}"
    console.print(f"[bold cyan]📰 Compiling {days}-day intelligence briefing...[/bold cyan]")
    report_content = run_research_query(query)
    saved_path = save_report(report_content, slug="daily-digest", report_type="digest")
    console.print(f"[bold green]✓ Briefing saved to:[/bold green] {saved_path}")

    if publish:
        site_path = publish_to_site(saved_path, report_type="digest")
        rebuild_site_index()
        console.print(f"[bold blue]✓ Published to static site archive:[/bold blue] {site_path}")

    console.print("\n" + "=" * 50 + "\n")
    console.print(report_content)


@app.command()
def publish(
    serve: bool = typer.Option(False, "--serve", "-s", help="Start local MkDocs preview server after rebuilding index"),
):
    """Rebuild the static documentation archive index from existing reports."""
    rebuild_site_index()
    console.print("[bold green]✓ MkDocs archive index rebuilt successfully.[/bold green]")

    if serve:
        console.print("[bold cyan]🌐 Starting MkDocs preview server at http://127.0.0.1:8000 ...[/bold cyan]")
        subprocess.run(["mkdocs", "serve"])


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
):
    """Start the FastAPI server."""
    import uvicorn

    console.print(f"[bold green]🚀 Launching API server on {host}:{port}...[/bold green]")
    uvicorn.run("agent.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
