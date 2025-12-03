#!/usr/bin/env python
"""CLI tool to analyze and verify LLM agent execution from debug logs.

Analyzes synthesis output JSON files from debug runs and generates a summary table.
Can analyze a single debug run or all runs in a directory.
"""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    help="Analyze LLM agent execution from debug logs",
    no_args_is_help=True,
)

console = Console()


def extract_ticker_from_filename(filename: str) -> str:
    """Extract ticker symbol from filename like 'ZS_synthesis_output_*.json'."""
    parts = filename.split("_")
    if parts:
        return parts[0]
    return "UNKNOWN"


def parse_synthesis_output(file_path: Path) -> dict:
    """Parse a synthesis output JSON file and extract key metrics.

    Args:
        file_path: Path to the synthesis output JSON file

    Returns:
        Dictionary with extracted metrics
    """
    try:
        with open(file_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        console.print(f"[red]Error reading {file_path.name}: {e}[/red]")
        return None

    # Extract basic info
    ticker = extract_ticker_from_filename(file_path.name)
    status = data.get("status", "unknown")

    # Extract timestamp from filename (e.g., "ZS_synthesis_output_20251202_163820.json")
    filename_parts = file_path.stem.split("_")
    timestamp = None
    if len(filename_parts) >= 4:
        date_part = filename_parts[-2]
        time_part = filename_parts[-1]
        timestamp = f"{date_part}_{time_part}"

    # Try to extract the investment signal from raw JSON
    result = data.get("result", {})
    raw_text = result.get("raw", "")

    recommendation = None
    final_score = None
    confidence = None
    tech_score = None
    fund_score = None
    sent_score = None
    token_usage = None
    fallback_mode = False

    # Parse the raw JSON string if it exists
    if raw_text:
        try:
            # Extract JSON from markdown code block if present
            if "```json" in raw_text:
                json_start = raw_text.find("```json") + 7
                json_end = raw_text.find("```", json_start)
                json_str = raw_text[json_start:json_end].strip()
            else:
                json_str = raw_text

            signal_data = json.loads(json_str)
            recommendation = signal_data.get("recommendation", "N/A")
            final_score = signal_data.get("final_score")
            confidence = signal_data.get("confidence")

            scores = signal_data.get("scores", {})
            tech_score = scores.get("technical")
            fund_score = scores.get("fundamental")
            sent_score = scores.get("sentiment")
        except (json.JSONDecodeError, ValueError):
            pass

    # Check for token usage
    token_info = data.get("token_usage", {})
    if token_info:
        token_usage = token_info.get("total_tokens", 0)

    # Check for fallback modes in synthesis input or other files
    used_fallback = data.get("used_fallback", False)

    return {
        "timestamp": timestamp,
        "ticker": ticker,
        "status": status,
        "recommendation": recommendation,
        "final_score": final_score,
        "confidence": confidence,
        "tech_score": tech_score,
        "fund_score": fund_score,
        "sent_score": sent_score,
        "token_usage": token_usage,
        "fallback_mode": used_fallback or fallback_mode,
        "file_path": file_path,
    }


def find_synthesis_files(path: Path) -> list[Path]:
    """Find all synthesis output files in a given path.

    Args:
        path: Either a directory or a specific debug run directory

    Returns:
        List of synthesis output file paths
    """
    files = []

    if path.is_dir():
        # Check if this is a debug run directory (contains *_synthesis_output_*.json)
        run_files = list(path.glob("*_synthesis_output_*.json"))
        if run_files:
            # This is a single run directory
            files.extend(run_files)
        else:
            # This is a parent directory, search subdirectories
            for subdir in path.iterdir():
                if subdir.is_dir():
                    run_files = list(subdir.glob("*_synthesis_output_*.json"))
                    files.extend(run_files)
    elif path.is_file():
        if path.name.endswith("_synthesis_output_*.json") or "_synthesis_output_" in path.name:
            files.append(path)

    return sorted(files, key=lambda x: x.parent.name)


def format_score(score: Optional[float]) -> str:
    """Format a score for display."""
    if score is None:
        return "N/A"
    return f"{int(score)}"


def format_recommendation(rec: Optional[str]) -> str:
    """Format recommendation with color coding."""
    if rec is None:
        return "[red]N/A[/red]"

    rec_lower = rec.lower()
    if "buy" in rec_lower or "strong" in rec_lower:
        return f"[green]{rec}[/green]"
    elif "sell" in rec_lower:
        return f"[red]{rec}[/red]"
    else:
        return f"[yellow]{rec}[/yellow]"


def check_data_completeness(run: dict) -> str:
    """Check if all required data fields are present.

    Returns ✓ if all critical fields are present, ❌ if any are missing.
    """
    # Check critical fields
    if run["recommendation"] is None:
        return "[red]❌[/red]"
    if run["final_score"] is None:
        return "[red]❌[/red]"
    if run["confidence"] is None:
        return "[red]❌[/red]"

    # Check component scores
    if run["tech_score"] is None or run["fund_score"] is None or run["sent_score"] is None:
        return "[red]❌[/red]"

    return "[green]✓[/green]"


@app.command()
def main(
    path: str = typer.Argument(
        "data/llm_debug",
        help="Path to debug logs directory or single debug run directory",
    ),
) -> None:
    """Analyze LLM agent execution from debug logs.

    Examples:
        # Analyze all runs in debug directory
        python scripts/verify_agent_execution.py data/llm_debug

        # Analyze a single run
        python scripts/verify_agent_execution.py data/llm_debug/20251202_163634
    """

    # Convert to Path object
    log_path = Path(path).resolve()

    # Validate path exists
    if not log_path.exists():
        console.print(f"[red]Error: Path does not exist: {path}[/red]")
        raise typer.Exit(code=1)

    # Find synthesis files
    synthesis_files = find_synthesis_files(log_path)

    if not synthesis_files:
        console.print(f"[yellow]No synthesis output files found in {path}[/yellow]")
        raise typer.Exit(code=0)

    # Parse all files
    console.print(f"[blue]Analyzing {len(synthesis_files)} debug run(s)...[/blue]")
    runs = []

    for file_path in synthesis_files:
        result = parse_synthesis_output(file_path)
        if result:
            runs.append(result)

    if not runs:
        console.print("[red]No valid synthesis outputs could be parsed[/red]")
        raise typer.Exit(code=1)

    # Create and display table
    table = Table(
        title=f"Agent Execution Analysis ({len(runs)} run{'s' if len(runs) != 1 else ''})"
    )

    table.add_column("Run Timestamp", style="cyan")
    table.add_column("Ticker", style="magenta")
    table.add_column("Status", style="cyan")
    table.add_column("Recommendation", style="white")
    table.add_column("Score", justify="center")
    table.add_column("Confidence", justify="center")
    table.add_column("Tech|Fund|Sent", justify="center")
    table.add_column("Fallback", justify="center")
    table.add_column("Complete", justify="center")

    for run in runs:
        # Check data completeness
        completeness = check_data_completeness(run)

        # Combine scores display
        scores_str = (
            f"{format_score(run['tech_score'])}|"
            f"{format_score(run['fund_score'])}|"
            f"{format_score(run['sent_score'])}"
        )

        # Format fallback indicator
        fallback_indicator = "[red]Yes[/red]" if run["fallback_mode"] else "[green]No[/green]"

        # Format recommendation with colors
        rec_display = format_recommendation(run["recommendation"])

        # Format score and confidence
        score_display = format_score(run["final_score"])
        confidence_display = format_score(run["confidence"])

        table.add_row(
            run["timestamp"] or "N/A",
            run["ticker"],
            "[green]✓[/green]" if run["status"] == "success" else "[red]✗[/red]",
            rec_display,
            score_display,
            confidence_display,
            scores_str,
            fallback_indicator,
            completeness,
        )

    console.print(table)

    # Print summary statistics
    if runs:
        console.print("\n[bold]Summary Statistics:[/bold]")

        complete = sum(
            1
            for r in runs
            if r["recommendation"] is not None
            and r["final_score"] is not None
            and r["confidence"] is not None
            and r["tech_score"] is not None
            and r["fund_score"] is not None
            and r["sent_score"] is not None
        )
        with_fallback = sum(1 for r in runs if r["fallback_mode"])

        console.print(f"  Total Runs: {len(runs)}")
        console.print(f"  Complete: {complete}/{len(runs)}")

        if with_fallback:
            console.print(f"  [yellow]With Fallback: {with_fallback}[/yellow]")


if __name__ == "__main__":
    app()
