"""Cache management CLI commands (greenfield Typer implementation).

Implements AC-4.5-4: Cache subcommands for status, clear, warm operations.

Migrated from brownfield Click implementation to Typer.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from data_extract.semantic.cache import CacheManager

cache_app = typer.Typer(help="Cache management commands")
console = Console()


@cache_app.command()
def status(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed cache information",
        ),
    ] = False,
) -> None:
    """Show cache status and statistics.

    Displays cache size, hit ratio, and entry information.

    Examples:
        data-extract cache status
        data-extract cache status -v
    """
    try:
        cache_manager = CacheManager()
        stats = cache_manager.get_stats()

        # Display status panel
        panel_content = (
            f"[bold]Cache Statistics[/bold]\n\n"
            f"Directory: {stats['cache_dir']}\n"
            f"Entries: {stats['num_entries']}\n"
            f"Size: {stats['total_size_mb']:.2f} MB / {stats['max_size_mb']} MB\n"
            f"Hit ratio: {stats['hit_ratio']:.1%}\n"
            f"Hits: {stats['cache_hits']}\n"
            f"Misses: {stats['cache_misses']}"
        )

        panel = Panel(
            panel_content,
            title="Cache Status",
            border_style="blue",
        )
        console.print(panel)

        # Show detailed info if verbose
        if verbose and stats["num_entries"] > 0:
            console.print()

            # List cache entries
            cache_dir = Path(stats["cache_dir"])
            if cache_dir.exists():
                table = Table(title="Cache Entries", show_header=True)
                table.add_column("Key", style="cyan")
                table.add_column("Size", style="green", justify="right")
                table.add_column("Modified", style="dim")

                for entry_file in sorted(cache_dir.glob("*.joblib"))[:20]:
                    if entry_file.name != "cache_index.joblib":
                        stat = entry_file.stat()
                        size_kb = stat.st_size / 1024
                        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                        table.add_row(
                            entry_file.stem,
                            f"{size_kb:.1f} KB",
                            modified,
                        )

                console.print(table)

                if stats["num_entries"] > 20:
                    console.print(f"\n[dim]Showing 20 of {stats['num_entries']} entries[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1)


@cache_app.command()
def clear(
    pattern: Optional[str] = typer.Option(
        None,
        "--pattern",
        "-p",
        help="Only clear entries matching pattern (e.g., 'tfidf_*')",
    ),
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Skip confirmation prompt",
        ),
    ] = False,
) -> None:
    """Clear cached entries.

    Remove all cached TF-IDF models, similarity matrices, and computed results.
    Use --pattern to selectively clear matching entries.

    Examples:
        data-extract cache clear
        data-extract cache clear --pattern "tfidf_*"
        data-extract cache clear -f
    """
    try:
        cache_manager = CacheManager()
        stats = cache_manager.get_stats()

        if stats["num_entries"] == 0:
            console.print("[yellow]Cache is already empty[/yellow]")
            return

        # Show what will be cleared
        if pattern:
            cache_dir = Path(stats["cache_dir"])
            matching_files = list(cache_dir.glob(f"{pattern}.joblib"))
            num_to_clear = len(matching_files)
            size_to_clear = sum(f.stat().st_size for f in matching_files) / (1024 * 1024)
            console.print(
                f"Found {num_to_clear} entries matching '{pattern}' ({size_to_clear:.2f} MB)"
            )
        else:
            num_to_clear = stats["num_entries"]
            size_to_clear = stats["total_size_mb"]
            console.print(f"Will clear {num_to_clear} entries ({size_to_clear:.2f} MB)")

        # Confirm
        if not force:
            confirmed = typer.confirm("Are you sure you want to clear the cache?")
            if not confirmed:
                console.print("[yellow]Cancelled[/yellow]")
                return

        # Clear cache
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Clearing cache...", total=None)

            if pattern:
                # Selective clear
                cache_dir = Path(stats["cache_dir"])
                for entry_file in cache_dir.glob(f"{pattern}.joblib"):
                    entry_file.unlink()
                progress.update(task, description="[green]Selective clear complete")
            else:
                # Full clear
                cache_manager.clear()
                progress.update(task, description="[green]Cache cleared")

        console.print(f"[green]Cleared {num_to_clear} cache entries[/green]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1)


@cache_app.command()
def warm(
    input_path: Path = typer.Argument(
        ...,
        exists=True,
        help="Directory containing JSON chunk files",
    ),
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed progress",
        ),
    ] = False,
) -> None:
    """Pre-compute and cache results for a corpus.

    Warm the cache by pre-computing TF-IDF vectors and other
    semantic analysis results for the given input files.

    Examples:
        data-extract cache warm ./chunks/
        data-extract cache warm ./chunks/ -v
    """
    try:
        # Import helper from greenfield semantic commands
        from data_extract.cli.commands.semantic import _load_chunks
        from data_extract.semantic.similarity import SimilarityAnalysisStage
        from data_extract.semantic.tfidf import TfidfVectorizationStage

        # Load chunks
        chunks = _load_chunks(input_path, verbose)
        if not chunks:
            console.print("[red]Error:[/red] No valid chunks found in input path")
            raise typer.Exit(code=1)

        console.print(f"[blue]Warming cache for {len(chunks)} chunks...[/blue]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # TF-IDF warming
            task1 = progress.add_task("[cyan]Computing TF-IDF vectors...", total=None)
            tfidf_stage = TfidfVectorizationStage()
            tfidf_result = tfidf_stage.process(chunks, None)
            progress.update(task1, description="[green]✓ TF-IDF cached")

            # Similarity warming
            task2 = progress.add_task("[cyan]Computing similarity matrix...", total=None)
            similarity_stage = SimilarityAnalysisStage()
            similarity_stage.process(tfidf_result, None)
            progress.update(task2, description="[green]✓ Similarity cached")

        # Show cache status
        cache_manager = CacheManager()
        stats = cache_manager.get_stats()

        console.print()
        panel = Panel(
            f"[bold]Cache Warming Complete[/bold]\n\n"
            f"Chunks processed: {len(chunks)}\n"
            f"Cache entries: {stats['num_entries']}\n"
            f"Cache size: {stats['total_size_mb']:.2f} MB",
            title="Warm Complete",
            border_style="green",
        )
        console.print(panel)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1)


@cache_app.command()
def metrics(
    output_format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format (json or text)",
            case_sensitive=False,
        ),
    ] = "text",
) -> None:
    """Show cache performance metrics.

    Display detailed cache performance statistics including
    hit ratio, timing, and efficiency metrics.

    Examples:
        data-extract cache metrics
        data-extract cache metrics -f json
    """
    try:
        # Validate format
        if output_format not in ["json", "text"]:
            console.print(
                f"[red]Error:[/red] Invalid format '{output_format}'. Use 'json' or 'text'"
            )
            raise typer.Exit(code=1)

        cache_manager = CacheManager()
        stats = cache_manager.get_stats()

        # Calculate additional metrics
        total_requests = stats["cache_hits"] + stats["cache_misses"]
        efficiency = stats["hit_ratio"] * 100 if total_requests > 0 else 0

        metrics_data = {
            "cache_directory": stats["cache_dir"],
            "entries": stats["num_entries"],
            "size_mb": round(stats["total_size_mb"], 2),
            "max_size_mb": stats["max_size_mb"],
            "utilization_pct": round((stats["total_size_mb"] / stats["max_size_mb"]) * 100, 1),
            "hits": stats["cache_hits"],
            "misses": stats["cache_misses"],
            "total_requests": total_requests,
            "hit_ratio": round(stats["hit_ratio"], 4),
            "efficiency_pct": round(efficiency, 1),
        }

        if output_format == "json":
            console.print(json.dumps(metrics_data, indent=2))
        else:
            # Text format with table
            table = Table(title="Cache Performance Metrics", show_header=True)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green", justify="right")

            table.add_row("Cache Directory", stats["cache_dir"])
            table.add_row("Total Entries", str(stats["num_entries"]))
            table.add_row("Size", f"{stats['total_size_mb']:.2f} MB")
            table.add_row("Max Size", f"{stats['max_size_mb']} MB")
            table.add_row("Utilization", f"{metrics_data['utilization_pct']:.1f}%")
            table.add_row("───", "───")
            table.add_row("Cache Hits", str(stats["cache_hits"]))
            table.add_row("Cache Misses", str(stats["cache_misses"]))
            table.add_row("Total Requests", str(total_requests))
            table.add_row("Hit Ratio", f"{stats['hit_ratio']:.1%}")
            table.add_row("Efficiency", f"{efficiency:.1f}%")

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1)
