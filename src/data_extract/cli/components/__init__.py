"""CLI components for progress tracking, panels, and feedback.

This package provides UI components for the data-extract CLI:
- Progress tracking (progress bars, stage indicators)
- Rich panels (preflight check, quality dashboard)
- Feedback control (verbosity levels, error collection)

Story 5-3: Real-Time Progress Indicators and Feedback
"""

from .feedback import (
    ErrorCollector,
    ErrorInfo,
    VerbosityController,
    VerbosityLevel,
    get_console,
    reset_console,
)
from .panels import (
    PreflightPanel,
    PreflightResult,
    QualityDashboard,
    QualityMetrics,
)
from .progress import (
    FileProgress,
    PipelineProgress,
    PipelineStage,
    StageProgress,
)

__all__ = [
    # Progress components
    "PipelineProgress",
    "FileProgress",
    "PipelineStage",
    "StageProgress",
    # Panel components
    "PreflightPanel",
    "PreflightResult",
    "QualityDashboard",
    "QualityMetrics",
    # Feedback components
    "VerbosityController",
    "VerbosityLevel",
    "ErrorCollector",
    "ErrorInfo",
    "get_console",
    "reset_console",
]
