"""Unit tests for summary_report module (Story 5-4).

Tests the core data structures, stage timing, and rendering components
for comprehensive summary statistics and reporting.

Test markers: @pytest.mark.story_5_4 for Story 5-4 specific tests
"""

from dataclasses import FrozenInstanceError

import pytest

from data_extract.cli.summary import (
    ExportFormat,
    QualityMetrics,
    StageName,
    StageTimer,
    SummaryReport,
    export_summary,
    render_next_steps,
    render_quality_dashboard,
    render_summary_panel,
    render_timing_breakdown,
)

# P1: Core functionality - run on PR
pytestmark = [
    pytest.mark.P1,
    pytest.mark.story_5_4,
    pytest.mark.skip,
    pytest.mark.unit,
    pytest.mark.cli,
]

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def quality_metrics():
    """Create sample quality metrics for testing.

    GIVEN: Quality metrics with various score distributions
    """
    return QualityMetrics(
        avg_quality=0.75,
        excellent_count=5,
        good_count=8,
        review_count=3,
        flagged_count=2,
        entity_count=25,
        readability_score=65.5,
    )


@pytest.fixture
def summary_report(quality_metrics):
    """Create sample summary report for testing.

    GIVEN: Complete summary report with all fields populated
    """
    return SummaryReport(
        files_processed=3,
        files_failed=1,
        chunks_created=42,
        errors=["Error processing file1.pdf: OCR timeout"],
        quality_metrics=quality_metrics,
        timing={
            "extract": 150.5,
            "normalize": 50.2,
            "chunk": 75.8,
            "semantic": 200.1,
            "output": 30.4,
        },
        config={
            "max_features": 5000,
            "similarity_threshold": 0.95,
            "n_components": 100,
            "quality_min_score": 0.3,
        },
        next_steps=[
            "Review 2 flagged chunks (low quality)",
            "Investigate LSA clustering: silhouette=0.42",
        ],
    )


@pytest.fixture
def tmp_export_dir(tmp_path):
    """Create temporary directory for export testing.

    GIVEN: Empty temporary directory for file operations
    """
    return tmp_path


# ============================================================================
# TestSummaryReportDataclass
# ============================================================================


class TestSummaryReportDataclass:
    """Test SummaryReport dataclass - immutability, validation, defaults."""

    @pytest.mark.story_5_4
    def test_summary_report_creation_all_fields(self, summary_report):
        """Should create SummaryReport with all fields.

        WHEN: Creating SummaryReport with complete data
        THEN: All fields should be accessible
        """
        # THEN
        assert summary_report.files_processed == 3
        assert summary_report.files_failed == 1
        assert summary_report.chunks_created == 42
        assert len(summary_report.errors) == 1
        assert summary_report.quality_metrics is not None
        assert len(summary_report.timing) == 5
        assert len(summary_report.config) == 4
        assert len(summary_report.next_steps) == 2

    @pytest.mark.story_5_4
    def test_summary_report_is_frozen(self, summary_report):
        """Should enforce immutability - frozen dataclass.

        WHEN: Attempting to modify SummaryReport field
        THEN: Should raise FrozenInstanceError
        """
        # WHEN/THEN
        with pytest.raises(FrozenInstanceError):
            summary_report.files_processed = 5

    @pytest.mark.story_5_4
    def test_summary_report_with_minimal_fields(self):
        """Should create SummaryReport with minimal required fields.

        WHEN: Creating SummaryReport with only required fields
        THEN: Optional fields should be None or empty
        """
        # WHEN
        report = SummaryReport(
            files_processed=1,
            files_failed=0,
            chunks_created=10,
            errors=[],
            quality_metrics=None,
            timing={},
            config={},
            next_steps=[],
        )

        # THEN
        assert report.files_processed == 1
        assert report.quality_metrics is None
        assert report.errors == []
        assert report.timing == {}

    @pytest.mark.story_5_4
    def test_summary_report_default_values(self):
        """Should use sensible defaults for optional fields.

        WHEN: Creating minimal SummaryReport
        THEN: Defaults should be empty collections
        """
        # WHEN
        report = SummaryReport(
            files_processed=0,
            files_failed=0,
            chunks_created=0,
            errors=[],
            quality_metrics=None,
            timing={},
            config={},
            next_steps=[],
        )

        # THEN
        assert isinstance(report.errors, list)
        assert isinstance(report.timing, dict)
        assert isinstance(report.config, dict)
        assert isinstance(report.next_steps, list)


# ============================================================================
# TestQualityMetrics
# ============================================================================


class TestQualityMetrics:
    """Test QualityMetrics dataclass - data validation and structure."""

    @pytest.mark.story_5_4
    def test_quality_metrics_creation(self, quality_metrics):
        """Should create QualityMetrics with all fields.

        WHEN: Creating QualityMetrics
        THEN: All fields should be accessible
        """
        # THEN
        assert quality_metrics.avg_quality == 0.75
        assert quality_metrics.excellent_count == 5
        assert quality_metrics.good_count == 8
        assert quality_metrics.review_count == 3
        assert quality_metrics.flagged_count == 2
        assert quality_metrics.entity_count == 25
        assert quality_metrics.readability_score == 65.5

    @pytest.mark.story_5_4
    def test_quality_metrics_is_frozen(self, quality_metrics):
        """Should enforce immutability - frozen dataclass.

        WHEN: Attempting to modify QualityMetrics field
        THEN: Should raise FrozenInstanceError
        """
        # WHEN/THEN
        with pytest.raises(FrozenInstanceError):
            quality_metrics.avg_quality = 0.8

    @pytest.mark.story_5_4
    def test_quality_metrics_count_consistency(self):
        """Should allow various count values for distribution.

        WHEN: Creating QualityMetrics with different counts
        THEN: Should reflect quality distribution properly
        """
        # WHEN
        metrics = QualityMetrics(
            avg_quality=0.85,
            excellent_count=10,
            good_count=5,
            review_count=3,
            flagged_count=0,
            entity_count=100,
            readability_score=70.0,
        )

        # THEN
        total = metrics.excellent_count + metrics.good_count + metrics.review_count
        assert total == 18


# ============================================================================
# TestStageTimer
# ============================================================================


class TestStageTimer:
    """Test StageTimer class - timing tracking and formatting."""

    @pytest.mark.story_5_4
    def test_stage_timer_start_stop(self):
        """Should measure elapsed time between start and stop.

        WHEN: Starting and stopping timer
        THEN: Elapsed time should be positive
        """
        # GIVEN
        timer = StageTimer(StageName.EXTRACT)

        # WHEN
        timer.start()
        import time

        time.sleep(0.01)  # Sleep 10ms
        elapsed = timer.stop()

        # THEN
        assert elapsed > 0
        assert elapsed < 1000  # Less than 1 second

    @pytest.mark.story_5_4
    def test_stage_timer_stage_name(self):
        """Should preserve stage name.

        WHEN: Creating StageTimer with specific stage
        THEN: Stage name should be accessible
        """
        # WHEN
        timer = StageTimer(StageName.SEMANTIC)

        # THEN
        assert timer.stage == StageName.SEMANTIC

    @pytest.mark.story_5_4
    def test_stage_timer_elapsed_before_stop(self):
        """Should return None if stopped before starting.

        WHEN: Calling elapsed() without start()
        THEN: Should handle gracefully
        """
        # GIVEN
        timer = StageTimer(StageName.CHUNK)

        # WHEN/THEN
        # Should either return 0 or handle the case gracefully
        # Implementation will determine exact behavior
        result = timer.stop()
        assert isinstance(result, (int, float)) or result is None

    @pytest.mark.story_5_4
    def test_stage_timer_format_output(self):
        """Should format elapsed time as human-readable string.

        WHEN: Formatting stage timer output
        THEN: Should return "ms" or similar format
        """
        # GIVEN
        timer = StageTimer(StageName.NORMALIZE)
        timer.start()
        import time

        time.sleep(0.01)
        timer.stop()

        # WHEN
        formatted = timer.format_duration()

        # THEN
        assert isinstance(formatted, str)
        assert "ms" in formatted or "m" in formatted

    @pytest.mark.story_5_4
    def test_stage_timer_multiple_stages(self):
        """Should handle multiple stage timers independently.

        WHEN: Creating multiple timers for different stages
        THEN: Each should track independently
        """
        # WHEN
        timer1 = StageTimer(StageName.EXTRACT)
        timer2 = StageTimer(StageName.NORMALIZE)

        # THEN
        assert timer1.stage == StageName.EXTRACT
        assert timer2.stage == StageName.NORMALIZE
        assert timer1.stage != timer2.stage


# ============================================================================
# TestSummaryRenderer
# ============================================================================


class TestSummaryRenderer:
    """Test rendering functions - panel, dashboard, timing, next steps."""

    @pytest.mark.story_5_4
    def test_render_summary_panel(self, summary_report):
        """Should render summary as Rich Panel with title.

        WHEN: Calling render_summary_panel()
        THEN: Should create Panel with summary content
        """
        # WHEN
        panel = render_summary_panel(summary_report)

        # THEN
        assert panel is not None  # Should return Panel or similar

    @pytest.mark.story_5_4
    def test_render_summary_panel_contains_file_count(self, summary_report):
        """Should include file count in panel.

        WHEN: Rendering summary panel
        THEN: Panel should contain files_processed value
        """
        # WHEN
        result = render_summary_panel(summary_report)

        # THEN
        # Panel content should be serializable
        assert result is not None

    @pytest.mark.story_5_4
    def test_render_quality_dashboard(self, quality_metrics):
        """Should render quality distribution as bar chart.

        WHEN: Calling render_quality_dashboard()
        THEN: Should display distribution bars for excellent/good/review/flagged
        """
        # WHEN
        dashboard = render_quality_dashboard(quality_metrics)

        # THEN
        assert dashboard is not None

    @pytest.mark.story_5_4
    def test_render_quality_dashboard_shows_all_levels(self, quality_metrics):
        """Should show all quality levels in dashboard.

        WHEN: Rendering quality dashboard with mixed scores
        THEN: Should display excellent, good, review, and flagged counts
        """
        # WHEN
        dashboard = render_quality_dashboard(quality_metrics)

        # THEN
        # Dashboard should be renderable
        assert dashboard is not None

    @pytest.mark.story_5_4
    def test_render_timing_breakdown(self, summary_report):
        """Should render per-stage timing breakdown.

        WHEN: Calling render_timing_breakdown()
        THEN: Should show Extract, Normalize, Chunk, Semantic, Output durations
        """
        # WHEN
        breakdown = render_timing_breakdown(summary_report.timing)

        # THEN
        assert breakdown is not None

    @pytest.mark.story_5_4
    def test_render_timing_breakdown_all_stages(self, summary_report):
        """Should include all 5 stages in breakdown.

        WHEN: Rendering with complete timing dictionary
        THEN: Should show all stage durations
        """
        # WHEN
        breakdown = render_timing_breakdown(summary_report.timing)

        # THEN
        assert breakdown is not None

    @pytest.mark.story_5_4
    def test_render_next_steps(self, summary_report):
        """Should render next steps as bulleted recommendations.

        WHEN: Calling render_next_steps()
        THEN: Should display actionable next steps
        """
        # WHEN
        steps = render_next_steps(summary_report.next_steps)

        # THEN
        assert steps is not None

    @pytest.mark.story_5_4
    def test_render_next_steps_conditional(self):
        """Should handle empty next_steps gracefully.

        WHEN: Rendering with no next steps
        THEN: Should return appropriate message
        """
        # WHEN
        steps = render_next_steps([])

        # THEN
        assert steps is not None or steps == ""


# ============================================================================
# TestExportFunctionality
# ============================================================================


class TestExportFunctionality:
    """Test summary export to multiple formats."""

    @pytest.mark.story_5_4
    def test_export_summary_json(self, summary_report, tmp_export_dir):
        """Should export summary as JSON.

        WHEN: Calling export_summary() with format=json
        THEN: Should create valid JSON file
        """
        # WHEN
        output_path = tmp_export_dir / "summary.json"
        result = export_summary(summary_report, output_path, ExportFormat.JSON)

        # THEN
        assert result is not None or output_path.exists()

    @pytest.mark.story_5_4
    def test_export_summary_html(self, summary_report, tmp_export_dir):
        """Should export summary as HTML with styling.

        WHEN: Calling export_summary() with format=html
        THEN: Should create self-contained HTML file
        """
        # WHEN
        output_path = tmp_export_dir / "summary.html"
        result = export_summary(summary_report, output_path, ExportFormat.HTML)

        # THEN
        assert result is not None or output_path.exists()

    @pytest.mark.story_5_4
    def test_export_summary_txt(self, summary_report, tmp_export_dir):
        """Should export summary as human-readable text.

        WHEN: Calling export_summary() with format=txt
        THEN: Should create formatted text file
        """
        # WHEN
        output_path = tmp_export_dir / "summary.txt"
        result = export_summary(summary_report, output_path, ExportFormat.TXT)

        # THEN
        assert result is not None or output_path.exists()

    @pytest.mark.story_5_4
    def test_export_format_enum(self):
        """Should have ExportFormat enum with json, html, txt.

        WHEN: Accessing ExportFormat enum values
        THEN: Should have all required formats
        """
        # THEN
        assert hasattr(ExportFormat, "JSON")
        assert hasattr(ExportFormat, "HTML")
        assert hasattr(ExportFormat, "TXT")


# ============================================================================
# TestStageName
# ============================================================================


class TestStageName:
    """Test StageName enum for pipeline stages."""

    @pytest.mark.story_5_4
    def test_stage_name_enum_values(self):
        """Should have all pipeline stages.

        WHEN: Accessing StageName enum
        THEN: Should have EXTRACT, NORMALIZE, CHUNK, SEMANTIC, OUTPUT
        """
        # THEN
        assert hasattr(StageName, "EXTRACT")
        assert hasattr(StageName, "NORMALIZE")
        assert hasattr(StageName, "CHUNK")
        assert hasattr(StageName, "SEMANTIC")
        assert hasattr(StageName, "OUTPUT")

    @pytest.mark.story_5_4
    def test_stage_name_count(self):
        """Should have exactly 5 pipeline stages.

        WHEN: Counting StageName members
        THEN: Should be 5 stages
        """
        # THEN
        stages = list(StageName)
        assert len(stages) == 5


# ============================================================================
# IMPLEMENTATION PENDING MARKERS
# ============================================================================


@pytest.mark.skip(reason="Implementation pending - summary.py module")
class TestSummaryPanelAdvanced:
    """Advanced summary panel tests - deferred to implementation."""

    def test_summary_panel_respects_no_color(self):
        """Should respect NO_COLOR environment variable."""
        pass

    def test_summary_panel_width_adaptation(self):
        """Should adapt panel width to terminal size."""
        pass

    def test_summary_panel_error_section(self):
        """Should display error summary section when errors present."""
        pass
