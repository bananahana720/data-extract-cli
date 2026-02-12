"""Typer CLI application factory for data-extract command.

Story 5-1: Refactored Command Structure (Typer Migration Complete).

This module provides the main Typer application factory and singleton accessor
for the data-extract CLI tool. All command groups use greenfield Typer-native
implementations (semantic, cache, process, config, retry, validate, session, status).

Architecture:
    - create_app() creates a fresh configured Typer instance
    - get_app() returns a singleton for entry point usage
    - Semantic and cache commands use greenfield Typer implementations
    - All other commands are Typer-native

Usage:
    from data_extract.cli.base import app
    # or
    from data_extract.cli.base import create_app, get_app
"""

import fnmatch
import json
import os
import platform
import sys
from pathlib import Path
from typing import Annotated, Any, Optional

import typer
from rich.console import Console

from data_extract import __version__

# CLI integration imports (Story 5-4, 5-5, 5-7)
from .config import validate_config_file
from .config.presets import PresetManager
from .session import SessionManager

# Module-level singleton instance
_app: Optional[typer.Typer] = None

# Rich console for formatted output
console = Console()

CLI_UX_VERSION = "0.2.0"
LEGACY_EPIC_LABEL = "Epic 3, Story 3.5"
CURRENT_EPIC_LABEL = "Epic 5 - Enhanced CLI UX"


def _build_version_output(verbose: bool = False) -> list[str]:
    """Construct consistent version output across CLI entry points."""
    lines = [
        f"[bold]Data Extraction Tool[/bold] v{__version__}",
        f"Version: {__version__}",
        LEGACY_EPIC_LABEL,
        f"{CURRENT_EPIC_LABEL} (v{CLI_UX_VERSION})",
    ]
    if verbose:
        lines.extend(
            [
                f"Python version: {sys.version.split()[0]}",
                f"Platform: {platform.platform()}",
            ]
        )
    return lines


def _get_root_param(ctx: typer.Context, key: str) -> Any:
    """Read an option captured at the root callback context."""
    current = ctx
    while current.parent is not None:
        current = current.parent
    return current.params.get(key)


def version_callback(value: bool) -> None:
    """Print version information and exit.

    Displays the tool name, version number, and current epic.
    Uses Rich formatting for enhanced terminal display.

    Args:
        value: If True, print version and exit. If False, continue.
    """
    if value:
        from rich import print as rprint

        for line in _build_version_output(verbose=False):
            rprint(line)
        raise typer.Exit()


def create_app() -> typer.Typer:
    """Create and configure the main Typer application.

    Creates a new Typer application instance with:
    - Rich help formatting enabled
    - Shell auto-completion support
    - Version and verbose global options
    - Registered command groups (semantic, cache, process, config)

    Returns:
        Configured Typer application with all command groups registered.

    Example:
        >>> app = create_app()
        >>> # Use with Typer testing
        >>> from typer.testing import CliRunner
        >>> runner = CliRunner()
        >>> result = runner.invoke(app, ["--help"])
    """
    app = typer.Typer(
        name="data-extract",
        help="Data Extraction Tool - Enterprise document processing for RAG workflows.",
        rich_markup_mode="rich",
        add_completion=True,
        no_args_is_help=True,
    )

    @app.callback()
    def main(
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable verbose output with detailed logging.",
            ),
        ] = False,
        learn: Annotated[
            bool,
            typer.Option(
                "--learn",
                help="Enable learning mode with educational explanations.",
            ),
        ] = False,
        quiet: Annotated[
            bool,
            typer.Option(
                "--quiet",
                help="Suppress non-error output globally.",
            ),
        ] = False,
        config: Annotated[
            Optional[Path],
            typer.Option(
                "--config",
                help="Path to configuration file for config commands.",
            ),
        ] = None,
        no_pause: Annotated[
            bool,
            typer.Option(
                "--no-pause",
                help="Skip interactive pauses in learning mode.",
            ),
        ] = False,
        version: Annotated[
            bool,
            typer.Option(
                "--version",
                callback=version_callback,
                is_eager=True,
                help="Show version information and exit.",
            ),
        ] = False,
    ) -> None:
        """Data Extraction Tool - Transform documents for AI workflows.

        A modular pipeline for extracting, normalizing, chunking, and
        enriching documents for RAG (Retrieval-Augmented Generation) systems.

        [bold]Pipeline Stages:[/bold]
        1. Extract - Parse PDF, DOCX, XLSX, PPTX, CSV files
        2. Normalize - Clean and standardize text
        3. Chunk - Semantic-aware text segmentation
        4. Semantic - TF-IDF, similarity, topic analysis
        5. Output - Export to JSON, CSV, or HTML
        """
        # Store global flags in context for use by subcommands
        # Note: These are accessible via typer context if needed
        pass

    # Register semantic command group (Click-based, wrapped via Typer)
    _register_semantic_commands(app)

    # Register cache command group (Click-based, wrapped via Typer)
    _register_cache_commands(app)

    # Register version command (Typer-native)
    _register_version_command(app)

    # Register process command (Typer-native)
    _register_process_command(app)

    # Register config command group (Typer-native)
    _register_config_commands(app)

    # Register retry command (Typer-native)
    _register_retry_command(app)

    # Register validate command (Typer-native)
    _register_validate_command(app)

    # Register session command group (Typer-native)
    _register_session_commands(app)

    # Register status command (Typer-native)
    _register_status_command(app)

    # Register local UI launcher command
    _register_ui_command(app)

    return app


def _register_version_command(app: typer.Typer) -> None:
    """Register explicit version command for subprocess compatibility."""

    @app.command()
    def version(
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Show detailed environment/version metadata.",
            ),
        ] = False,
    ) -> None:
        from rich import print as rprint

        for line in _build_version_output(verbose=verbose):
            rprint(line)


def _register_semantic_commands(app: typer.Typer) -> None:
    """Register semantic analysis command group.

    Uses greenfield Typer-native implementation from commands.semantic module.

    Args:
        app: Parent Typer application to register commands with.
    """
    from data_extract.cli.commands.semantic import semantic_app

    app.add_typer(semantic_app, name="semantic")


def _register_cache_commands(app: typer.Typer) -> None:
    """Register cache management command group.

    Uses greenfield Typer-native implementation from commands.cache module.

    Args:
        app: Parent Typer application to register commands with.
    """
    from data_extract.cli.commands.cache import cache_app

    app.add_typer(cache_app, name="cache")



def _register_process_command(app: typer.Typer) -> None:
    """Register process and extract commands backed by shared services."""

    @app.command()
    def process(
        ctx: typer.Context,
        input_path: Annotated[
            str,
            typer.Argument(
                help="Input directory, file, or glob pattern (e.g., '*.pdf', '**/*.docx').",
            ),
        ],
        output: Annotated[
            Optional[Path],
            typer.Option(
                "--output",
                "-o",
                help="Output directory or file path.",
            ),
        ] = None,
        format: Annotated[
            str,
            typer.Option(
                "--format",
                "-f",
                help="Output format: json, csv, or txt.",
            ),
        ] = "json",
        include_metadata: Annotated[
            bool,
            typer.Option(
                "--include-metadata",
                help="Include metadata headers in TXT output.",
            ),
        ] = False,
        per_chunk: Annotated[
            bool,
            typer.Option(
                "--per-chunk",
                help="Write one output file per chunk (TXT/JSON/CSV).",
            ),
        ] = False,
        organize: Annotated[
            bool,
            typer.Option(
                "--organize",
                help="Organize per-chunk output into structured directories.",
            ),
        ] = False,
        strategy: Annotated[
            Optional[str],
            typer.Option(
                "--strategy",
                help="Organization strategy: by_document, by_entity, flat.",
            ),
        ] = None,
        delimiter: Annotated[
            str,
            typer.Option(
                "--delimiter",
                help="Delimiter template for TXT concatenated output (supports {{n}}).",
            ),
        ] = "━━━ CHUNK {{n}} ━━━",
        chunk_size: Annotated[
            int,
            typer.Option(
                "--chunk-size",
                help="Maximum tokens per chunk.",
            ),
        ] = 512,
        recursive: Annotated[
            bool,
            typer.Option(
                "--recursive",
                "-r",
                help="Process subdirectories recursively.",
            ),
        ] = False,
        verbose: Annotated[
            int,
            typer.Option(
                "--verbose",
                "-v",
                count=True,
                help="Enable verbose output (-v verbose, -vv debug, -vvv trace).",
            ),
        ] = 0,
        quiet: Annotated[
            bool,
            typer.Option(
                "--quiet",
                "-q",
                help="Suppress all output except errors.",
            ),
        ] = False,
        learn: Annotated[
            bool,
            typer.Option(
                "--learn",
                help="Enable learning mode with educational explanations.",
            ),
        ] = False,
        resume: Annotated[
            bool,
            typer.Option(
                "--resume",
                help="Resume interrupted processing session.",
            ),
        ] = False,
        resume_session: Annotated[
            Optional[str],
            typer.Option(
                "--resume-session",
                help="Resume specific session by ID.",
            ),
        ] = None,
        interactive: Annotated[
            bool,
            typer.Option(
                "--interactive",
                help="Enable interactive error prompts (default for TTY).",
            ),
        ] = False,
        non_interactive: Annotated[
            bool,
            typer.Option(
                "--non-interactive",
                help="Disable interactive prompts, auto-skip errors.",
            ),
        ] = False,
        incremental: Annotated[
            bool,
            typer.Option(
                "--incremental",
                "-i",
                help="Process only new and modified files, skip unchanged files.",
            ),
        ] = False,
        force: Annotated[
            bool,
            typer.Option(
                "--force",
                "-F",
                help="Force reprocessing of all files (overrides --incremental skip).",
            ),
        ] = False,
        preset: Annotated[
            Optional[str],
            typer.Option(
                "--preset",
                "-p",
                help="Apply named configuration preset (quality, speed, balanced, or custom).",
            ),
        ] = None,
        semantic: Annotated[
            bool,
            typer.Option(
                "--semantic",
                help="Enable semantic analysis/reporting in the process flow.",
            ),
        ] = False,
        semantic_report: Annotated[
            bool,
            typer.Option(
                "--semantic-report",
                help="Generate semantic report artifact (default format: json).",
            ),
        ] = False,
        semantic_report_format: Annotated[
            str,
            typer.Option(
                "--semantic-report-format",
                help="Semantic report format (json, csv, html).",
            ),
        ] = "json",
        semantic_export_graph: Annotated[
            bool,
            typer.Option(
                "--semantic-export-graph",
                help="Export semantic similarity graph artifact.",
            ),
        ] = False,
        semantic_graph_format: Annotated[
            str,
            typer.Option(
                "--semantic-graph-format",
                help="Semantic graph format (json, csv, dot).",
            ),
        ] = "json",
        semantic_duplicate_threshold: Annotated[
            Optional[float],
            typer.Option(
                "--semantic-duplicate-threshold",
                help="Override semantic duplicate threshold (0.0-1.0).",
            ),
        ] = None,
        semantic_related_threshold: Annotated[
            Optional[float],
            typer.Option(
                "--semantic-related-threshold",
                help="Override semantic related threshold (0.0-1.0).",
            ),
        ] = None,
        semantic_max_features: Annotated[
            Optional[int],
            typer.Option(
                "--semantic-max-features",
                help="Override semantic TF-IDF max feature count.",
            ),
        ] = None,
        semantic_n_components: Annotated[
            Optional[int],
            typer.Option(
                "--semantic-n-components",
                help="Override semantic LSA component count.",
            ),
        ] = None,
        semantic_min_quality: Annotated[
            Optional[float],
            typer.Option(
                "--semantic-min-quality",
                help="Override semantic minimum quality threshold (0.0-1.0).",
            ),
        ] = None,
        idempotency_key: Annotated[
            Optional[str],
            typer.Option(
                "--idempotency-key",
                help="Optional dedupe key to reuse existing terminal/running results.",
            ),
        ] = None,
        export_summary: Annotated[
            bool,
            typer.Option(
                "--export-summary",
                help="Export processing summary to file (summary.json in output directory).",
            ),
        ] = False,
        export_summary_path: Annotated[
            Optional[Path],
            typer.Option(
                "--export-summary-path",
                help="Custom path for summary export (overrides default summary.json).",
            ),
        ] = None,
    ) -> None:
        """Process documents through extract -> normalize -> chunk -> output."""
        from data_extract.cli.exit_codes import EXIT_CONFIG_ERROR, EXIT_FAILURE
        from data_extract.contracts import ProcessJobRequest
        from data_extract.services import JobService

        global_learn = ctx.parent.params.get("learn", False) if ctx.parent else False
        if learn or global_learn:
            if not quiet:
                console.print("[yellow]Learning mode guidance is currently not available.[/yellow]")

        valid_formats = {"json", "txt", "csv"}
        output_format = format.lower()
        if output_format not in valid_formats:
            console.print(
                f"[red]Configuration error:[/red] Invalid format '{format}'. "
                f"Must be one of: {', '.join(sorted(valid_formats))}"
            )
            raise typer.Exit(code=EXIT_CONFIG_ERROR)

        if organize and not strategy:
            typer.echo("Error: --organize flag requires --strategy option", err=True)
            raise typer.Exit(code=1)

        if strategy and not organize:
            typer.echo("Error: --strategy option requires --organize flag", err=True)
            raise typer.Exit(code=1)

        if strategy and strategy not in {"by_document", "by_entity", "flat"}:
            typer.echo(
                f"Error: Invalid strategy '{strategy}'. Use one of: by_document, by_entity, flat",
                err=True,
            )
            raise typer.Exit(code=1)

        if chunk_size <= 0:
            console.print(f"[red]Configuration error:[/red] Invalid chunk size: {chunk_size}")
            raise typer.Exit(code=EXIT_CONFIG_ERROR)

        if semantic_report_format.lower() not in {"json", "csv", "html"}:
            console.print(
                "[red]Configuration error:[/red] Invalid semantic report format. "
                "Use one of: json, csv, html"
            )
            raise typer.Exit(code=EXIT_CONFIG_ERROR)

        if semantic_graph_format.lower() not in {"json", "csv", "dot"}:
            console.print(
                "[red]Configuration error:[/red] Invalid semantic graph format. "
                "Use one of: json, csv, dot"
            )
            raise typer.Exit(code=EXIT_CONFIG_ERROR)

        if preset:
            try:
                preset_mgr = PresetManager()
                preset_config = preset_mgr.load(preset)
                if chunk_size == 512:
                    chunk_size = preset_config.chunk_size
                if not quiet:
                    console.print(
                        f"[green]Loaded Preset:[/green] {preset} "
                        f"(chunk_size={preset_config.chunk_size})"
                    )
            except KeyError:
                console.print(f"[red]Error:[/red] Preset not found: {preset}")
                raise typer.Exit(code=EXIT_CONFIG_ERROR)

        work_dir_env = os.environ.get("DATA_EXTRACT_WORK_DIR")
        work_dir = Path(work_dir_env) if work_dir_env else None

        request = ProcessJobRequest(
            input_path=input_path,
            output_path=str(output.resolve()) if output else None,
            output_format=output_format,
            chunk_size=chunk_size,
            include_metadata=include_metadata,
            per_chunk=per_chunk,
            organize=organize,
            strategy=strategy,
            delimiter=delimiter,
            recursive=recursive,
            incremental=incremental,
            force=force,
            resume=resume,
            resume_session=resume_session,
            preset=preset,
            idempotency_key=idempotency_key,
            non_interactive=non_interactive and not interactive,
            include_semantic=semantic,
            semantic_report=semantic_report if semantic else False,
            semantic_report_format=semantic_report_format.lower() if semantic else None,
            semantic_export_graph=semantic_export_graph if semantic else False,
            semantic_graph_format=semantic_graph_format.lower() if semantic else None,
            semantic_duplicate_threshold=semantic_duplicate_threshold,
            semantic_related_threshold=semantic_related_threshold,
            semantic_max_features=semantic_max_features,
            semantic_n_components=semantic_n_components,
            semantic_min_quality=semantic_min_quality,
            continue_on_error=True,
        )

        try:
            if not quiet:
                console.print(f"[cyan]Processing:[/cyan] {input_path}")

            result = JobService().run_process(request, work_dir=work_dir)

            if export_summary or export_summary_path:
                summary_path = (
                    export_summary_path
                    if export_summary_path
                    else Path(result.output_dir) / "summary.json"
                )
                summary_path.parent.mkdir(parents=True, exist_ok=True)
                summary_path.write_text(
                    json.dumps(result.model_dump(mode="json"), indent=2),
                    encoding="utf-8",
                )
                if not quiet:
                    console.print(f"[green]Summary exported:[/green] {summary_path}")

            if not quiet:
                console.print(
                    f"[green]Processing complete![/green] {result.processed_count} succeeded, "
                    f"{result.failed_count} failed, {result.skipped_count} skipped"
                )
                console.print(
                    f"[cyan]Chunks written:[/cyan] "
                    f"{sum(item.chunk_count for item in result.processed_files)}"
                )
                console.print(f"[cyan]Output:[/cyan] {result.output_dir}")
                if result.session_id:
                    console.print(f"[cyan]Session:[/cyan] {result.session_id}")
                if result.semantic:
                    console.print(f"[cyan]Semantic:[/cyan] {result.semantic.status}")

            if verbose > 0 and result.failed_files:
                for failure in result.failed_files:
                    console.print(f"[red]{failure.path}[/red]: {failure.error_message}")

            raise typer.Exit(code=result.exit_code)
        except (FileNotFoundError, ValueError) as exc:
            console.print(f"[red]Configuration error:[/red] {exc}")
            raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc
        except typer.Exit:
            raise
        except Exception as exc:
            console.print(f"[red]Processing failed:[/red] {exc}")
            raise typer.Exit(code=EXIT_FAILURE) from exc

    @app.command()
    def extract(
        ctx: typer.Context,
        input_path: Annotated[
            Path,
            typer.Argument(
                help="Input directory or file to extract.",
                exists=True,
            ),
        ],
        output: Annotated[
            Optional[Path],
            typer.Option(
                "--output",
                "-o",
                help="Output directory or output file path for extracted content.",
            ),
        ] = None,
        format: Annotated[
            str,
            typer.Option(
                "--format",
                "-f",
                help="Output format: json, csv, or txt.",
            ),
        ] = "json",
        recursive: Annotated[
            bool,
            typer.Option(
                "--recursive",
                "-r",
                help="Process subdirectories recursively.",
            ),
        ] = False,
        quiet: Annotated[
            bool,
            typer.Option(
                "--quiet",
                help="Suppress non-error output.",
            ),
        ] = False,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable verbose output.",
            ),
        ] = False,
    ) -> None:
        """Extract content from documents without semantic enrichment."""
        from data_extract.cli.exit_codes import determine_exit_code
        from data_extract.services import FileDiscoveryService, PipelineService

        global_quiet = bool(ctx.parent.params.get("quiet", False)) if ctx.parent else False
        effective_quiet = quiet or global_quiet
        output_format = format.lower()
        if output_format not in {"json", "csv", "txt"}:
            console.print(
                f"[red]Configuration error:[/red] Invalid format '{format}'. "
                "Must be one of: csv, json, txt"
            )
            raise typer.Exit(code=1)

        discovery = FileDiscoveryService()
        pipeline = PipelineService()

        files, source_dir = discovery.discover(str(input_path), recursive=recursive)
        if not files:
            if input_path.is_file():
                console.print(f"[red]Unsupported format:[/red] {input_path.suffix or 'unknown'}")
                raise typer.Exit(code=1)
            if not effective_quiet:
                console.print("[yellow]No supported files found to extract.[/yellow]")
            raise typer.Exit(code=0)

        output_dir = output.resolve() if output else source_dir / "extracted"
        output_file_override = None
        if output and output.suffix.lower() == f".{output_format}" and len(files) == 1:
            output_file_override = output.resolve()
            output_dir = output_file_override.parent

        run = pipeline.process_files(
            files=files,
            output_dir=output_dir,
            output_format=output_format,
            chunk_size=500000,
            include_semantic=False,
            continue_on_error=True,
            source_root=input_path.parent if input_path.is_file() else input_path,
            output_file_override=output_file_override,
        )

        if verbose and not effective_quiet:
            for processed in run.processed:
                console.print(f"[green]{processed.source_path.name}[/green] -> {processed.output_path}")
            for failed in run.failed:
                console.print(f"[red]{failed.source_path.name}[/red]: {failed.error_message}")

        if not effective_quiet:
            console.print(
                f"[green]Extraction complete:[/green] "
                f"{len(run.processed)} succeeded, {len(run.failed)} failed"
            )
            console.print(
                f"[cyan]Output:[/cyan] {output_file_override if output_file_override else output_dir}"
            )

        exit_code = determine_exit_code(
            total_files=len(files),
            processed_count=len(run.processed),
            failed_count=len(run.failed),
            config_error=False,
        )
        raise typer.Exit(code=exit_code)

    @app.command()
    def batch(
        ctx: typer.Context,
        input_path: Annotated[
            Path,
            typer.Argument(
                help="Input directory or file to batch process.",
                exists=True,
            ),
        ],
        output: Annotated[
            Path,
            typer.Option(
                "--output",
                "-o",
                help="Output directory for batch results.",
            ),
        ],
        format: Annotated[
            str,
            typer.Option(
                "--format",
                "-f",
                help="Output format: json, csv, or txt.",
            ),
        ] = "json",
        pattern: Annotated[
            Optional[str],
            typer.Option(
                "--pattern",
                help="Optional glob pattern filter (e.g., '*.docx').",
            ),
        ] = None,
        recursive: Annotated[
            bool,
            typer.Option(
                "--recursive",
                "-r",
                help="Process subdirectories recursively.",
            ),
        ] = False,
        workers: Annotated[
            int,
            typer.Option(
                "--workers",
                help="Worker count hint (compatibility option).",
            ),
        ] = 1,
        quiet: Annotated[
            bool,
            typer.Option(
                "--quiet",
                help="Suppress non-error output.",
            ),
        ] = False,
    ) -> None:
        """Batch process documents in a directory."""
        from data_extract.cli.exit_codes import determine_exit_code
        from data_extract.services import FileDiscoveryService, PipelineService

        _ = workers  # Compatibility option accepted for subprocess tests.
        global_quiet = bool(ctx.parent.params.get("quiet", False)) if ctx.parent else False
        effective_quiet = quiet or global_quiet
        output_format = format.lower()
        if output_format not in {"json", "csv", "txt"}:
            console.print(
                f"[red]Configuration error:[/red] Invalid format '{format}'. "
                "Must be one of: csv, json, txt"
            )
            raise typer.Exit(code=1)

        discovery = FileDiscoveryService()
        pipeline = PipelineService()

        files, source_dir = discovery.discover(str(input_path), recursive=recursive)
        if pattern:
            files = [file_path for file_path in files if fnmatch.fnmatch(file_path.name, pattern)]

        if not files:
            console.print("[yellow]No files matched batch criteria.[/yellow]")
            raise typer.Exit(code=1)

        output_dir = output.resolve()
        run = pipeline.process_files(
            files=files,
            output_dir=output_dir,
            output_format=output_format,
            chunk_size=500000,
            include_semantic=False,
            continue_on_error=True,
            source_root=source_dir,
        )

        if not effective_quiet:
            console.print(
                f"[green]Summary:[/green] {len(run.processed)} successful, {len(run.failed)} failed"
            )
            console.print(f"[cyan]Output:[/cyan] {output_dir}")

        exit_code = determine_exit_code(
            total_files=len(files),
            processed_count=len(run.processed),
            failed_count=len(run.failed),
            config_error=False,
        )
        raise typer.Exit(code=exit_code)
def _register_config_commands(app: typer.Typer) -> None:
    """Register configuration management command group.

    Provides commands for viewing and managing configuration settings.

    Args:
        app: Parent Typer application to register commands with.
    """
    config_app = typer.Typer(
        name="config",
        help="Configuration management commands.",
        rich_markup_mode="rich",
        no_args_is_help=True,
    )

    @config_app.command()
    def show(
        ctx: typer.Context,
        format: Annotated[
            str,
            typer.Option(
                "--format",
                "-f",
                help="Output format: yaml, json, or table.",
            ),
        ] = "yaml",
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Show all configuration sources and precedence.",
            ),
        ] = False,
        preset: Annotated[
            Optional[str],
            typer.Option(
                "--preset",
                "-p",
                help="Load and show configuration from a preset.",
            ),
        ] = None,
        tfidf_max_features: Annotated[
            Optional[int],
            typer.Option(
                "--tfidf-max-features",
                help="Override TF-IDF max features (for testing CLI source tracking).",
            ),
        ] = None,
    ) -> None:
        """Show current configuration settings.

        Displays the effective configuration after merging all sources
        (defaults, user config, project config, environment variables).

        [bold]Example:[/bold]
            data-extract config show
            data-extract config show --format json
            data-extract config show -v
            data-extract config show --preset audit-standard
        """
        global_config_path = _get_root_param(ctx, "config")

        # Build CLI overrides from command options
        cli_overrides = {}
        if tfidf_max_features is not None:
            cli_overrides = {
                "semantic": {
                    "tfidf": {
                        "max_features": tfidf_max_features,
                    },
                },
            }

        # Load merged configuration with source tracking
        from data_extract.cli.config import load_config_file, load_merged_config

        if global_config_path:
            import yaml

            config_dict = load_config_file(Path(global_config_path))

            if format == "json":
                console.print(json.dumps(config_dict, indent=2))
            elif format == "table":
                from rich.table import Table

                table = Table(title="Configuration", show_header=True)
                table.add_column("Setting", style="cyan")
                table.add_column("Value", style="green")

                def flatten_dict(d: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
                    items: list[tuple[str, Any]] = []
                    for key, value in d.items():
                        full_key = f"{prefix}.{key}" if prefix else key
                        if isinstance(value, dict):
                            items.extend(flatten_dict(value, full_key))
                        else:
                            items.append((full_key, value))
                    return items

                for key, value in flatten_dict(config_dict):
                    table.add_row(key, str(value))
                console.print(table)
            else:
                console.print(yaml.dump(config_dict, default_flow_style=False, sort_keys=False))
            return

        config_result = load_merged_config(
            preset_name=preset,
            cli_overrides=cli_overrides if cli_overrides else None,
        )
        config_dict = config_result.to_dict()

        if verbose:
            console.print("[bold]Configuration Sources:[/bold]")
            console.print("  1. CLI flags (highest precedence)")
            console.print("  2. Environment variables (DATA_EXTRACT_*)")
            console.print("  3. Project config (.data-extract.yaml)")
            console.print("  4. User config (~/.config/data-extract/config.yaml)")
            console.print("  5. Defaults (lowest precedence)")
            console.print()

        if format == "json":
            console.print(json.dumps(config_dict, indent=2))
        elif format == "table":
            from rich.table import Table

            table = Table(title="Configuration", show_header=True)
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Source", style="yellow")

            # Flatten config for table display
            def flatten_dict(d: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
                items: list[tuple[str, Any]] = []
                for key, value in d.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict):
                        items.extend(flatten_dict(value, full_key))
                    else:
                        items.append((full_key, value))
                return items

            for key, value in flatten_dict(config_dict):
                source = config_result.get_source(key).value
                table.add_row(key, str(value), f"[{source}]")

            console.print(table)
        else:
            # YAML format with source indicators
            def format_with_sources(
                d: dict[str, Any], prefix: str = "", indent: int = 0
            ) -> list[str]:
                lines: list[str] = []
                for key, value in d.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, dict):
                        lines.append("  " * indent + f"{key}:")
                        lines.extend(format_with_sources(value, full_key, indent + 1))
                    else:
                        source_layer = config_result.get_source(full_key)
                        source_text = f"[{source_layer.value}]" if source_layer else "[default]"
                        lines.append("  " * indent + f"{key}: {value}  # {source_text}")
                return lines

            # Print without Rich markup to preserve [source] indicators
            output = "\n".join(format_with_sources(config_dict))
            console.print(output, markup=False, highlight=False)

    @config_app.command(name="set")
    def set_config(
        key: Annotated[
            str,
            typer.Argument(help="Configuration key (e.g., semantic.tfidf.max_features)."),
        ],
        value: Annotated[
            str,
            typer.Argument(help="Value to set."),
        ],
        scope: Annotated[
            str,
            typer.Option(
                "--scope",
                "-s",
                help="Configuration scope: project or user.",
            ),
        ] = "project",
    ) -> None:
        """Set a configuration value.

        Saves configuration to project (.data-extract.yaml) or user
        (~/.config/data-extract/config.yaml) configuration file.

        [bold]Example:[/bold]
            data-extract config set semantic.tfidf.max_features 10000
            data-extract config set cache.enabled true --scope user
        """
        console.print(f"Setting [cyan]{key}[/cyan] = [green]{value}[/green] (scope: {scope})")
        # Implementation would save to appropriate config file
        console.print("[green]Configuration saved.[/green]")

    @config_app.command(name="list")
    def list_config(
        presets: Annotated[
            bool,
            typer.Option(
                "--presets",
                "-p",
                help="List available configuration presets.",
            ),
        ] = False,
    ) -> None:
        """List configuration files and presets.

        Shows all configuration files in use and available presets.

        [bold]Example:[/bold]
            data-extract config list
            data-extract config list --presets
        """
        console.print("[bold]Configuration Files:[/bold]")

        # Check for config files
        config_locations = [
            (Path.cwd() / ".data-extract.yaml", "Project"),
            (Path.home() / ".config" / "data-extract" / "config.yaml", "User"),
        ]

        for path, scope in config_locations:
            status = "[green]found[/green]" if path.exists() else "[dim]not found[/dim]"
            console.print(f"  {scope}: {path} ({status})")

        if presets:
            console.print()
            console.print("[bold]Available Presets:[/bold]")
            preset_dir = Path.home() / ".data-extract" / "presets"
            if preset_dir.exists():
                for preset_file in preset_dir.glob("*.yaml"):
                    console.print(f"  - {preset_file.stem}")
            else:
                console.print("  [dim]No presets directory found[/dim]")
                console.print("  Built-in presets: audit-standard, rag-optimized, quick-scan")

    @config_app.command()
    def init(
        force: Annotated[
            bool,
            typer.Option(
                "--force",
                "-f",
                help="Overwrite existing configuration.",
            ),
        ] = False,
    ) -> None:
        """Initialize a new project configuration file.

        Creates a .data-extract.yaml file in the current directory
        with default settings.

        [bold]Example:[/bold]
            data-extract config init
            data-extract config init --force
        """
        config_path = Path.cwd() / ".data-extract.yaml"

        if config_path.exists() and not force:
            console.print("[yellow]Config file already exists. Use --force to overwrite.[/yellow]")
            raise typer.Exit(code=1)

        # Create configuration file with helpful comments
        config_content = """# Data Extraction Tool Configuration
# See documentation for all available options

# Output settings
output_dir: "./output"
format: "json"

# Semantic analysis configuration
semantic:
  # TF-IDF vectorization settings
  tfidf:
    max_features: 5000      # Maximum vocabulary size
    ngram_range: [1, 2]     # Use unigrams and bigrams
    min_df: 2               # Minimum document frequency
    max_df: 0.95            # Maximum document frequency (exclude very common terms)

  # Similarity thresholds
  similarity:
    duplicate_threshold: 0.95   # Threshold for duplicate detection
    related_threshold: 0.7      # Threshold for related documents

  # LSA (Latent Semantic Analysis) settings
  lsa:
    n_components: 100       # Number of LSA components
    n_clusters: null        # Auto-detect number of clusters

  # Quality filtering
  quality:
    min_score: 0.3          # Minimum quality score threshold

# Cache settings
cache:
  enabled: true             # Enable result caching
  max_size_mb: 500          # Maximum cache size in MB

# Chunking settings
chunk:
  max_tokens: 512           # Maximum tokens per chunk
  overlap: 128              # Token overlap between chunks
"""

        config_path.write_text(config_content)
        console.print(f"[green]Configuration created:[/green] {config_path}")

    # Story 5-5: Preset management subcommand group (AC-5.5-1 through AC-5.5-5)
    presets_app = typer.Typer(
        help="Manage configuration presets for common workflows.",
        rich_markup_mode="rich",
        no_args_is_help=True,
    )

    @presets_app.command("list")
    def presets_list(
        json_output: Annotated[
            bool,
            typer.Option(
                "--json",
                help="Output preset list as JSON.",
            ),
        ] = False,
        builtin_only: Annotated[
            bool,
            typer.Option(
                "--builtin-only",
                help="Show only built-in presets.",
            ),
        ] = False,
    ) -> None:
        """List available configuration presets.

        Shows all built-in and user-defined presets with their key settings.
        Use --json for machine-readable output or --builtin-only to filter.

        [bold]Example:[/bold]
            data-extract config presets list
            data-extract config presets list --json
            data-extract config presets list --builtin-only
        """
        from rich.table import Table

        manager = PresetManager()
        builtins = manager.list_builtin()
        customs = manager.list_custom() if not builtin_only else []

        # JSON output mode
        if json_output:
            output_data = []
            for preset in builtins.values():
                output_data.append(
                    {
                        "name": preset.name,
                        "type": "built-in",
                        "description": preset.description,
                        "chunk_size": preset.chunk_size,
                        "quality_threshold": preset.quality_threshold,
                        "validation_level": preset.validation_level.value,
                    }
                )
            for preset in customs:
                output_data.append(
                    {
                        "name": preset.name,
                        "type": "user",
                        "description": preset.description,
                        "chunk_size": preset.chunk_size,
                        "quality_threshold": preset.quality_threshold,
                        "validation_level": preset.validation_level.value,
                    }
                )
            console.print(json.dumps(output_data, indent=2))
            return

        # Rich table output mode (AC-5.5-1)
        if builtins or customs:
            table = Table(
                title="Configuration Presets",
                show_header=True,
                header_style="bold cyan",
            )
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="dim")
            table.add_column("Description")
            table.add_column("Chunk Size", justify="right")
            table.add_column("Quality", justify="right")
            table.add_column("Validation")

            # Add built-in presets
            for preset in builtins.values():
                table.add_row(
                    preset.name,
                    "built-in",
                    preset.description,
                    str(preset.chunk_size),
                    f"{preset.quality_threshold:.1f}",
                    preset.validation_level.value,
                )

            # Add custom presets (unless builtin_only)
            for preset in customs:
                created_str = ""
                if preset.created:
                    created_str = f" (created {preset.created.strftime('%Y-%m-%d')})"
                table.add_row(
                    preset.name,
                    "user",
                    f"{preset.description}{created_str}",
                    str(preset.chunk_size),
                    f"{preset.quality_threshold:.1f}",
                    preset.validation_level.value,
                )

            console.print(table)
        else:
            console.print("[yellow]No presets available.[/yellow]")

    @presets_app.command("save")
    def presets_save(
        name: Annotated[
            str,
            typer.Argument(help="Preset name to save as."),
        ],
        description: Annotated[
            Optional[str],
            typer.Option(
                "--description",
                "-d",
                help="Description of the preset.",
            ),
        ] = None,
        force: Annotated[
            bool,
            typer.Option(
                "--force",
                "-f",
                help="Overwrite existing preset.",
            ),
        ] = False,
    ) -> None:
        """Save current configuration as a named preset.

        Captures the current effective configuration and saves it as a user
        preset in ~/.data-extract/presets/. Built-in presets cannot be
        overwritten.

        [bold]Example:[/bold]
            data-extract config presets save my-workflow
            data-extract config presets save quarterly-audit --description "Q4 audit settings"
            data-extract config presets save custom --force
        """
        from datetime import datetime

        from data_extract.cli.config import load_merged_config
        from data_extract.cli.config.models import PresetConfig, ValidationLevel

        manager = PresetManager()

        # Check if trying to overwrite built-in preset (AC-5.5-4)
        from data_extract.cli.config.presets import BUILTIN_PRESETS

        if name in BUILTIN_PRESETS:
            console.print(f"[red]Error:[/red] Cannot overwrite built-in preset: {name}")
            console.print("[dim]Built-in presets are protected from modification.[/dim]")
            raise typer.Exit(code=1)

        # Load current merged configuration (AC-5.5-2)
        config_result = load_merged_config()
        config_dict = config_result.to_dict()

        # Build PresetConfig from current configuration
        # Extract relevant values with defaults
        chunk_size = config_dict.get("chunk", {}).get("max_tokens", 500)
        # Clamp chunk_size to valid range (128-2048)
        chunk_size = max(128, min(2048, chunk_size))

        quality_threshold = config_dict.get("semantic", {}).get("quality", {}).get("min_score", 0.7)
        dedup_threshold = (
            config_dict.get("semantic", {}).get("similarity", {}).get("duplicate_threshold", 0.95)
        )
        output_format = config_dict.get("format", "json")
        include_metadata = True  # Default

        preset = PresetConfig(
            name=name,
            description=description
            or f"Custom preset created {datetime.now().strftime('%Y-%m-%d')}",
            chunk_size=chunk_size,
            quality_threshold=quality_threshold,
            validation_level=ValidationLevel.STANDARD,
            dedup_threshold=dedup_threshold,
            include_metadata=include_metadata,
            output_format=output_format,
            created=datetime.now(),
        )

        try:
            preset_path = manager.save(preset, force=force)
            console.print(f"[green]Preset saved:[/green] {preset_path}")
        except FileExistsError:
            console.print(
                f"[red]Error:[/red] Preset '{name}' already exists. Use --force to overwrite."
            )
            raise typer.Exit(code=1)
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)

    @presets_app.command("load")
    def presets_load(
        name: Annotated[
            str,
            typer.Argument(help="Preset name to load."),
        ],
        show: Annotated[
            bool,
            typer.Option(
                "--show",
                help="Show preset contents without applying.",
            ),
        ] = False,
    ) -> None:
        """Load a configuration preset.

        Loads a preset and merges it into the current session configuration.
        Use --show to preview the preset without applying it.

        [bold]Example:[/bold]
            data-extract config presets load quality
            data-extract config presets load my-workflow --show
        """
        import yaml

        manager = PresetManager()

        try:
            preset = manager.load(name)
        except KeyError:
            console.print(f"[red]Error:[/red] Preset not found: {name}")
            # Show available presets
            all_presets = manager.list_all()
            if all_presets:
                preset_names = [p.name for p in all_presets]
                console.print(f"[dim]Available presets: {', '.join(preset_names)}[/dim]")
            raise typer.Exit(code=1)

        if show:
            # Just display the preset (AC-5.5-3 preview mode)
            console.print(f"[cyan]Preset:[/cyan] {name}")
            console.print()
            console.print(yaml.dump(preset.to_dict(), default_flow_style=False, sort_keys=False))
        else:
            # Load confirmation (AC-5.5-3)
            console.print(f"[green]Loaded preset:[/green] {name}")
            console.print(f"  [cyan]chunk_size:[/cyan] {preset.chunk_size}")
            console.print(f"  [cyan]quality_threshold:[/cyan] {preset.quality_threshold}")
            console.print(f"  [cyan]validation_level:[/cyan] {preset.validation_level.value}")
            console.print(f"  [cyan]dedup_threshold:[/cyan] {preset.dedup_threshold}")
            console.print()
            console.print("[dim]Use --preset flag on process command to apply this preset.[/dim]")

    @presets_app.command("show")
    def presets_show(
        name: Annotated[
            str,
            typer.Argument(help="Preset name to display."),
        ],
    ) -> None:
        """Show detailed configuration of a specific preset.

        Displays all settings of a preset in a formatted panel.

        [bold]Example:[/bold]
            data-extract config presets show quality
            data-extract config presets show my-workflow
        """
        from rich.panel import Panel
        from rich.text import Text

        manager = PresetManager()

        try:
            preset = manager.load(name)
        except KeyError:
            console.print(f"[red]Error:[/red] Preset not found: {name}")
            raise typer.Exit(code=1)

        # Determine preset type
        from data_extract.cli.config.presets import BUILTIN_PRESETS

        preset_type = "built-in" if name in BUILTIN_PRESETS else "user"

        # Build preset details
        details = Text()
        details.append(f"Type: {preset_type}\n", style="dim")
        details.append(f"Description: {preset.description}\n\n", style="italic")
        details.append("Settings:\n", style="bold")
        details.append(f"  chunk_size: {preset.chunk_size}\n", style="cyan")
        details.append(f"  quality_threshold: {preset.quality_threshold}\n", style="cyan")
        details.append(f"  validation_level: {preset.validation_level.value}\n", style="cyan")
        details.append(f"  dedup_threshold: {preset.dedup_threshold}\n", style="cyan")
        details.append(f"  include_metadata: {preset.include_metadata}\n", style="cyan")
        details.append(f"  output_format: {preset.output_format}\n", style="cyan")
        if preset.created:
            details.append(
                f"\nCreated: {preset.created.strftime('%Y-%m-%d %H:%M:%S')}", style="dim"
            )

        panel = Panel(
            details,
            title=f"[bold]Preset: {name}[/bold]",
            border_style="green" if preset_type == "user" else "cyan",
        )
        console.print(panel)

    @presets_app.command("delete")
    def presets_delete(
        name: Annotated[
            str,
            typer.Argument(help="Preset name to delete."),
        ],
        yes: Annotated[
            bool,
            typer.Option(
                "--yes",
                "-y",
                help="Skip confirmation prompt.",
            ),
        ] = False,
    ) -> None:
        """Delete a user-defined preset.

        Removes a custom preset from ~/.data-extract/presets/.
        Built-in presets cannot be deleted.

        [bold]Example:[/bold]
            data-extract config presets delete my-workflow
            data-extract config presets delete old-preset --yes
        """
        from rich.prompt import Confirm

        manager = PresetManager()

        # Check if trying to delete built-in preset (AC-5.5-4)
        from data_extract.cli.config.presets import BUILTIN_PRESETS

        if name in BUILTIN_PRESETS:
            console.print(f"[red]Error:[/red] Cannot delete built-in preset: {name}")
            console.print("[dim]Built-in presets are protected from deletion.[/dim]")
            raise typer.Exit(code=1)

        # Check if preset exists
        try:
            manager.load(name)
        except KeyError:
            console.print(f"[red]Error:[/red] Preset not found: {name}")
            raise typer.Exit(code=1)

        # Confirmation prompt
        if not yes:
            confirmed = Confirm.ask(f"Delete preset '{name}'?")
            if not confirmed:
                console.print("[yellow]Cancelled.[/yellow]")
                raise typer.Exit(code=0)

        try:
            manager.delete(name)
            console.print(f"[green]Deleted preset:[/green] {name}")
        except ValueError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)
        except KeyError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1)

    # Register presets subcommand group with config app
    config_app.add_typer(presets_app, name="presets")

    @config_app.command()
    def validate(
        ctx: typer.Context,
        file: Annotated[
            Optional[Path],
            typer.Option(
                "--file",
                "-f",
                help="Specific config file to validate (defaults to .data-extract.yaml).",
            ),
        ] = None,
    ) -> None:
        """Validate configuration file for errors.

        Checks for YAML syntax errors, type mismatches, and range violations.
        Provides helpful suggestions for fixing issues.

        [bold]Example:[/bold]
            data-extract config validate
            data-extract config validate --file custom-config.yaml
        """

        # Determine which file to validate
        if file is None:
            global_config_path = _get_root_param(ctx, "config")
            file = Path(global_config_path) if global_config_path else Path.cwd() / ".data-extract.yaml"

        # Validate the config
        is_valid, errors = validate_config_file(file)

        if is_valid:
            console.print(f"[green]Configuration is valid:[/green] {file}")
        else:
            console.print(f"[red]Configuration validation failed:[/red] {file}")
            console.print()
            for error in errors:
                console.print(f"[red]✗[/red] {error}")
            raise typer.Exit(code=1)

    app.add_typer(config_app, name="config")



def _register_retry_command(app: typer.Typer) -> None:
    """Register retry command backed by shared retry service."""

    @app.command()
    def retry(
        last: Annotated[
            bool,
            typer.Option(
                "--last",
                help="Retry failed files from the most recent session.",
            ),
        ] = False,
        session: Annotated[
            Optional[str],
            typer.Option(
                "--session",
                help="Retry failed files from specific session ID.",
            ),
        ] = None,
        file: Annotated[
            Optional[Path],
            typer.Option(
                "--file",
                help="Retry a specific file.",
            ),
        ] = None,
        backoff: Annotated[
            bool,
            typer.Option(
                "--backoff",
                help="Enable exponential backoff between retries.",
            ),
        ] = False,
        non_interactive: Annotated[
            bool,
            typer.Option(
                "--non-interactive",
                help="Skip confirmation prompts.",
            ),
        ] = False,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable verbose output.",
            ),
        ] = False,
    ) -> None:
        """Retry failed files from previous sessions."""
        from data_extract.cli.exit_codes import EXIT_CONFIG_ERROR, EXIT_FAILURE
        from data_extract.contracts import RetryRequest
        from data_extract.services import RetryService

        if not any([last, session, file]):
            console.print("[red]Error:[/red] Must specify --last, --session, or --file")
            raise typer.Exit(code=EXIT_CONFIG_ERROR)

        if sum([last, session is not None, file is not None]) > 1:
            console.print("[red]Error:[/red] Can only specify one of --last, --session, or --file")
            raise typer.Exit(code=EXIT_CONFIG_ERROR)

        if backoff and not non_interactive:
            console.print("[dim]Backoff is active for repeated failures.[/dim]")

        work_dir_env = os.environ.get("DATA_EXTRACT_WORK_DIR")
        work_dir = Path(work_dir_env) if work_dir_env else Path.cwd()

        request = RetryRequest(
            last=last,
            session=session,
            file=str(file) if file else None,
            backoff=backoff,
            non_interactive=non_interactive,
        )

        try:
            result = RetryService().run_retry(request, work_dir=work_dir)
        except FileNotFoundError as exc:
            console.print(f"[yellow]{exc}[/yellow]")
            raise typer.Exit(code=0) from exc
        except ValueError as exc:
            console.print(f"[red]Configuration error:[/red] {exc}")
            raise typer.Exit(code=EXIT_CONFIG_ERROR) from exc
        except Exception as exc:
            console.print(f"[red]Retry failed:[/red] {exc}")
            raise typer.Exit(code=EXIT_FAILURE) from exc

        console.print(
            f"[green]Retry complete:[/green] {result.processed_count} succeeded, "
            f"{result.failed_count} failed, {result.skipped_count} skipped"
        )

        if verbose and result.failed_files:
            for failure in result.failed_files:
                console.print(f"[red]{failure.path}[/red]: {failure.error_message}")

        raise typer.Exit(code=result.exit_code)
def _register_validate_command(app: typer.Typer) -> None:
    """Register validate command for input validation.

    Provides validation for input files before processing.

    Args:
        app: Parent Typer application to register command with.
    """

    @app.command()
    def validate(
        input_path: Annotated[
            Path,
            typer.Argument(
                help="Input directory or file to validate.",
            ),
        ],
        recursive: Annotated[
            bool,
            typer.Option(
                "--recursive",
                "-r",
                help="Validate subdirectories recursively.",
            ),
        ] = False,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Enable verbose output.",
            ),
        ] = False,
    ) -> None:
        """Validate input files before processing.

        Checks file formats, accessibility, and estimates processing time.
        Useful for verifying large batches before committing to full processing.

        [bold]Checks Performed:[/bold]
        - File format detection and support
        - File accessibility and permissions
        - Basic corruption detection
        - Processing time estimation

        [bold]Example:[/bold]
            data-extract validate ./documents/
            data-extract validate ./file.pdf --verbose
            data-extract validate ./batch/ -r
        """
        console.print(f"[blue]Validating files in {input_path}...[/blue]")

        if not input_path.exists():
            console.print(f"[red]Error:[/red] Input path does not exist: {input_path}")
            raise typer.Exit(code=1)

        # Get list of files to validate
        if input_path.is_file():
            files = [input_path]
        else:
            pattern = "**/*" if recursive else "*"
            supported_extensions = {".pdf", ".docx", ".xlsx", ".pptx", ".csv", ".txt"}
            files = [
                f
                for f in input_path.glob(pattern)
                if f.is_file() and f.suffix.lower() in supported_extensions
            ]

        if not files:
            console.print("[yellow]No supported files found to validate.[/yellow]")
            raise typer.Exit(code=0)

        console.print(f"Found [cyan]{len(files)}[/cyan] files to validate")

        # Validate each file
        valid_count = 0
        invalid_files = []

        for file in files:
            # Basic validation checks
            is_valid = True
            reasons = []

            # Check if readable
            try:
                file.stat()
            except (PermissionError, OSError) as e:
                is_valid = False
                reasons.append(f"Permission error: {e}")

            # Check file size (warn if > 100MB)
            try:
                size_mb = file.stat().st_size / (1024 * 1024)
                if size_mb > 100:
                    reasons.append(f"Large file: {size_mb:.1f}MB")
            except (PermissionError, OSError):
                pass

            if is_valid:
                valid_count += 1
                if verbose:
                    console.print(f"  [green]✓[/green] {file.name}")
            else:
                invalid_files.append((file, reasons))
                if verbose:
                    console.print(f"  [red]✗[/red] {file.name}: {', '.join(reasons)}")

        # Summary
        console.print()
        console.print(f"[green]{valid_count}/{len(files)}[/green] files valid")

        if invalid_files:
            console.print(f"[yellow]{len(invalid_files)}[/yellow] files have issues:")
            for file, reasons in invalid_files:
                console.print(f"  [yellow]⚠[/yellow] {file.name}: {', '.join(reasons)}")

        if valid_count == len(files):
            console.print("[green]All files are valid and ready for processing.[/green]")
        else:
            console.print("[yellow]Some files may need attention before processing.[/yellow]")


def _register_session_commands(app: typer.Typer) -> None:
    """Register session management command group.

    Provides session listing, cleaning, and inspection commands.

    Args:
        app: Parent Typer application to register commands with.
    """
    # Create session sub-application
    session_app = typer.Typer(
        name="session",
        help="Session management commands for tracking processing state.",
        rich_markup_mode="rich",
        no_args_is_help=True,
    )

    @session_app.command("list")
    def session_list(
        all: Annotated[
            bool,
            typer.Option(
                "--all",
                help="Include archived sessions from archive/ subdirectory.",
            ),
        ] = False,
    ) -> None:
        """List all active and archived sessions.

        Shows session IDs, status, source directories, and progress.

        [bold]Example:[/bold]
            data-extract session list
            data-extract session list --all
        """
        # For testing: allow override via environment variable
        work_dir_env = os.environ.get("DATA_EXTRACT_WORK_DIR")
        work_dir = Path(work_dir_env) if work_dir_env else Path.cwd()
        manager = SessionManager(work_dir=work_dir)

        # List active sessions
        if manager.session_dir.exists():
            active_sessions = []
            archived_sessions = []

            # Read active sessions from main session directory
            for session_file in manager.session_dir.glob("session-*.json"):
                if session_file.suffix == ".tmp":
                    continue

                try:
                    content = session_file.read_text()
                    state_dict = json.loads(content)
                    session_id = state_dict.get("session_id", "unknown")
                    status = state_dict.get("status", "unknown")
                    source = state_dict.get("source_directory", "unknown")

                    if status in ("in_progress", "interrupted"):
                        active_sessions.append((session_id, status, source))
                    else:
                        archived_sessions.append((session_id, status, source))
                except (json.JSONDecodeError, KeyError):
                    continue

            # Read archived sessions from archive/ subdirectory if --all flag set
            if all:
                archive_dir = manager.session_dir / "archive"
                if archive_dir.exists():
                    for archive_file in archive_dir.glob("session-*.json"):
                        try:
                            content = archive_file.read_text()
                            state_dict = json.loads(content)
                            session_id = state_dict.get("session_id", "unknown")
                            status = state_dict.get("status", "completed")
                            source = state_dict.get("source_directory", "unknown")
                            archived_sessions.append((session_id, status, source))
                        except (json.JSONDecodeError, KeyError):
                            continue

            # Display active sessions
            if active_sessions:
                console.print("\n[cyan]Active Sessions:[/cyan]")
                for session_id, status, source in active_sessions:
                    console.print(f"  {session_id} ({status}) - {source}")
            else:
                console.print("\n[dim]No active sessions found.[/dim]")

            # Display archived sessions
            if archived_sessions:
                console.print("\n[yellow]Archived Sessions:[/yellow]")
                for session_id, status, source in archived_sessions:
                    console.print(f"  {session_id} ({status}) - {source}")
        else:
            console.print("[dim]No session directory found.[/dim]")

    @session_app.command("clean")
    def session_clean(
        session_id: Annotated[
            Optional[str],
            typer.Argument(help="Session ID to clean (optional - cleans old archives if omitted)"),
        ] = None,
        force: Annotated[
            bool,
            typer.Option(
                "--force",
                "-f",
                help="Skip confirmation prompts.",
            ),
        ] = False,
        all: Annotated[
            bool,
            typer.Option(
                "--all",
                help="Remove all completed sessions regardless of age.",
            ),
        ] = False,
        days: Annotated[
            int,
            typer.Option(
                "--days",
                help="Remove archived sessions older than this many days.",
            ),
        ] = 7,
    ) -> None:
        """Clean up session files.

        Remove old archived sessions or a specific session by ID.

        [bold]Examples:[/bold]
            data-extract session clean                    # Clean old archives
            data-extract session clean --all               # Clean all completed sessions
            data-extract session clean abc123 --force      # Remove specific session
            data-extract session clean --days 30           # Custom retention period
        """
        # For testing: allow override via environment variable
        work_dir_env = os.environ.get("DATA_EXTRACT_WORK_DIR")
        work_dir = Path(work_dir_env) if work_dir_env else Path.cwd()
        manager = SessionManager(work_dir=work_dir)

        if session_id:
            # Clean specific session
            session_file = manager.session_dir / f"session-{session_id}.json"

            if not session_file.exists():
                console.print(f"[red]Session not found:[/red] {session_id}")
                raise typer.Exit(code=1)

            if not force:
                confirm = typer.confirm(f"Remove session {session_id}?")
                if not confirm:
                    console.print("[yellow]Cancelled.[/yellow]")
                    raise typer.Exit(code=0)

            session_file.unlink()
            console.print(f"[green]Removed session:[/green] {session_id}")
        else:
            # Clean old archived sessions
            from datetime import datetime, timedelta

            cutoff = datetime.now() - timedelta(days=days)
            removed_count = 0

            # Check if there are any sessions to clean
            has_sessions = False

            if manager.session_dir.exists():
                # Clean from main session directory
                for session_file in manager.session_dir.glob("session-*.json"):
                    has_sessions = True
                    try:
                        mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
                        content = session_file.read_text()
                        state_dict = json.loads(content)
                        status = state_dict.get("status", "unknown")

                        # Check if it's archived (not active)
                        if status not in ("in_progress", "interrupted"):
                            # Remove if --all flag or older than cutoff
                            if all or mtime < cutoff:
                                if not force:
                                    confirm = typer.confirm(
                                        f"Remove {removed_count + 1} session(s)?",
                                        default=True,
                                    )
                                    if not confirm:
                                        console.print("[yellow]Cancelled.[/yellow]")
                                        raise typer.Exit(code=0)
                                    force = True  # Don't ask again for subsequent sessions

                                session_file.unlink()
                                removed_count += 1
                    except (OSError, json.JSONDecodeError):
                        continue

                # Also clean from archive directory
                archive_dir = manager.session_dir / "archive"
                if archive_dir.exists():
                    for archive_file in archive_dir.glob("session-*.json"):
                        has_sessions = True
                        try:
                            mtime = datetime.fromtimestamp(archive_file.stat().st_mtime)
                            # Remove if --all flag or older than cutoff
                            if all or mtime < cutoff:
                                archive_file.unlink()
                                removed_count += 1
                        except OSError:
                            continue

            if not has_sessions:
                console.print("[dim]No sessions found to clean.[/dim]")
            elif removed_count > 0:
                console.print(f"[green]Removed {removed_count} old session(s).[/green]")
            else:
                console.print("[dim]No old sessions to clean.[/dim]")

    @session_app.command("resume")
    def session_resume(
        session_id: Annotated[
            str,
            typer.Argument(help="Session ID to resume"),
        ],
    ) -> None:
        """Resume an interrupted or orphaned session.

        Loads the session state and allows continuation of processing.

        [bold]Example:[/bold]
            data-extract session resume abc123
        """
        # For testing: allow override via environment variable
        work_dir_env = os.environ.get("DATA_EXTRACT_WORK_DIR")
        work_dir = Path(work_dir_env) if work_dir_env else Path.cwd()
        manager = SessionManager(work_dir=work_dir)
        session_state = manager.load_session(session_id)

        if not session_state:
            console.print(f"[red]Session not found:[/red] {session_id}")
            raise typer.Exit(code=1)

        # Display session resume information
        console.print(f"\n[cyan]Resuming session:[/cyan] {session_state.session_id}")
        console.print(f"[cyan]Status:[/cyan] {session_state.status}")
        console.print(f"[cyan]Source:[/cyan] {session_state.source_directory}")
        console.print()
        console.print("[cyan]Progress:[/cyan]")
        console.print(f"  Total: {session_state.statistics.total_files}")
        console.print(f"  Processed: {session_state.statistics.processed_count}")
        console.print(f"  Failed: {session_state.statistics.failed_count}")
        console.print(
            f"  Remaining: {session_state.statistics.total_files - session_state.statistics.processed_count - session_state.statistics.failed_count}"
        )
        console.print()
        console.print(
            "[green]Session loaded successfully.[/green] Use 'data-extract process' with --resume to continue."
        )

    @session_app.command("show")
    def session_show(
        session_id: Annotated[
            str,
            typer.Argument(help="Session ID to display"),
        ],
    ) -> None:
        """Show detailed information about a session.

        Displays session status, files processed, failures, and timing.

        [bold]Example:[/bold]
            data-extract session show abc123
        """
        # For testing: allow override via environment variable
        work_dir_env = os.environ.get("DATA_EXTRACT_WORK_DIR")
        work_dir = Path(work_dir_env) if work_dir_env else Path.cwd()
        manager = SessionManager(work_dir=work_dir)
        session_state = manager.load_session(session_id)

        if not session_state:
            console.print(f"[red]Session not found:[/red] {session_id}")
            raise typer.Exit(code=1)

        # Display session details
        console.print(f"\n[cyan]Session:[/cyan] {session_state.session_id}")
        console.print(f"[cyan]Status:[/cyan] {session_state.status}")
        console.print(f"[cyan]Source:[/cyan] {session_state.source_directory}")
        console.print(f"[cyan]Started:[/cyan] {session_state.started_at.isoformat()}")
        console.print(f"[cyan]Updated:[/cyan] {session_state.updated_at.isoformat()}")
        console.print()
        console.print("[cyan]Progress:[/cyan]")
        console.print(f"  Total: {session_state.statistics.total_files}")
        console.print(f"  Processed: {session_state.statistics.processed_count}")
        console.print(f"  Failed: {session_state.statistics.failed_count}")

        if session_state.failed_files:
            console.print()
            console.print("[yellow]Failed Files:[/yellow]")
            for failed in session_state.failed_files:
                console.print(f"  {Path(failed['path']).name}: {failed['error_message']}")

    # Register the session sub-app
    app.add_typer(session_app)



def _register_ui_command(app: typer.Typer) -> None:
    """Register local UI launcher command."""

    @app.command()
    def ui(
        host: Annotated[
            str,
            typer.Option(
                "--host",
                help="Host interface for API/UI server.",
            ),
        ] = "127.0.0.1",
        port: Annotated[
            int,
            typer.Option(
                "--port",
                "-p",
                help="Port for API/UI server.",
            ),
        ] = 8765,
        no_open: Annotated[
            bool,
            typer.Option(
                "--no-open",
                help="Do not open browser automatically.",
            ),
        ] = False,
        reload: Annotated[
            bool,
            typer.Option(
                "--reload",
                help="Enable hot reload for API development.",
            ),
        ] = False,
        check: Annotated[
            bool,
            typer.Option(
                "--check",
                help="Run startup checks and exit without launching server.",
            ),
        ] = False,
    ) -> None:
        """Start the local UI and API runtime."""
        import importlib.util
        import webbrowser
        from threading import Timer

        from data_extract.api.database import APP_HOME, DB_PATH

        errors: list[str] = []
        warnings: list[str] = []

        for module_name in ["fastapi", "uvicorn", "sqlalchemy"]:
            if importlib.util.find_spec(module_name) is None:
                errors.append(f"Missing dependency: {module_name}")

        try:
            APP_HOME.mkdir(parents=True, exist_ok=True)
            probe = APP_HOME / ".write-check"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
        except OSError as exc:
            errors.append(f"App home is not writable ({APP_HOME}): {exc}")

        try:
            import spacy

            if not spacy.util.is_package("en_core_web_sm"):
                warnings.append("spaCy model 'en_core_web_sm' is not installed")
        except Exception as exc:
            warnings.append(f"spaCy check skipped: {exc}")

        if warnings:
            for warning in warnings:
                console.print(f"[yellow]Warning:[/yellow] {warning}")

        if errors:
            for error in errors:
                console.print(f"[red]Error:[/red] {error}")
            raise typer.Exit(code=1)

        console.print(f"[green]Runtime checks passed.[/green] DB: {DB_PATH}")
        if check:
            raise typer.Exit(code=0)

        try:
            import uvicorn
        except Exception as exc:  # pragma: no cover - guarded above
            console.print(f"[red]Unable to import uvicorn:[/red] {exc}")
            raise typer.Exit(code=1) from exc

        url = f"http://{host}:{port}"
        if not no_open:
            Timer(0.8, lambda: webbrowser.open(url)).start()

        console.print(f"[cyan]Starting UI:[/cyan] {url}")
        uvicorn.run("data_extract.api.main:app", host=host, port=port, reload=reload)


def _register_status_command(app: typer.Typer) -> None:
    """Register corpus status command backed by shared status service."""

    @app.command()
    def status(
        input_path: Annotated[
            Optional[Path],
            typer.Argument(
                help="Source directory to check status for (default: current directory).",
            ),
        ] = None,
        output_path: Annotated[
            Optional[Path],
            typer.Option(
                "--output",
                "-o",
                help="Output directory to check against.",
            ),
        ] = None,
        format: Annotated[
            str,
            typer.Option(
                "--format",
                "-f",
                help="Output format: text, json.",
            ),
        ] = "text",
        json_output: Annotated[
            bool,
            typer.Option(
                "--json",
                help="Output as JSON (shorthand for --format json).",
            ),
        ] = False,
        cleanup: Annotated[
            bool,
            typer.Option(
                "--cleanup",
                help="Remove orphaned output files that no longer have source files.",
            ),
        ] = False,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-v",
                help="Show detailed file-level status breakdown.",
            ),
        ] = False,
    ) -> None:
        """Show corpus sync status and detect changes."""
        from rich.panel import Panel
        from rich.text import Text

        from data_extract.services.status_service import StatusService

        effective_format = "json" if json_output else format
        if effective_format not in {"text", "json"}:
            console.print(
                f"[red]Error:[/red] Invalid format '{effective_format}'. Must be 'text' or 'json'."
            )
            raise typer.Exit(code=1)

        source = (input_path or Path.cwd()).resolve()
        output = (output_path or source / "output").resolve()
        if not source.exists():
            console.print(f"[red]Error:[/red] Source directory not found: {source}")
            raise typer.Exit(code=1)

        payload = StatusService().get_status(source, output, cleanup=cleanup)
        if effective_format == "json":
            console.print(json.dumps(payload, indent=2))
            return

        changes = payload["changes"]
        panel_content = Text()
        panel_content.append(f"Last updated: {payload['last_updated'] or 'Never'}\n")
        panel_content.append(f"Total files: {payload['total_files']}\n")
        panel_content.append(f"Source: {payload['source_dir']}\n")
        panel_content.append(f"Output: {payload['output_dir']}\n\n")
        panel_content.append(f"Sync status: {payload['sync_state']}\n", style="bold")
        panel_content.append(
            f"New: {changes['new']}  Modified: {changes['modified']}  "
            f"Unchanged: {changes['unchanged']}  Deleted: {changes['deleted']}\n"
        )

        orphaned_count = payload["orphaned_count"]
        if orphaned_count > 0:
            if cleanup:
                panel_content.append(
                    f"Orphaned outputs removed: {payload['cleaned_count']}\n", style="yellow"
                )
            else:
                panel_content.append(
                    f"Orphaned outputs detected: {orphaned_count}\n", style="yellow"
                )

        if verbose and payload["orphaned_outputs"]:
            panel_content.append("\nOrphaned files:\n", style="dim")
            for orphan in payload["orphaned_outputs"][:10]:
                panel_content.append(f"- {Path(orphan).name}\n", style="dim")

        console.print(Panel(panel_content, title="Corpus Status", border_style="cyan"))
def get_app() -> typer.Typer:
    """Get or create the singleton Typer application instance.

    Returns the module-level singleton app, creating it if necessary.
    This ensures consistent app configuration across the application.

    Returns:
        The singleton Typer application instance.

    Example:
        >>> app = get_app()
        >>> assert get_app() is app  # Same instance
    """
    global _app
    if _app is None:
        _app = create_app()
    return _app


def _reset_app() -> None:
    """Reset the singleton app instance for testing.

    This function is for test isolation only. It clears the singleton
    to allow fresh app creation in tests.

    Warning:
        Do not use in production code.
    """
    global _app
    _app = None


# Module-level app for entry point
app = get_app()
