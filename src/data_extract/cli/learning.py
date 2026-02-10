"""Learning mode support for CLI commands.

Story 5-1: Enhanced CLI UX - Journey 4 (Learning Mode).

This module provides educational explanations and tips for CLI users
who want to learn about NLP concepts while using the tool.

Features:
- Contextual explanations of TF-IDF, LSA, cosine similarity
- Step-by-step progress indicators
- Interactive pauses between steps
- Summary of concepts covered
"""

from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel

console = Console()


class LearningExplainer:
    """Provides educational explanations for semantic analysis concepts."""

    def __init__(self, interactive: bool = True):
        """Initialize learning explainer.

        Args:
            interactive: Whether to pause between explanations (default True).
        """
        self.interactive = interactive
        self.concepts_covered: List[str] = []

    def explain_tfidf(self) -> None:
        """Explain TF-IDF (Term Frequency-Inverse Document Frequency)."""
        explanation = """[bold cyan]TF-IDF (Term Frequency-Inverse Document Frequency)[/bold cyan]

[magenta]What's happening:[/magenta]
TF-IDF converts text into numerical vectors by measuring how important
each word is to a document relative to a collection of documents.

[magenta]Key Concepts:[/magenta]
• [bold]Term Frequency (TF):[/bold] How often a word appears in a document
• [bold]Inverse Document Frequency (IDF):[/bold] How rare a word is across all documents
• [bold]TF-IDF Score:[/bold] TF × IDF - high for distinctive words, low for common words

[magenta]Why it matters:[/magenta]
Words like "audit" in audit reports get high scores (distinctive),
while words like "the" get low scores (common everywhere).

This lets us find documents that are similar based on their unique vocabulary.
"""
        console.print(
            Panel(explanation, title="[LEARN] TF-IDF Vectorization", border_style="magenta")
        )
        self.concepts_covered.append("TF-IDF vectorization")

        if self.interactive:
            self._pause()

    def explain_lsa(self) -> None:
        """Explain LSA (Latent Semantic Analysis)."""
        explanation = """[bold cyan]LSA (Latent Semantic Analysis)[/bold cyan]

[magenta]What's happening:[/magenta]
LSA reduces the dimensionality of TF-IDF vectors using Singular Value
Decomposition (SVD) to discover hidden "topics" in your document collection.

[magenta]Key Concepts:[/magenta]
• [bold]Dimensionality Reduction:[/bold] Compress thousands of words into ~100 topics
• [bold]SVD (Singular Value Decomposition):[/bold] Mathematical technique to find patterns
• [bold]Latent Topics:[/bold] Hidden themes that connect related documents

[magenta]Why it matters:[/magenta]
LSA discovers that "risk assessment" and "control evaluation" belong to
the same topic, even though they use different words.

This enables topic modeling and improves clustering quality.
"""
        console.print(
            Panel(explanation, title="[LEARN] LSA Topic Modeling", border_style="magenta")
        )
        self.concepts_covered.append("LSA topic modeling")

        if self.interactive:
            self._pause()

    def explain_similarity(self) -> None:
        """Explain cosine similarity for duplicate detection."""
        explanation = """[bold cyan]Cosine Similarity for Duplicate Detection[/bold cyan]

[magenta]What's happening:[/magenta]
Cosine similarity measures the angle between two document vectors
to determine how similar they are, ranging from 0.0 (different) to 1.0 (identical).

[magenta]Key Concepts:[/magenta]
• [bold]Cosine Similarity:[/bold] Measures angle between vectors (0.0-1.0)
• [bold]Duplicate Threshold:[/bold] Similarity above this = duplicates (typically 0.95)
• [bold]Near-Duplicates:[/bold] Documents with similar content but minor differences

[magenta]Why it matters:[/magenta]
Documents with 0.96 similarity are likely duplicates - maybe one has
an extra line or slightly different formatting.

This lets us identify and remove redundant content for cleaner knowledge bases.
"""
        console.print(
            Panel(explanation, title="[LEARN] Similarity Analysis", border_style="magenta")
        )
        self.concepts_covered.append("Cosine similarity")

        if self.interactive:
            self._pause()

    def explain_quality_metrics(self) -> None:
        """Explain quality metrics for chunks."""
        explanation = """[bold cyan]Quality Metrics for Chunks[/bold cyan]

[magenta]What's happening:[/magenta]
Quality metrics assess how suitable each chunk is for RAG (Retrieval-Augmented
Generation) systems by measuring information density and readability.

[magenta]Key Concepts:[/magenta]
• [bold]Information Density:[/bold] Ratio of meaningful content to total text
• [bold]Readability Scores:[/bold] Flesch-Kincaid, SMOG, Gunning Fog indices
• [bold]Quality Thresholds:[/bold] Minimum scores to filter low-quality chunks

[magenta]Why it matters:[/magenta]
Chunks with low information density (headers, footers, boilerplate) or
very poor readability may not be useful for AI retrieval.

This helps build higher-quality knowledge bases for LLM applications.
"""
        console.print(Panel(explanation, title="[LEARN] Quality Metrics", border_style="magenta"))
        self.concepts_covered.append("Quality metrics")

        if self.interactive:
            self._pause()

    def show_step(self, step: int, total: int, message: str) -> None:
        """Show step indicator with message.

        Args:
            step: Current step number (1-indexed).
            total: Total number of steps.
            message: Description of current step.
        """
        console.print(
            f"[magenta][LEARN][/magenta] [bold blue][Step {step}/{total}][/bold blue] {message}"
        )
        if self.interactive:
            self._pause()

    def show_summary(self) -> None:
        """Show summary of concepts covered during learning session."""
        if not self.concepts_covered:
            return

        summary = "[bold cyan]What You Learned:[/bold cyan]\n\n"
        summary += "Today's session covered these NLP concepts:\n"
        for i, concept in enumerate(self.concepts_covered, 1):
            summary += f"{i}. [green]{concept}[/green]\n"

        summary += "\n[magenta]💡 Tip:[/magenta] Try running with [cyan]--verbose[/cyan] to see "
        summary += "detailed parameter values and processing statistics."

        console.print(Panel(summary, title="[LEARN] Summary", border_style="magenta"))

    def _pause(self) -> None:
        """Pause for user to read explanation."""
        if self.interactive:
            console.print("\n[dim]Press Enter to continue...[/dim]", end="")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                # Handle non-interactive environments gracefully
                pass
            console.print()


def create_learning_context(command: str, interactive: bool = True) -> Dict[str, Any]:
    """Create learning context for a command.

    Args:
        command: Name of the command being executed.
        interactive: Whether to enable interactive pauses.

    Returns:
        Dictionary with learning explainer and command context.
    """
    explainer = LearningExplainer(interactive=interactive)

    return {
        "explainer": explainer,
        "command": command,
        "interactive": interactive,
    }


def show_pipeline_overview(explainer: LearningExplainer, command: str) -> None:
    """Show overview of the processing pipeline for this command.

    Args:
        explainer: LearningExplainer instance.
        command: Command being executed.
    """
    if command == "analyze":
        overview = """[bold]Semantic Analysis Pipeline:[/bold]

1. [cyan]TF-IDF Vectorization[/cyan] - Convert text to numerical vectors
2. [cyan]Similarity Analysis[/cyan] - Compute pairwise document similarity
3. [cyan]LSA Topic Modeling[/cyan] - Extract latent topics
4. [cyan]Quality Assessment[/cyan] - Evaluate chunk quality metrics
5. [cyan]Report Generation[/cyan] - Compile comprehensive results
"""
    elif command == "deduplicate":
        overview = """[bold]Deduplication Pipeline:[/bold]

1. [cyan]TF-IDF Vectorization[/cyan] - Convert documents to vectors
2. [cyan]Similarity Computation[/cyan] - Find near-duplicate pairs
3. [cyan]Duplicate Removal[/cyan] - Keep one from each duplicate group
"""
    elif command == "cluster":
        overview = """[bold]Clustering Pipeline:[/bold]

1. [cyan]TF-IDF Vectorization[/cyan] - Convert documents to vectors
2. [cyan]LSA Dimensionality Reduction[/cyan] - Extract latent topics
3. [cyan]K-Means Clustering[/cyan] - Group similar documents
4. [cyan]Cluster Analysis[/cyan] - Identify cluster characteristics
"""
    else:
        overview = f"[bold]Processing Pipeline:[/bold] {command}"

    console.print(Panel(overview, title="[LEARN] Pipeline Overview", border_style="blue"))

    if explainer.interactive:
        explainer._pause()
