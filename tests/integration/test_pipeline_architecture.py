"""Integration tests for pipeline architecture.

Tests cover:
- End-to-end pipeline flow with mock stages
- Pipeline orchestrator chains stages correctly
- ProcessingContext passed through all stages
- ProcessingError handling (continue batch processing)
- CriticalError handling (halt processing)
- Individual stage execution standalone
"""

import pytest

pytestmark = [pytest.mark.P0, pytest.mark.integration]

from src.data_extract.core.exceptions import CriticalError, ProcessingError  # noqa: E402
from src.data_extract.core.models import ProcessingContext  # noqa: E402
from src.data_extract.core.pipeline import Pipeline  # noqa: E402


# Mock stages for integration testing
class Stage1StringLength:
    """Stage 1: Calculate string length."""

    def process(self, input_data: str, context: ProcessingContext) -> int:
        """Convert string to int (length)."""
        context.metrics.setdefault("stages", []).append("Stage1")
        if context.logger:
            context.logger.info("stage1_executed", input=input_data)
        return len(input_data)


class Stage2Double:
    """Stage 2: Double the number."""

    def process(self, input_data: int, context: ProcessingContext) -> int:
        """Double the input."""
        context.metrics.setdefault("stages", []).append("Stage2")
        if context.logger:
            context.logger.info("stage2_executed", input=input_data)
        return input_data * 2


class Stage3ToString:
    """Stage 3: Convert to string."""

    def process(self, input_data: int, context: ProcessingContext) -> str:
        """Convert int to string."""
        context.metrics.setdefault("stages", []).append("Stage3")
        if context.logger:
            context.logger.info("stage3_executed", input=input_data)
        return f"Result: {input_data}"


class StageWithProcessingError:
    """Stage that raises ProcessingError."""

    def process(self, input_data: str, context: ProcessingContext) -> str:
        """Raise ProcessingError for testing."""
        context.metrics.setdefault("stages", []).append("StageWithProcessingError")
        raise ProcessingError("Recoverable error in processing")


class StageWithCriticalError:
    """Stage that raises CriticalError."""

    def process(self, input_data: str, context: ProcessingContext) -> str:
        """Raise CriticalError for testing."""
        context.metrics.setdefault("stages", []).append("StageWithCriticalError")
        raise CriticalError("Unrecoverable critical error")


class StageAfterError:
    """Stage that runs after error stage."""

    def process(self, input_data: str, context: ProcessingContext) -> str:
        """Mark execution in metrics."""
        context.metrics.setdefault("stages", []).append("StageAfterError")
        return input_data


class TestPipelineOrchestration:
    """Test Pipeline class orchestrates stages correctly."""

    @pytest.mark.test_id("int-INT-001")
    def test_end_to_end_pipeline_flow(self):
        """Test Pipeline chains three stages correctly."""
        pipeline = Pipeline([Stage1StringLength(), Stage2Double(), Stage3ToString()])
        context = ProcessingContext(config={"mode": "test"})

        result = pipeline.process("hello", context)

        # Verify result: len("hello") = 5, 5 * 2 = 10, "Result: 10"
        assert result == "Result: 10"

        # Verify all stages executed in order
        assert context.metrics["stages"] == ["Stage1", "Stage2", "Stage3"]

    @pytest.mark.test_id("int-INT-002")
    def test_pipeline_with_logger(self):
        """Test Pipeline with structured logger in context."""
        import structlog  # noqa: E402

        logger = structlog.get_logger().bind(test="pipeline")
        pipeline = Pipeline([Stage1StringLength(), Stage2Double()])
        context = ProcessingContext(logger=logger)

        result = pipeline.process("test", context)

        # len("test") = 4, 4 * 2 = 8
        assert result == 8
        assert context.logger is not None

    @pytest.mark.test_id("int-INT-003")
    def test_pipeline_with_config(self):
        """Test Pipeline stages access config from context."""

        class ConfigReaderStage:
            def process(self, input_data: int, context: ProcessingContext) -> int:
                multiplier = context.config.get("multiplier", 1)
                return input_data * multiplier

        pipeline = Pipeline([ConfigReaderStage()])
        context = ProcessingContext(config={"multiplier": 5})

        result = pipeline.process(10, context)
        assert result == 50  # 10 * 5

    @pytest.mark.test_id("int-INT-004")
    def test_pipeline_metrics_accumulation(self):
        """Test Pipeline stages accumulate metrics in context."""
        pipeline = Pipeline([Stage1StringLength(), Stage2Double(), Stage3ToString()])
        context = ProcessingContext()
        context.metrics["processed_files"] = 0

        pipeline.process("data", context)

        # Metrics should accumulate
        assert "stages" in context.metrics
        assert len(context.metrics["stages"]) == 3
        assert context.metrics["processed_files"] == 0  # Unchanged (not modified by stages)

    @pytest.mark.test_id("int-INT-005")
    def test_individual_stage_standalone(self):
        """Test individual stage can execute standalone without Pipeline."""
        stage = Stage1StringLength()
        context = ProcessingContext()

        result = stage.process("standalone", context)

        assert result == 10  # len("standalone")
        assert context.metrics["stages"] == ["Stage1"]


class TestPipelineErrorHandling:
    """Test Pipeline error handling with ProcessingError and CriticalError."""

    @pytest.mark.test_id("int-INT-006")
    def test_processing_error_propagates(self):
        """Test ProcessingError propagates from pipeline stage."""
        pipeline = Pipeline([StageWithProcessingError()])
        context = ProcessingContext()

        with pytest.raises(ProcessingError) as exc_info:
            pipeline.process("data", context)

        assert "Recoverable error" in str(exc_info.value)
        assert context.metrics["stages"] == ["StageWithProcessingError"]

    @pytest.mark.test_id("int-INT-007")
    def test_critical_error_propagates(self):
        """Test CriticalError propagates from pipeline stage."""
        pipeline = Pipeline([StageWithCriticalError()])
        context = ProcessingContext()

        with pytest.raises(CriticalError) as exc_info:
            pipeline.process("data", context)

        assert "Unrecoverable" in str(exc_info.value)
        assert context.metrics["stages"] == ["StageWithCriticalError"]

    @pytest.mark.test_id("int-INT-008")
    def test_processing_error_halts_pipeline(self):
        """Test ProcessingError halts pipeline (subsequent stages don't run)."""
        pipeline = Pipeline([StageWithProcessingError(), StageAfterError()])
        context = ProcessingContext()

        with pytest.raises(ProcessingError):
            pipeline.process("data", context)

        # Only first stage should execute
        assert context.metrics["stages"] == ["StageWithProcessingError"]
        assert "StageAfterError" not in context.metrics["stages"]

    @pytest.mark.test_id("int-INT-009")
    def test_critical_error_halts_pipeline(self):
        """Test CriticalError halts pipeline (subsequent stages don't run)."""
        pipeline = Pipeline([StageWithCriticalError(), StageAfterError()])
        context = ProcessingContext()

        with pytest.raises(CriticalError):
            pipeline.process("data", context)

        # Only first stage should execute
        assert context.metrics["stages"] == ["StageWithCriticalError"]
        assert "StageAfterError" not in context.metrics["stages"]

    @pytest.mark.test_id("int-INT-010")
    def test_batch_processing_with_error_handling(self):
        """Test batch processing continues after ProcessingError (real-world pattern)."""
        pipeline = Pipeline([Stage1StringLength()])
        files = ["file1", "file2", "corrupted", "file4"]
        successful = []
        failed = []

        for file_data in files:
            context = ProcessingContext()
            try:
                # Simulate corrupted file raising error
                if file_data == "corrupted":
                    raise ProcessingError(f"Failed to process {file_data}")

                result = pipeline.process(file_data, context)
                successful.append((file_data, result))
            except ProcessingError as e:
                failed.append((file_data, str(e)))
                continue  # Continue with next file

        # Should process 3 successful files
        assert len(successful) == 3
        assert len(failed) == 1
        assert failed[0][0] == "corrupted"


class TestPipelineTypeContracts:
    """Test Pipeline type contracts between stages."""

    @pytest.mark.test_id("int-INT-011")
    def test_type_flow_str_to_int_to_str(self):
        """Test Pipeline flows types correctly: str → int → str."""
        pipeline = Pipeline([Stage1StringLength(), Stage2Double(), Stage3ToString()])
        context = ProcessingContext()

        # Input: str
        result = pipeline.process("pipeline", context)

        # Output: str (after int transformation)
        assert isinstance(result, str)
        assert result == "Result: 16"  # len("pipeline")=8, 8*2=16

    @pytest.mark.test_id("int-INT-012")
    def test_empty_pipeline_returns_input(self):
        """Test Pipeline with no stages returns input unchanged."""
        pipeline = Pipeline([])
        context = ProcessingContext()

        result = pipeline.process("unchanged", context)
        assert result == "unchanged"

    @pytest.mark.test_id("int-INT-013")
    def test_single_stage_pipeline(self):
        """Test Pipeline with single stage (edge case)."""
        pipeline = Pipeline([Stage1StringLength()])
        context = ProcessingContext()

        result = pipeline.process("single", context)
        assert result == 6  # len("single")


class TestProcessingContextIntegration:
    """Test ProcessingContext integration with Pipeline (AC-1.4.4)."""

    @pytest.mark.test_id("int-INT-014")
    def test_context_passed_through_all_stages(self):
        """Test ProcessingContext is accessible in all pipeline stages."""
        pipeline = Pipeline([Stage1StringLength(), Stage2Double(), Stage3ToString()])
        context = ProcessingContext(config={"test_key": "test_value"}, metrics={"initial": 0})

        pipeline.process("test", context)

        # All stages should have recorded execution
        assert len(context.metrics["stages"]) == 3
        # Initial metrics preserved
        assert context.metrics["initial"] == 0
        # Config preserved
        assert context.config["test_key"] == "test_value"

    @pytest.mark.test_id("int-INT-015")
    def test_context_config_accessible_all_stages(self):
        """Test all stages can read from ProcessingContext.config."""

        class ConfigReader1:
            def process(self, input_data: str, context: ProcessingContext) -> str:
                prefix = context.config.get("prefix", "")
                return f"{prefix}{input_data}"

        class ConfigReader2:
            def process(self, input_data: str, context: ProcessingContext) -> str:
                suffix = context.config.get("suffix", "")
                return f"{input_data}{suffix}"

        pipeline = Pipeline([ConfigReader1(), ConfigReader2()])
        context = ProcessingContext(config={"prefix": "[START]", "suffix": "[END]"})

        result = pipeline.process("DATA", context)
        assert result == "[START]DATA[END]"

    @pytest.mark.test_id("int-INT-016")
    def test_context_metrics_mutable(self):
        """Test ProcessingContext.metrics is mutable for accumulation."""

        class MetricsWriter:
            def process(self, input_data: int, context: ProcessingContext) -> int:
                context.metrics.setdefault("total", 0)
                context.metrics["total"] += input_data
                return input_data + 1

        pipeline = Pipeline([MetricsWriter(), MetricsWriter(), MetricsWriter()])
        context = ProcessingContext()

        result = pipeline.process(1, context)

        # Result: 1 -> 2 -> 3 -> 4
        assert result == 4
        # Metrics accumulated: 1 + 2 + 3 = 6
        assert context.metrics["total"] == 6
