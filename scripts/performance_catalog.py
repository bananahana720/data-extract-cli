"""Shared performance test/catalog constants for scripts and automation."""

from __future__ import annotations

# Canonical module mapping used by validate_performance.py.
COMPONENT_TEST_MODULES: dict[str, tuple[str, ...]] = {
    "extract": (
        "test_extractor_benchmarks.py",
        "test_throughput.py",
    ),
    "normalize": ("test_quality_performance.py",),
    "chunk": (
        "test_chunk/test_chunking_latency.py",
        "test_chunk/test_entity_aware_performance.py",
        "test_chunk/test_memory_efficiency.py",
    ),
    "semantic": (
        "test_lsa_performance.py",
        "test_quality_performance.py",
        "test_summary_performance.py",
    ),
    "output": (
        "test_json_performance.py",
        "test_txt_performance.py",
        "test_pipeline_benchmarks.py",
        "test_cli_benchmarks.py",
    ),
    "api_runtime": ("test_api_queue_dispatch_perf.py",),
}


# Canonical suite selectors used by run_performance_suite.py.
RUN_PERFORMANCE_SUITE_NODEIDS: dict[str, tuple[str, ...]] = {
    "extractors": (
        "tests/performance/test_extractor_benchmarks.py::TestExtractorBenchmarks::test_txt_small_file_performance",
        "tests/performance/test_extractor_benchmarks.py::TestExtractorBenchmarks::test_excel_small_file_performance",
        "tests/performance/test_extractor_benchmarks.py::TestExtractorBenchmarks::test_pdf_small_file_performance",
    ),
    "pipeline": (
        "tests/performance/test_pipeline_benchmarks.py::TestPipelineBenchmarks::test_single_txt_pipeline_latency",
        "tests/performance/test_pipeline_benchmarks.py::TestPipelineBenchmarks::test_pipeline_json_vs_txt_output_latency",
        "tests/performance/test_pipeline_benchmarks.py::TestPipelineBenchmarks::test_batch_workers_improve_parallel_processing",
        "tests/performance/test_pipeline_benchmarks.py::TestPipelineBenchmarks::test_pipeline_profile_visibility_auto_vs_legacy",
    ),
    "cli": (
        "tests/performance/test_cli_benchmarks.py::TestSingleFilePerformance::test_cli_txt_extraction_performance",
        "tests/performance/test_cli_benchmarks.py::TestProgressDisplayOverhead::test_progress_vs_quiet_overhead",
        "tests/performance/test_cli_benchmarks.py::TestEncodingPerformance::test_unicode_heavy_content",
    ),
}


# Supported performance suite groups and defaults for run_performance_suite.py.
RUN_PERFORMANCE_SUITE_DEFAULT_SUITES: tuple[str, ...] = ("extractors", "pipeline", "cli")
RUN_PERFORMANCE_SUITE_ALL_SUITES: tuple[str, ...] = (
    *RUN_PERFORMANCE_SUITE_DEFAULT_SUITES,
    "api_runtime",
)


# API runtime load selectors consumed by run_performance_suite.py and validate_performance.py.
# Tuple schema: (<selector name>, <endpoint path or absolute URL>)
RUN_PERFORMANCE_SUITE_API_RUNTIME_SELECTORS: tuple[tuple[str, str], ...] = (
    ("health", "/api/v1/health"),
    ("health_detailed", "/api/v1/health?detailed=true"),
)


# Test selectors used to refresh all maintained baseline operations.
BASELINE_REFRESH_NODEIDS: tuple[str, ...] = (
    "tests/performance/test_extractor_benchmarks.py::TestExtractorBenchmarks",
    "tests/performance/test_cli_benchmarks.py",
)


# Baseline keys intentionally maintained by refresh automation.
ACTIVE_BASELINE_KEYS: tuple[str, ...] = (
    "txt_extract_small",
    "excel_extract_small",
    "pdf_small",
    "docx_extract_small",
    "pptx_extract_small",
    "cli_extract_txt",
    "cli_extract_pdf",
    "cli_batch_1workers",
    "cli_batch_4workers",
    "cli_batch_8workers",
    "cli_batch_16workers",
    "cli_stress_high_concurrency",
    "cli_progress_overhead",
    "cli_unicode_encoding",
)
