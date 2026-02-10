"""Semantic analysis CLI commands (Typer implementation).

Greenfield implementation of semantic analysis commands using Typer.
Migrated from brownfield Click-based implementation.

Implements AC-4.5-1 (analyze), AC-4.5-2 (deduplicate), AC-4.5-3 (cluster).
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from data_extract.chunk.models import Chunk
from data_extract.cli.config import SemanticCliConfig, load_config_file, merge_config
from data_extract.semantic.lsa import LsaConfig, LsaReductionStage
from data_extract.semantic.models import SemanticResult, TfidfConfig
from data_extract.semantic.quality_metrics import QualityConfig, QualityMetricsStage
from data_extract.semantic.similarity import SimilarityAnalysisStage, SimilarityConfig
from data_extract.semantic.tfidf import TfidfVectorizationStage

console = Console()
semantic_app = typer.Typer(
    help="Semantic analysis commands for knowledge curation",
    no_args_is_help=True,
)


@semantic_app.command()
def analyze(
    input_path: Path = typer.Argument(
        ..., exists=True, help="Directory containing JSON chunk files or a single JSON file"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output path for results (default: stdout for JSON)"
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format (json, csv, or html)",
        case_sensitive=False,
    ),
    config_path: Optional[Path] = typer.Option(
        None, "--config", "-c", exists=True, help="Path to configuration file"
    ),
    max_features: Optional[int] = typer.Option(
        None, "--max-features", help="Maximum TF-IDF vocabulary size (default: 5000)"
    ),
    duplicate_threshold: Optional[float] = typer.Option(
        None,
        "--duplicate-threshold",
        min=0.0,
        max=1.0,
        help="Similarity threshold for duplicates (0.0-1.0, default: 0.95)",
    ),
    n_components: Optional[int] = typer.Option(
        None, "--n-components", help="Number of LSA components (default: 100)"
    ),
    min_quality: Optional[float] = typer.Option(
        None,
        "--min-quality",
        min=0.0,
        max=1.0,
        help="Minimum quality score threshold (0.0-1.0, default: 0.3)",
    ),
    no_cache: bool = typer.Option(False, "--no-cache", help="Disable caching for this operation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    report: bool = typer.Option(False, "--report", "-r", help="Generate full HTML report"),
    export_graph: Optional[str] = typer.Option(
        None,
        "--export-graph",
        "-g",
        help="Export similarity graph in specified format (json, csv, or dot)",
        case_sensitive=False,
    ),
) -> None:
    """Run full semantic analysis pipeline on documents.

    Executes TF-IDF vectorization, similarity analysis, LSA topic modeling,
    and quality metrics assessment. Generates comprehensive report.

    Examples:

        # Basic analysis with JSON output
        data-extract semantic analyze ./chunks/ -o results.json

        # Full HTML report
        data-extract semantic analyze ./chunks/ --report -o report.html

        # Custom configuration
        data-extract semantic analyze ./chunks/ --max-features 10000 --n-components 50
    """
    try:
        # Validate output format
        valid_formats = ["json", "csv", "html"]
        if output_format.lower() not in valid_formats:
            console.print(
                f"[red]Error:[/red] Invalid format '{output_format}'. "
                f"Must be one of: {', '.join(valid_formats)}"
            )
            raise typer.Exit(1)

        # Validate export graph format
        if export_graph and export_graph.lower() not in ["json", "csv", "dot"]:
            console.print(
                f"[red]Error:[/red] Invalid graph format '{export_graph}'. "
                "Must be one of: json, csv, dot"
            )
            raise typer.Exit(1)

        # Load configuration
        file_config = load_config_file(config_path)
        cli_args = {
            "tfidf_max_features": max_features,
            "similarity_duplicate_threshold": duplicate_threshold,
            "lsa_n_components": n_components,
            "quality_min_score": min_quality,
            "cache_enabled": not no_cache,
        }
        config = merge_config(cli_args, file_config, SemanticCliConfig())

        # Load chunks
        chunks = _load_chunks(input_path, verbose)
        if not chunks:
            console.print("[red]Error:[/red] No valid chunks found in input path")
            raise typer.Exit(1)

        console.print(f"[blue]Loaded {len(chunks)} chunks from {input_path}[/blue]")

        # Run semantic pipeline with progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            # Create pipeline stages
            tfidf_config = TfidfConfig(
                max_features=config.tfidf_max_features,
                min_df=config.tfidf_min_df,
                max_df=config.tfidf_max_df,
                ngram_range=config.tfidf_ngram_range,
                use_cache=config.cache_enabled,
            )
            similarity_config = SimilarityConfig(
                duplicate_threshold=config.similarity_duplicate_threshold,
                related_threshold=config.similarity_related_threshold,
                use_cache=config.cache_enabled,
            )
            lsa_config = LsaConfig(
                n_components=config.lsa_n_components,
                n_clusters=config.lsa_n_clusters,
                use_cache=config.cache_enabled,
            )
            quality_config = QualityConfig(
                min_quality=config.quality_min_score,
                use_cache=config.cache_enabled,
            )

            # Stage 1: TF-IDF
            task1 = progress.add_task("[cyan]TF-IDF Vectorization...", total=1)
            tfidf_stage = TfidfVectorizationStage(config=tfidf_config)
            tfidf_result = tfidf_stage.process(chunks, None)
            progress.update(task1, completed=1)

            if not tfidf_result.success:
                console.print(f"[red]TF-IDF failed:[/red] {tfidf_result.error}")
                raise typer.Exit(1)

            # Stage 2: Similarity
            task2 = progress.add_task("[cyan]Similarity Analysis...", total=1)
            similarity_stage = SimilarityAnalysisStage(config=similarity_config)
            similarity_result = similarity_stage.process(tfidf_result, None)
            progress.update(task2, completed=1)

            # Stage 3: LSA
            task3 = progress.add_task("[cyan]LSA Topic Extraction...", total=1)
            lsa_stage = LsaReductionStage(config=lsa_config)
            lsa_result = lsa_stage.process(similarity_result, None)
            progress.update(task3, completed=1)

            # Stage 4: Quality Metrics
            task4 = progress.add_task("[cyan]Quality Assessment...", total=1)
            quality_stage = QualityMetricsStage(config=quality_config)
            enriched_chunks = quality_stage.process(chunks, None)
            progress.update(task4, completed=1)

        # Generate output
        results = _compile_results(lsa_result, enriched_chunks, config)

        if report or output_format.lower() == "html":
            from data_extract.semantic.reporting import generate_html_report

            html_content = generate_html_report(results)
            if output:
                output.write_text(html_content)
                console.print(f"[green]Report saved to {output}[/green]")
            else:
                console.print(html_content)
        elif output_format.lower() == "csv":
            from data_extract.semantic.reporting import generate_csv_report

            csv_content = generate_csv_report(results)
            if output:
                output.write_text(csv_content)
                console.print(f"[green]CSV saved to {output}[/green]")
            else:
                console.print(csv_content)
        else:
            # JSON output
            json_output = json.dumps(results, indent=2, default=str)
            if output:
                output.write_text(json_output)
                console.print(f"[green]Results saved to {output}[/green]")
            else:
                console.print(json_output)

        # Export similarity graph if requested
        if export_graph:
            from data_extract.semantic.reporting import export_similarity_graph

            graph_content = export_similarity_graph(results, output_format=export_graph.lower())
            if output:
                # Derive graph filename from output path
                graph_ext = {"json": ".graph.json", "csv": ".graph.csv", "dot": ".graph.dot"}
                graph_path = output.with_suffix(graph_ext[export_graph.lower()])
                graph_path.write_text(graph_content)
                console.print(f"[green]Graph exported to {graph_path}[/green]")
            else:
                console.print("\n[bold]Similarity Graph:[/bold]")
                console.print(graph_content)

        # Display summary
        _display_summary(results, verbose)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        if verbose:
            import traceback

            console.print(traceback.format_exc())
        raise typer.Exit(1)


@semantic_app.command()
def deduplicate(
    input_path: Path = typer.Argument(
        ..., exists=True, help="Directory containing JSON chunk files"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output path for deduplicated chunks"
    ),
    threshold: float = typer.Option(
        0.95,
        "--threshold",
        "-t",
        min=0.0,
        max=1.0,
        help="Similarity threshold for duplicate detection (0.0-1.0)",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show duplicates without removing them"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Remove duplicate documents based on similarity threshold.

    Identifies near-duplicate documents using TF-IDF similarity and
    removes duplicates, keeping one representative from each group.

    Examples:

        # Preview duplicates (dry run)
        data-extract semantic deduplicate ./chunks/ --dry-run

        # Remove duplicates with 90% threshold
        data-extract semantic deduplicate ./chunks/ -t 0.9 -o ./clean/

        # Verbose output showing all pairs
        data-extract semantic deduplicate ./chunks/ -v
    """
    try:
        # Load chunks
        chunks = _load_chunks(input_path, verbose)
        if not chunks:
            console.print("[red]Error:[/red] No valid chunks found")
            raise typer.Exit(1)

        console.print(f"[blue]Analyzing {len(chunks)} chunks for duplicates...[/blue]")

        # Run TF-IDF and similarity analysis
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Finding duplicates...", total=None)

            tfidf_stage = TfidfVectorizationStage()
            tfidf_result = tfidf_stage.process(chunks, None)

            similarity_config = SimilarityConfig(duplicate_threshold=threshold)
            similarity_stage = SimilarityAnalysisStage(config=similarity_config)
            result = similarity_stage.process(tfidf_result, None)

            progress.update(task, completed=1)

        # Extract duplicate groups
        duplicate_groups = result.data.get("duplicate_groups", []) if result.data else []
        duplicate_pairs = result.data.get("similar_pairs", []) if result.data else []

        # Filter pairs above threshold
        duplicate_pairs = [(a, b, s) for a, b, s in duplicate_pairs if s >= threshold]

        # Display results
        console.print()
        if duplicate_groups:
            _display_duplicate_report(duplicate_groups, duplicate_pairs, threshold, verbose)

            # Calculate savings
            total_duplicates = sum(len(g) - 1 for g in duplicate_groups)
            savings_pct = (total_duplicates / len(chunks)) * 100 if chunks else 0

            console.print()
            panel = Panel(
                f"[bold]Duplicate Analysis Summary[/bold]\n\n"
                f"Total chunks: {len(chunks)}\n"
                f"Duplicate groups: {len(duplicate_groups)}\n"
                f"Duplicates found: {total_duplicates}\n"
                f"Potential reduction: [green]{savings_pct:.1f}%[/green]",
                title="Savings Report",
                border_style="green",
            )
            console.print(panel)

            if not dry_run and output:
                # Remove duplicates and save
                keep_ids = set()
                for group in duplicate_groups:
                    keep_ids.add(group[0])  # Keep first in each group

                # Add non-duplicate chunks
                all_duplicate_ids = set()
                for group in duplicate_groups:
                    all_duplicate_ids.update(group)

                for chunk in chunks:
                    if chunk.id not in all_duplicate_ids:
                        keep_ids.add(chunk.id)

                # Filter chunks
                clean_chunks = [c for c in chunks if c.id in keep_ids]

                # Save
                _save_chunks(clean_chunks, output)
                console.print(
                    f"\n[green]Saved {len(clean_chunks)} deduplicated chunks to {output}[/green]"
                )

        else:
            console.print(f"[green]No duplicates found above threshold {threshold}[/green]")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@semantic_app.command()
def cluster(
    input_path: Path = typer.Argument(
        ..., exists=True, help="Directory containing JSON chunk files"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output path for cluster assignments"
    ),
    n_clusters: Optional[int] = typer.Option(
        None, "--n-clusters", "-k", help="Number of clusters (default: auto-detect)"
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format (json, csv, or html)",
        case_sensitive=False,
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Group documents into clusters using LSA and K-means.

    Performs dimensionality reduction with LSA and clusters documents
    using K-means algorithm. Outputs cluster assignments and top terms.

    Examples:

        # Auto-detect cluster count
        data-extract semantic cluster ./chunks/ -o clusters.json

        # Specify 10 clusters
        data-extract semantic cluster ./chunks/ -k 10

        # HTML output with visualizations
        data-extract semantic cluster ./chunks/ -f html -o clusters.html
    """
    try:
        # Validate output format
        valid_formats = ["json", "csv", "html"]
        if output_format.lower() not in valid_formats:
            console.print(
                f"[red]Error:[/red] Invalid format '{output_format}'. "
                f"Must be one of: {', '.join(valid_formats)}"
            )
            raise typer.Exit(1)

        # Load chunks
        chunks = _load_chunks(input_path, verbose)
        if not chunks:
            console.print("[red]Error:[/red] No valid chunks found")
            raise typer.Exit(1)

        console.print(f"[blue]Clustering {len(chunks)} chunks...[/blue]")

        # Run pipeline
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Running LSA clustering...", total=None)

            # TF-IDF
            tfidf_stage = TfidfVectorizationStage()
            tfidf_result = tfidf_stage.process(chunks, None)

            # LSA with clustering
            lsa_config = LsaConfig(n_clusters=n_clusters)
            lsa_stage = LsaReductionStage(config=lsa_config)
            result = lsa_stage.process(tfidf_result, None)

            progress.update(task, completed=1)

        # Extract results
        clusters_data = result.data.get("clusters", []) if result.data else []
        topics = result.data.get("topics", {}) if result.data else {}
        silhouette = result.data.get("silhouette_score", 0.0) if result.data else 0.0

        # Build cluster report
        cluster_report = _build_cluster_report(chunks, clusters_data, topics, silhouette)

        # Display summary
        _display_cluster_summary(cluster_report, verbose)

        # Output results
        if output_format.lower() == "html":
            from data_extract.semantic.reporting import generate_cluster_html

            html_content = generate_cluster_html(cluster_report)
            if output:
                output.write_text(html_content)
                console.print(f"\n[green]Cluster report saved to {output}[/green]")
            else:
                console.print(html_content)
        elif output_format.lower() == "csv":
            csv_lines = ["chunk_id,cluster,cluster_size"]
            for chunk_id, cluster_id in zip(
                [c.id for c in chunks],
                clusters_data if len(clusters_data) else [],
            ):
                cluster_size = sum(1 for c in clusters_data if c == cluster_id)
                csv_lines.append(f"{chunk_id},{cluster_id},{cluster_size}")
            csv_content = "\n".join(csv_lines)
            if output:
                output.write_text(csv_content)
                console.print(f"\n[green]CSV saved to {output}[/green]")
            else:
                console.print(csv_content)
        else:
            json_output = json.dumps(cluster_report, indent=2, default=str)
            if output:
                output.write_text(json_output)
                console.print(f"\n[green]Results saved to {output}[/green]")
            else:
                console.print(json_output)

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@semantic_app.command()
def topics(
    input_path: Path = typer.Argument(
        ..., exists=True, help="Directory containing JSON chunk files"
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output path for topic extraction results"
    ),
    n_topics: int = typer.Option(10, "--n-topics", "-n", help="Number of topics to extract"),
    top_terms: int = typer.Option(10, "--top-terms", "-t", help="Number of top terms per topic"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
) -> None:
    """Extract topics from documents using LSA.

    Performs Latent Semantic Analysis to identify main topics/themes
    in the document corpus and shows top terms for each topic.

    Examples:

        # Extract 10 topics with 10 terms each
        data-extract semantic topics ./chunks/

        # Extract 20 topics with 15 terms each
        data-extract semantic topics ./chunks/ -n 20 -t 15 -o topics.json
    """
    try:
        # Load chunks
        chunks = _load_chunks(input_path, verbose)
        if not chunks:
            console.print("[red]Error:[/red] No valid chunks found")
            raise typer.Exit(1)

        console.print(f"[blue]Extracting topics from {len(chunks)} chunks...[/blue]")

        # Run pipeline
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Running LSA topic extraction...", total=None)

            # TF-IDF
            tfidf_stage = TfidfVectorizationStage()
            tfidf_result = tfidf_stage.process(chunks, None)

            # LSA
            lsa_config = LsaConfig(n_components=n_topics, top_n_terms=top_terms)
            lsa_stage = LsaReductionStage(config=lsa_config)
            result = lsa_stage.process(tfidf_result, None)

            progress.update(task, completed=1)

        # Extract topics
        topics_data = result.data.get("topics", {}) if result.data else {}
        explained_variance = result.data.get("explained_variance", []) if result.data else []

        # Display topics
        console.print()
        table = Table(title="Extracted Topics", show_header=True, header_style="bold cyan")
        table.add_column("Topic", style="cyan", width=8)
        table.add_column("Top Terms", style="white")
        table.add_column("Variance", style="green", width=10)

        for topic_idx, terms in sorted(topics_data.items()):
            variance = explained_variance[topic_idx] if topic_idx < len(explained_variance) else 0
            table.add_row(
                f"Topic {topic_idx}",
                ", ".join(terms[:top_terms]),
                f"{variance:.3f}",
            )

        console.print(table)

        # Total variance explained
        total_variance = sum(explained_variance) if explained_variance else 0
        console.print(f"\n[blue]Total variance explained:[/blue] {total_variance:.1%}")

        # Output results
        if output:
            result_dict = {
                "topics": topics_data,
                "explained_variance": [float(v) for v in explained_variance],
                "total_variance_explained": float(total_variance),
                "n_chunks": len(chunks),
            }
            output.write_text(json.dumps(result_dict, indent=2))
            console.print(f"\n[green]Results saved to {output}[/green]")

    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


# Helper functions


def _load_chunks(input_path: Path, verbose: bool = False) -> List[Chunk]:
    """Load chunks from JSON files in input path."""
    chunks = []

    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.glob("**/*.json"))

    for file_path in files:
        try:
            with open(file_path) as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                for item in data:
                    chunk = _dict_to_chunk(item)
                    if chunk:
                        chunks.append(chunk)
            elif isinstance(data, dict):
                if "chunks" in data:
                    for item in data["chunks"]:
                        chunk = _dict_to_chunk(item)
                        if chunk:
                            chunks.append(chunk)
                else:
                    chunk = _dict_to_chunk(data)
                    if chunk:
                        chunks.append(chunk)

            if verbose:
                console.print(f"[dim]Loaded {len(chunks)} chunks from {file_path}[/dim]")

        except Exception as e:
            if verbose:
                console.print(f"[yellow]Warning:[/yellow] Failed to load {file_path}: {e}")

    return chunks


def _dict_to_chunk(data: Dict[str, Any]) -> Optional[Chunk]:
    """Convert dictionary to Chunk object."""
    try:
        return Chunk(
            id=data.get("id", ""),
            text=data.get("text", ""),
            document_id=data.get("document_id", ""),
            position_index=data.get("position_index", 0),
            token_count=data.get("token_count", 0),
            word_count=data.get("word_count", len(data.get("text", "").split())),
            entities=data.get("entities", []),
            section_context=data.get("section_context", ""),
            quality_score=data.get("quality_score", 0.0),
            readability_scores=data.get("readability_scores", {}),
            metadata=data.get("metadata", {}),
        )
    except Exception:
        return None


def _save_chunks(chunks: List[Chunk], output_path: Path) -> None:
    """Save chunks to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    chunks_data = []
    for chunk in chunks:
        chunks_data.append(
            {
                "id": chunk.id,
                "text": chunk.text,
                "document_id": chunk.document_id,
                "position_index": chunk.position_index,
                "token_count": chunk.token_count,
                "word_count": chunk.word_count,
                "entities": chunk.entities,
                "section_context": chunk.section_context,
                "quality_score": chunk.quality_score,
                "readability_scores": chunk.readability_scores,
            }
        )

    with open(output_path, "w") as f:
        json.dump({"chunks": chunks_data}, f, indent=2)


def _compile_results(
    semantic_result: SemanticResult,
    enriched_chunks: List[Chunk],
    config: SemanticCliConfig,
) -> Dict[str, Any]:
    """Compile analysis results into report dictionary."""
    data = semantic_result.data or {}
    metadata = semantic_result.metadata or {}

    return {
        "summary": {
            "total_chunks": len(enriched_chunks),
            "vocabulary_size": metadata.get("vocabulary_size", 0),
            "n_components": metadata.get("n_components", 0),
            "n_clusters": metadata.get("n_clusters", 0),
            "cache_hit": semantic_result.cache_hit,
            "processing_time_ms": semantic_result.processing_time_ms,
        },
        "similarity": {
            "duplicate_groups": data.get("duplicate_groups", []),
            "n_duplicates": len(data.get("duplicate_groups", [])),
            "statistics": data.get("similarity_statistics", {}),
        },
        "topics": data.get("topics", {}),
        "clusters": {
            "assignments": (
                [int(c) for c in data.get("clusters", [])]
                if data.get("clusters") is not None
                else []
            ),
            "silhouette_score": data.get("silhouette_score", 0.0),
        },
        "quality": {
            "distribution": _get_quality_distribution(enriched_chunks),
            "mean_score": (
                sum(c.quality_score for c in enriched_chunks) / len(enriched_chunks)
                if enriched_chunks
                else 0
            ),
        },
        "config": {
            "tfidf_max_features": config.tfidf_max_features,
            "similarity_threshold": config.similarity_duplicate_threshold,
            "lsa_n_components": config.lsa_n_components,
            "quality_min_score": config.quality_min_score,
        },
    }


def _get_quality_distribution(chunks: List[Chunk]) -> Dict[str, int]:
    """Get quality score distribution from chunks."""
    distribution = {"high": 0, "medium": 0, "low": 0, "review": 0}

    for chunk in chunks:
        score = chunk.quality_score
        if score >= 0.7:
            distribution["high"] += 1
        elif score >= 0.3:
            distribution["medium"] += 1
        else:
            distribution["low"] += 1

    return distribution


def _display_summary(results: Dict[str, Any], verbose: bool) -> None:
    """Display analysis summary panel using Story 5-4 summary module.

    AC-5.4-1: Rich Panel summary display
    AC-5.4-2: Quality distribution breakdown
    AC-5.4-3: Per-stage timing breakdown
    AC-5.4-7: Next step recommendations
    """
    from data_extract.cli.summary import (
        QualityMetrics,
        SummaryReport,
        render_next_steps,
        render_quality_dashboard,
        render_summary_panel,
        render_timing_breakdown,
    )

    summary = results["summary"]
    similarity = results["similarity"]
    quality = results["quality"]

    # Build QualityMetrics from quality distribution
    distribution = quality.get("distribution", {})
    high_count = distribution.get("high", 0)
    medium_count = distribution.get("medium", 0)
    low_count = distribution.get("low", 0)

    quality_metrics = QualityMetrics(
        avg_quality=quality.get("mean_score", 0.0),
        excellent_count=high_count,
        good_count=medium_count,
        review_count=low_count,
        flagged_count=distribution.get("review", 0),
        entity_count=0,  # Not tracked in semantic analysis
        readability_score=0.0,  # Not tracked in semantic analysis
        duplicate_percentage=(
            (similarity.get("n_duplicates", 0) / summary["total_chunks"] * 100)
            if summary["total_chunks"] > 0
            else 0.0
        ),
    )

    # Build timing dict (semantic analysis has a single timing value)
    timing = {
        "semantic": summary.get("processing_time_ms", 0.0),
    }

    # Build next steps recommendations based on analysis results
    next_steps: List[str] = []
    if similarity.get("n_duplicates", 0) > 0:
        next_steps.append(
            f"Run 'semantic deduplicate' to remove {similarity['n_duplicates']} duplicate groups"
        )
    if quality.get("mean_score", 1.0) < 0.7:
        next_steps.append("Review low-quality chunks for potential data issues")
    if summary.get("n_clusters", 0) > 0:
        next_steps.append("Explore cluster assignments for thematic organization")
    if not next_steps:
        next_steps.append("Analysis complete - data ready for downstream use")

    # Build SummaryReport for rendering
    report = SummaryReport(
        files_processed=summary["total_chunks"],
        files_failed=0,
        chunks_created=summary["total_chunks"],
        errors=(),
        quality_metrics=quality_metrics,
        timing=timing,
        config=results.get("config", {}),
        next_steps=tuple(next_steps),
        processing_duration_ms=summary.get("processing_time_ms", 0.0),
    )

    console.print()

    # Render main summary panel (AC-5.4-1)
    console.print(render_summary_panel(report))

    # Render quality dashboard with distribution bars (AC-5.4-2)
    if verbose:
        console.print()
        console.print(render_quality_dashboard(quality_metrics))

        # Render timing breakdown (AC-5.4-3)
        console.print()
        console.print(render_timing_breakdown(timing))

    # Always render next steps (AC-5.4-7)
    console.print()
    console.print(render_next_steps(next_steps))


def _display_duplicate_report(
    groups: List[List[str]],
    pairs: List[tuple],
    threshold: float,
    verbose: bool,
) -> None:
    """Display duplicate detection report."""
    table = Table(title=f"Duplicate Groups (threshold: {threshold})", show_header=True)
    table.add_column("Group", style="cyan", width=8)
    table.add_column("Members", style="white")
    table.add_column("Size", style="green", width=6)

    for idx, group in enumerate(groups[:20]):  # Limit to 20 groups
        table.add_row(
            f"#{idx + 1}",
            ", ".join(group[:5]) + ("..." if len(group) > 5 else ""),
            str(len(group)),
        )

    console.print(table)

    if verbose and pairs:
        console.print()
        pair_table = Table(title="Similarity Pairs", show_header=True)
        pair_table.add_column("Document A", style="white")
        pair_table.add_column("Document B", style="white")
        pair_table.add_column("Similarity", style="green")

        for a, b, sim in pairs[:20]:
            pair_table.add_row(a, b, f"{sim:.3f}")

        console.print(pair_table)


def _build_cluster_report(
    chunks: List[Chunk],
    clusters: Any,
    topics: Dict[int, List[str]],
    silhouette: float,
) -> Dict[str, Any]:
    """Build cluster analysis report."""
    import numpy as np

    clusters_array = np.array(clusters) if len(clusters) else np.array([])
    n_clusters = len(np.unique(clusters_array)) if len(clusters_array) else 0

    cluster_sizes = {}
    cluster_members = {}

    if len(clusters_array):
        for cluster_id in range(n_clusters):
            mask = clusters_array == cluster_id
            cluster_sizes[cluster_id] = int(np.sum(mask))
            indices = np.where(mask)[0]
            cluster_members[cluster_id] = [chunks[i].id for i in indices[:10]]  # Top 10 members

    return {
        "n_clusters": n_clusters,
        "n_documents": len(chunks),
        "silhouette_score": float(silhouette),
        "cluster_sizes": cluster_sizes,
        "cluster_members": cluster_members,
        "cluster_topics": {k: topics.get(k, []) for k in range(n_clusters)},
    }


def _display_cluster_summary(report: Dict[str, Any], verbose: bool) -> None:
    """Display cluster analysis summary."""
    console.print()
    table = Table(title="Cluster Summary", show_header=True)
    table.add_column("Cluster", style="cyan", width=10)
    table.add_column("Size", style="green", width=8)
    table.add_column("Top Terms", style="white")

    for cluster_id in range(report["n_clusters"]):
        size = report["cluster_sizes"].get(cluster_id, 0)
        terms = report["cluster_topics"].get(cluster_id, [])[:5]
        table.add_row(
            f"Cluster {cluster_id}",
            str(size),
            ", ".join(terms) if terms else "N/A",
        )

    console.print(table)
    console.print(f"\n[blue]Silhouette Score:[/blue] {report['silhouette_score']:.3f}")
