"""Core extraction pipeline service shared by CLI and API."""

from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, cast

import structlog

from data_extract.core.models import Chunk, Document
from data_extract.extract import get_extractor
from data_extract.normalize.config import NormalizationConfig
from data_extract.normalize.normalizer import Normalizer
from data_extract.output import OutputWriter
from data_extract.output.organization import OrganizationStrategy
from data_extract.services.pathing import normalize_path


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
        self.logger = structlog.get_logger(__name__)
        self.normalizer: Normalizer | None = None

    def process_files(
        self,
        files: Iterable[Path],
        output_dir: Path,
        output_format: str,
        chunk_size: int,
        workers: int = 1,
        include_metadata: bool = False,
        per_chunk: bool = False,
        organize: bool = False,
        strategy: str | None = None,
        delimiter: str = "━━━ CHUNK {{n}} ━━━",
        include_semantic: bool = False,
        continue_on_error: bool = True,
        source_root: Path | None = None,
        pipeline_profile: str = "auto",
        allow_advanced_fallback: bool = True,
        output_file_override: Path | None = None,
    ) -> PipelineRunResult:
        """Process files and return per-file and aggregate details."""
        result = PipelineRunResult()
        output_dir.mkdir(parents=True, exist_ok=True)
        file_list = list(files)
        worker_count = max(1, int(workers))

        if worker_count <= 1 or len(file_list) <= 1:
            for file_path in file_list:
                try:
                    file_result = self.process_file(
                        file_path=file_path,
                        output_dir=output_dir,
                        output_format=output_format,
                        chunk_size=chunk_size,
                        include_metadata=include_metadata,
                        per_chunk=per_chunk,
                        organize=organize,
                        strategy=strategy,
                        delimiter=delimiter,
                        include_semantic=include_semantic,
                        source_root=source_root,
                        pipeline_profile=pipeline_profile,
                        allow_advanced_fallback=allow_advanced_fallback,
                        output_file_override=output_file_override,
                    )
                    result.processed.append(file_result)
                    for stage, value in file_result.stage_timings_ms.items():
                        result.stage_totals_ms[stage] = (
                            result.stage_totals_ms.get(stage, 0.0) + value
                        )
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

        # Process files in parallel when workers > 1. Each worker uses an isolated
        # PipelineService instance to avoid sharing mutable normalizer/writer state.
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = {
                executor.submit(
                    self._process_file_isolated,
                    file_path=file_path,
                    output_dir=output_dir,
                    output_format=output_format,
                    chunk_size=chunk_size,
                    include_metadata=include_metadata,
                    per_chunk=per_chunk,
                    organize=organize,
                    strategy=strategy,
                    delimiter=delimiter,
                    include_semantic=include_semantic,
                    source_root=source_root,
                    pipeline_profile=pipeline_profile,
                    allow_advanced_fallback=allow_advanced_fallback,
                    output_file_override=output_file_override,
                ): file_path
                for file_path in file_list
            }

            for future in as_completed(futures):
                file_path = futures[future]
                try:
                    file_result = future.result()
                    result.processed.append(file_result)
                    for stage, value in file_result.stage_timings_ms.items():
                        result.stage_totals_ms[stage] = (
                            result.stage_totals_ms.get(stage, 0.0) + value
                        )
                except Exception as exc:
                    result.failed.append(
                        PipelineFailure(
                            source_path=file_path,
                            error_type=type(exc).__name__,
                            error_message=str(exc),
                        )
                    )
                    if not continue_on_error:
                        for pending in futures:
                            if not pending.done():
                                pending.cancel()
                        break

        return result

    @staticmethod
    def _process_file_isolated(
        file_path: Path,
        output_dir: Path,
        output_format: str,
        chunk_size: int,
        include_metadata: bool,
        per_chunk: bool,
        organize: bool,
        strategy: str | None,
        delimiter: str,
        include_semantic: bool,
        source_root: Path | None,
        pipeline_profile: str,
        allow_advanced_fallback: bool,
        output_file_override: Path | None,
    ) -> PipelineFileResult:
        """Process one file with an isolated service instance for thread safety."""
        service = PipelineService()
        return service.process_file(
            file_path=file_path,
            output_dir=output_dir,
            output_format=output_format,
            chunk_size=chunk_size,
            include_metadata=include_metadata,
            per_chunk=per_chunk,
            organize=organize,
            strategy=strategy,
            delimiter=delimiter,
            include_semantic=include_semantic,
            source_root=source_root,
            pipeline_profile=pipeline_profile,
            allow_advanced_fallback=allow_advanced_fallback,
            output_file_override=output_file_override,
        )

    def process_file(
        self,
        file_path: Path,
        output_dir: Path,
        output_format: str,
        chunk_size: int,
        include_metadata: bool = False,
        per_chunk: bool = False,
        organize: bool = False,
        strategy: str | None = None,
        delimiter: str = "━━━ CHUNK {{n}} ━━━",
        include_semantic: bool = False,
        source_root: Path | None = None,
        pipeline_profile: str = "auto",
        allow_advanced_fallback: bool = True,
        output_file_override: Path | None = None,
    ) -> PipelineFileResult:
        """Run the full pipeline for a single file."""
        stage_timings_ms: Dict[str, float] = {}
        use_advanced = self._should_use_advanced_pipeline(
            include_semantic=include_semantic,
            pipeline_profile=pipeline_profile,
            file_path=file_path,
        )

        start = time.perf_counter()
        document = self._extract(file_path)
        stage_timings_ms["extract"] = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        if use_advanced:
            try:
                normalized = self._normalize_advanced(document)
            except Exception as exc:
                if not allow_advanced_fallback:
                    raise
                self.logger.warning(
                    "advanced_normalize_fallback",
                    source_path=str(file_path),
                    error=str(exc),
                )
                normalized = self._normalize(document)
                use_advanced = False
        else:
            normalized = self._normalize(document)
        stage_timings_ms["normalize"] = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        if use_advanced:
            try:
                chunks = self._chunk_advanced(normalized, chunk_size)
                if not chunks:
                    # Compatibility fallback: CLI integration expects a deterministic
                    # placeholder chunk for empty/near-empty documents so output files
                    # are still emitted in TXT concatenated/per-chunk modes.
                    chunks = self._chunk(normalized, chunk_size)
                    use_advanced = False
            except Exception as exc:
                if not allow_advanced_fallback:
                    raise
                self.logger.warning(
                    "advanced_chunk_fallback",
                    source_path=str(file_path),
                    error=str(exc),
                )
                chunks = self._chunk(normalized, chunk_size)
        else:
            chunks = self._chunk(normalized, chunk_size)
        stage_timings_ms["chunk"] = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        semantic_chunks = self._semantic(chunks) if include_semantic else chunks
        stage_timings_ms["semantic"] = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        if output_file_override is not None:
            output_path = output_file_override
        elif per_chunk or organize:
            output_path = output_dir
        else:
            output_path = self._resolve_output_path(
                file_path=file_path,
                output_dir=output_dir,
                output_format=output_format,
                source_root=source_root,
            )
        strategy_enum = OrganizationStrategy(strategy) if strategy else None
        formatter_kwargs: Dict[str, object] = {
            "include_metadata": include_metadata,
            "delimiter": delimiter,
        }
        if output_format == "json":
            formatter_kwargs["write_bom"] = False
        self.writer.write(
            semantic_chunks,
            output_path=output_path,
            format_type=output_format,
            per_chunk=per_chunk,
            organize=organize,
            strategy=strategy_enum,
            **formatter_kwargs,
        )
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

    def _normalize_advanced(self, document: Document) -> Document:
        """Apply advanced normalizer pipeline for semantic-ready processing."""
        from data_extract.core.models import ProcessingContext

        if self.normalizer is None:
            self.normalizer = Normalizer(NormalizationConfig())

        context = ProcessingContext(config={}, logger=self.logger, metrics={})
        return self.normalizer.process(document, context)

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

    def _chunk_advanced(self, document: Document, chunk_size: int) -> List[Chunk]:
        """Run semantic boundary-aware chunking engine."""
        from data_extract.chunk.engine import ChunkingConfig, ChunkingEngine
        from data_extract.core.models import ProcessingContext

        engine = ChunkingEngine(
            config=ChunkingConfig(
                chunk_size=max(1, int(chunk_size)),
                overlap_pct=0.15,
                entity_aware=False,
                quality_enrichment=True,
            )
        )
        context = ProcessingContext(config={}, logger=self.logger, metrics={})
        return cast(List[Chunk], engine.process(document, context))

    @staticmethod
    def _semantic(chunks: List[Chunk]) -> List[Chunk]:
        """Optional semantic stage hook.

        V1 keeps semantic enrichment lightweight and deterministic.
        """
        return chunks

    @staticmethod
    def _should_use_advanced_pipeline(
        include_semantic: bool,
        pipeline_profile: str,
        file_path: Path,
    ) -> bool:
        profile = str(pipeline_profile or "auto").lower()
        if profile == "advanced":
            return True
        if profile == "legacy":
            return False
        advanced_extensions = {
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".tif",
            ".tiff",
            ".bmp",
            ".gif",
            ".webp",
        }
        return include_semantic or file_path.suffix.lower() in advanced_extensions

    @staticmethod
    def _resolve_output_path(
        file_path: Path,
        output_dir: Path,
        output_format: str,
        source_root: Path | None,
    ) -> Path:
        """Map source path to stable output path while avoiding stem collisions."""
        if source_root is None:
            relative = Path(file_path.name)
        else:
            normalized_root = normalize_path(source_root)
            normalized_source = normalize_path(file_path)
            try:
                relative = normalized_source.relative_to(normalized_root)
            except ValueError:
                relative = Path(file_path.name)

        output_path = output_dir / relative.with_suffix(f".{output_format}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
