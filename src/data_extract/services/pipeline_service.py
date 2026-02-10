"""Core extraction pipeline service shared by CLI and API."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List

from data_extract.core.models import Chunk, Document
from data_extract.extract import get_extractor
from data_extract.output import OutputWriter


@dataclass
class PipelineFileResult:
    """Result details for one processed input file."""

    source_path: Path
    output_path: Path
    chunk_count: int
    stage_timings_ms: Dict[str, float] = field(default_factory=dict)


@dataclass
class PipelineFailure:
    """Failure details for one source file."""

    source_path: Path
    error_type: str
    error_message: str


@dataclass
class PipelineRunResult:
    """Aggregate processing result for a batch."""

    processed: List[PipelineFileResult] = field(default_factory=list)
    failed: List[PipelineFailure] = field(default_factory=list)
    skipped: List[Path] = field(default_factory=list)
    stage_totals_ms: Dict[str, float] = field(default_factory=dict)


class PipelineService:
    """Run extract -> normalize -> chunk -> optional semantic -> output."""

    def __init__(self) -> None:
        self.writer = OutputWriter()

    def process_files(
        self,
        files: Iterable[Path],
        output_dir: Path,
        output_format: str,
        chunk_size: int,
        include_semantic: bool = False,
        continue_on_error: bool = True,
    ) -> PipelineRunResult:
        """Process files and return per-file and aggregate details."""
        result = PipelineRunResult()
        output_dir.mkdir(parents=True, exist_ok=True)

        for file_path in files:
            try:
                file_result = self.process_file(
                    file_path=file_path,
                    output_dir=output_dir,
                    output_format=output_format,
                    chunk_size=chunk_size,
                    include_semantic=include_semantic,
                )
                result.processed.append(file_result)
                for stage, value in file_result.stage_timings_ms.items():
                    result.stage_totals_ms[stage] = result.stage_totals_ms.get(stage, 0.0) + value
            except Exception as exc:
                result.failed.append(
                    PipelineFailure(
                        source_path=file_path,
                        error_type=type(exc).__name__,
                        error_message=str(exc),
                    )
                )
                if not continue_on_error:
                    break

        return result

    def process_file(
        self,
        file_path: Path,
        output_dir: Path,
        output_format: str,
        chunk_size: int,
        include_semantic: bool = False,
    ) -> PipelineFileResult:
        """Run the full pipeline for a single file."""
        stage_timings_ms: Dict[str, float] = {}

        start = time.perf_counter()
        document = self._extract(file_path)
        stage_timings_ms["extract"] = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        normalized = self._normalize(document)
        stage_timings_ms["normalize"] = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        chunks = self._chunk(normalized, chunk_size)
        stage_timings_ms["chunk"] = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        semantic_chunks = self._semantic(chunks) if include_semantic else chunks
        stage_timings_ms["semantic"] = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        output_path = output_dir / f"{file_path.stem}.{output_format}"
        self.writer.write(semantic_chunks, output_path=output_path, format_type=output_format)
        stage_timings_ms["output"] = (time.perf_counter() - start) * 1000

        return PipelineFileResult(
            source_path=file_path,
            output_path=output_path,
            chunk_count=len(semantic_chunks),
            stage_timings_ms=stage_timings_ms,
        )

    @staticmethod
    def _extract(file_path: Path) -> Document:
        """Extract a file into a Document model using format-specific adapter."""
        adapter = get_extractor(file_path)
        return adapter.process(file_path)

    @staticmethod
    def _normalize(document: Document) -> Document:
        """Apply lightweight, deterministic text normalization."""
        text = document.text
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = "\n".join(line.strip() for line in text.split("\n"))
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return document.model_copy(update={"text": text})

    @staticmethod
    def _chunk(document: Document, chunk_size: int) -> List[Chunk]:
        """Chunk text by approximate token count (word windows)."""
        words = document.text.split()
        if not words:
            return [
                Chunk(
                    id=f"{document.id}_001",
                    text="",
                    document_id=document.id,
                    position_index=0,
                    token_count=0,
                    word_count=0,
                    entities=[],
                    section_context="",
                    quality_score=0.0,
                    readability_scores={},
                    metadata=document.metadata,
                )
            ]

        chunks: List[Chunk] = []
        step = max(1, chunk_size)

        for index, offset in enumerate(range(0, len(words), step), start=1):
            chunk_words = words[offset : offset + step]
            chunk_text = " ".join(chunk_words)
            coverage = min(1.0, len(chunk_words) / float(step))

            chunks.append(
                Chunk(
                    id=f"{document.id}_{index:03d}",
                    text=chunk_text,
                    document_id=document.id,
                    position_index=index - 1,
                    token_count=len(chunk_words),
                    word_count=len(chunk_words),
                    entities=[],
                    section_context="",
                    quality_score=coverage,
                    readability_scores={},
                    metadata=document.metadata,
                )
            )

        return chunks

    @staticmethod
    def _semantic(chunks: List[Chunk]) -> List[Chunk]:
        """Optional semantic stage hook.

        V1 keeps semantic enrichment lightweight and deterministic.
        """
        return chunks
