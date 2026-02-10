"""
Performance benchmarking tests for the Data Extractor Tool.

This package contains systematic performance benchmarks for:
- Extractors (DOCX, PDF, PPTX, XLSX, TXT)
- Processors (Context, Metadata, Quality)
- Formatters (JSON, Markdown, Chunked)
- Pipeline orchestration

Run with: pytest tests/performance/ -v -m performance

To establish baselines:
    pytest tests/performance/ -v -m performance --tb=short

To skip performance tests in regular runs:
    pytest tests/ -v -m "not performance"
"""
