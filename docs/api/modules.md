# API Modules Overview

## Module Index

### `cli.__init__`
_CLI module for data extraction tool.

Provides command-line interface for:
- Extract: Single file ex..._
- **Classes:** 0
- **Functions:** 0

### `cli.__main__`
_CLI entry point for python -m cli execution.

This module enables the CLI to be run as:
    python -..._
- **Classes:** 0
- **Functions:** 0

### `cli.commands`
_CLI Command Implementations.

Implements all CLI commands:
- extract: Single file extraction
- batch..._
- **Classes:** 0
- **Functions:** 12

### `cli.main`
_Main CLI Entry Point for Data Extraction Tool.

Provides command-line interface using Click framewor..._
- **Classes:** 0
- **Functions:** 3

### `cli.progress_display`
_CLI Progress Display Module.

Provides Rich-based progress visualization for file extraction operati..._
- **Classes:** 2
- **Functions:** 2

### `core.__init__`
_Core module - Foundation data models and interfaces.

This module defines the contracts that all oth..._
- **Classes:** 0
- **Functions:** 0

### `core.interfaces`
_Core interface contracts for the extraction system.

These abstract base classes define the contract..._
- **Classes:** 4
- **Functions:** 0

### `core.models`
_Core data models for the extraction system.

These are the foundation data structures that flow thro..._
- **Classes:** 11
- **Functions:** 0

### `data_extract.__init__`
_Data Extraction Tool - Enterprise document processing pipeline.

This package provides a modular pip..._
- **Classes:** 0
- **Functions:** 0

### `data_extract.chunk.__init__`
_Semantic chunking pipeline stage with lazy imports.

Avoid importing heavy dependencies (spaCy, text..._
- **Classes:** 0
- **Functions:** 1

### `data_extract.chunk.engine`
_Semantic boundary-aware chunking engine.

This module implements the core chunking logic for RAG-opt..._
- **Classes:** 2
- **Functions:** 0

### `data_extract.chunk.entity_preserver`
_Entity-aware boundary detection for semantic chunking.

This module implements entity preservation l..._
- **Classes:** 2
- **Functions:** 0

### `data_extract.chunk.metadata_enricher`
_Metadata enrichment component for chunk quality scoring (Story 3.3).

Implements MetadataEnricher cl..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.chunk.models`
_Chunk data models (re-exported from core for compatibility).

Story 3.1 uses Chunk model from core/m..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.chunk.quality`
_Quality scoring for chunks (Story 3.3).

Implements QualityScore dataclass for comprehensive chunk q..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.chunk.sentence_segmenter`
_Sentence segmentation wrapper for chunking engine.

Wraps the spaCy-based sentence boundary detectio..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.cli`
_CLI entry point for data-extract command.

This is a minimal implementation for Story 3.5 UAT valida..._
- **Classes:** 0
- **Functions:** 4

### `data_extract.config.__init__`
_Configuration management.

Epic 5 will implement configuration cascade system._
- **Classes:** 0
- **Functions:** 0

### `data_extract.core.__init__`
_Core data models and pipeline architecture.

Exports:
- EntityType: Enum for audit domain entity typ..._
- **Classes:** 0
- **Functions:** 0

### `data_extract.core.exceptions`
_Exception hierarchy for data extraction pipeline.

This module defines a consistent exception hierar..._
- **Classes:** 6
- **Functions:** 0

### `data_extract.core.models`
_Core data models for the data extraction pipeline.

This module defines Pydantic v2 models for pipel..._
- **Classes:** 13
- **Functions:** 0

### `data_extract.core.pipeline`
_Pipeline architecture for modular data processing.

This module defines the protocol-based pipeline ..._
- **Classes:** 2
- **Functions:** 0

### `data_extract.extract.__init__`
_Extractor adapters and registry.

This module provides the factory pattern for selecting the appropr..._
- **Classes:** 0
- **Functions:** 2

### `data_extract.extract.adapter`
_Adapter pattern for brownfield-to-greenfield extractor integration.

This module implements the adap..._
- **Classes:** 2
- **Functions:** 0

### `data_extract.extract.csv`
_CSV extractor adapter.

Wraps brownfield CSVExtractor and converts output to greenfield Document mod..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.extract.docx`
_DOCX extractor adapter.

Wraps brownfield DocxExtractor and converts output to greenfield Document m..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.extract.excel`
_Excel extractor adapter.

Wraps brownfield ExcelExtractor and converts output to greenfield Document..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.extract.pdf`
_PDF extractor adapter.

Wraps brownfield PdfExtractor and converts output to greenfield Document mod..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.extract.pptx`
_PPTX extractor adapter.

Wraps brownfield PptxExtractor and converts output to greenfield Document m..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.extract.txt`
_Text file extractor adapter.

Wraps brownfield TextFileExtractor and converts output to greenfield D..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.normalize.__init__`
_Text normalization pipeline stage.

This module contains text cleaning and normalization processors:..._
- **Classes:** 0
- **Functions:** 0

### `data_extract.normalize.cleaning`
_Text cleaning and artifact removal.

This module implements the TextCleaner class for removing OCR a..._
- **Classes:** 2
- **Functions:** 0

### `data_extract.normalize.config`
_Normalization configuration models and loaders.

This module defines configuration for text normaliz..._
- **Classes:** 1
- **Functions:** 2

### `data_extract.normalize.entities`
_Entity normalization for audit domain.

This module provides entity recognition, standardization, an..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.normalize.metadata`
_Metadata enrichment module for Story 2.6.

This module provides metadata enrichment functionality fo..._
- **Classes:** 1
- **Functions:** 4

### `data_extract.normalize.normalizer`
_Normalizer orchestrator for text normalization pipeline.

This module implements the main Normalizer..._
- **Classes:** 2
- **Functions:** 0

### `data_extract.normalize.schema`
_Schema standardization for document type detection and transformation.

This module implements docum..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.normalize.validation`
_OCR confidence scoring and quality validation for extracted documents.

This module implements OCR c..._
- **Classes:** 1
- **Functions:** 0

### `data_extract.output.__init__`
_Output module for data extraction pipeline.

This module provides formatters and organization strate..._
- **Classes:** 0
- **Functions:** 0

### `data_extract.output.formatters.__init__`
_Output formatters for different file formats._
- **Classes:** 0
- **Functions:** 0

### `data_extract.output.formatters.base`
_Base formatter interface and common functionality._
- **Classes:** 2
- **Functions:** 0

### `data_extract.output.formatters.csv_formatter`
_CSV formatter for chunk output._
- **Classes:** 1
- **Functions:** 0

### `data_extract.output.formatters.json_formatter`
_JSON formatter for chunk output._
- **Classes:** 1
- **Functions:** 0

### `data_extract.output.formatters.txt_formatter`
_Plain text formatter for chunk output._
- **Classes:** 1
- **Functions:** 0

### `data_extract.output.organization`
_Output organization strategies for chunk files._
- **Classes:** 3
- **Functions:** 0

### `data_extract.output.utils`
_Utility functions for output formatting._
- **Classes:** 0
- **Functions:** 3

### `data_extract.output.validation.__init__`
_Validation modules for output formatting._
- **Classes:** 0
- **Functions:** 0

### `data_extract.output.validation.csv_parser`
_CSV parser validation module._
- **Classes:** 1
- **Functions:** 1

### `data_extract.output.writer`
_Output writer for coordinating formatters and organization._
- **Classes:** 1
- **Functions:** 0

### `data_extract.semantic.__init__`
_Semantic analysis pipeline stage.

This module will contain similarity and quality analysis:
- TF-ID..._
- **Classes:** 0
- **Functions:** 0

### `data_extract.utils.__init__`
_Shared utilities and helpers._
- **Classes:** 0
- **Functions:** 0

### `data_extract.utils.nlp`
_NLP utilities for text processing using spaCy.

This module provides sentence boundary detection and..._
- **Classes:** 0
- **Functions:** 1

### `extractors.__init__`
_Format-specific extractors for various document types.

This package contains extractors for differe..._
- **Classes:** 0
- **Functions:** 0

### `extractors.csv_extractor`
_CSV Extractor - CSV/TSV File Extraction

Extracts content from CSV/TSV files with support for:
- Aut..._
- **Classes:** 1
- **Functions:** 0

### `extractors.docx_extractor`
_DOCX Extractor - Microsoft Word Document Extraction

This is a SPIKE implementation focused on getti..._
- **Classes:** 1
- **Functions:** 0

### `extractors.excel_extractor`
_Excel Extractor - Microsoft Excel Workbook Extraction

Extracts content from Excel workbooks (.xlsx,..._
- **Classes:** 1
- **Functions:** 0

### `extractors.pdf_extractor`
_PDF Extractor - PDF Document Extraction

Extracts content from PDF files with native text extraction..._
- **Classes:** 1
- **Functions:** 0

### `extractors.pptx_extractor`
_PowerPoint (PPTX) Extractor - Microsoft PowerPoint Presentation Extraction

Extracts content from Po..._
- **Classes:** 1
- **Functions:** 0

### `extractors.txt_extractor`
_Plain Text Extractor - Extract content from text files.

Supports .txt, .md, and .log files with par..._
- **Classes:** 1
- **Functions:** 1

### `formatters.__init__`
_Output formatters for the extraction system.

Formatters convert ProcessingResult into AI-ready form..._
- **Classes:** 0
- **Functions:** 0

### `formatters.chunked_text_formatter`
_ChunkedTextFormatter - Convert ProcessingResult to token-limited text chunks.

This formatter produc..._
- **Classes:** 1
- **Functions:** 0

### `formatters.json_formatter`
_JsonFormatter - Convert ProcessingResult to hierarchical JSON.

This formatter produces structured J..._
- **Classes:** 1
- **Functions:** 0

### `formatters.markdown_formatter`
_MarkdownFormatter - Convert ProcessingResult to human-readable Markdown.

This formatter produces cl..._
- **Classes:** 1
- **Functions:** 0

### `infrastructure.__init__`
_Infrastructure components for the extraction system.

This package provides cross-cutting concerns l..._
- **Classes:** 0
- **Functions:** 0

### `infrastructure.config_manager`
_Configuration Manager - Centralized Configuration System

Provides centralized configuration managem..._
- **Classes:** 2
- **Functions:** 0

### `infrastructure.error_handler`
_Error Handling Infrastructure for Data Extraction System.

Provides standardized error handling with..._
- **Classes:** 12
- **Functions:** 0

### `infrastructure.logging_framework`
_Logging framework for structured logging with performance timing.

Provides:
- Structured JSON loggi..._
- **Classes:** 1
- **Functions:** 5

### `infrastructure.progress_tracker`
_Progress Tracking Infrastructure for Data Extraction System.

Provides progress reporting for long-r..._
- **Classes:** 1
- **Functions:** 0

### `pipeline.__init__`
_Pipeline Package - Orchestrates Extraction Workflow.

This package provides the main pipeline orches..._
- **Classes:** 0
- **Functions:** 0

### `pipeline.batch_processor`
_BatchProcessor - Parallel File Processing for Large Batches.

This module provides parallel batch pr..._
- **Classes:** 1
- **Functions:** 0

### `pipeline.extraction_pipeline`
_ExtractionPipeline - Main Pipeline Orchestrator.

This module implements the main extraction pipelin..._
- **Classes:** 1
- **Functions:** 0

### `processors.__init__`
_Content processors for enriching extracted data.

Processors add value to raw extracted content:
- C..._
- **Classes:** 0
- **Functions:** 0

### `processors.context_linker`
_ContextLinker Processor - Build Hierarchical Document Structure

This processor creates a tree struc..._
- **Classes:** 1
- **Functions:** 0

### `processors.metadata_aggregator`
_MetadataAggregator Processor - Compute Statistics and Extract Entities

This processor computes docu..._
- **Classes:** 1
- **Functions:** 0

### `processors.quality_validator`
_QualityValidator Processor - Score Extraction Quality

This processor validates extraction quality b..._
- **Classes:** 1
- **Functions:** 0
