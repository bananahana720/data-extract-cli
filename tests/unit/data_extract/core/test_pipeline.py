"""Tests for core.pipeline module.

Test Coverage:
- Protocol compliance: PipelineStage protocol implementation verification
- Single stage execution: Pipeline with one stage processes correctly
- Multi-stage chaining: Output flows from stage N to stage N+1
- Empty pipeline: Pipeline with no stages returns input unchanged
- Context propagation: ProcessingContext passed to all stages
- Error propagation: Exceptions bubble up from stages
- Determinism: Same input produces same output
- Type safety: Generic type parameters work correctly
"""

import pytest

from data_extract.core.models import ProcessingContext
from data_extract.core.pipeline import Pipeline

pytestmark = [pytest.mark.P0, pytest.mark.unit]


# Mock stages for testing
class StringToIntStage:
    """Mock stage: Convert string to int (string length)."""

    def process(self, input_data: str, context: ProcessingContext) -> int:
        """Return length of input string."""
        context.metrics.setdefault("stages_executed", []).append("StringToInt")
        return len(input_data)


class IntToFloatStage:
    """Mock stage: Convert int to float (multiply by 1.5)."""

    def process(self, input_data: int, context: ProcessingContext) -> float:
        """Multiply input by 1.5."""
        context.metrics.setdefault("stages_executed", []).append("IntToFloat")
        return float(input_data) * 1.5


class FloatToStringStage:
    """Mock stage: Convert float to string."""

    def process(self, input_data: float, context: ProcessingContext) -> str:
        """Format float as string."""
        context.metrics.setdefault("stages_executed", []).append("FloatToString")
        return f"Result: {input_data:.1f}"


class IdentityStage:
    """Mock stage: Return input unchanged (identity function)."""

    def process(self, input_data: str, context: ProcessingContext) -> str:
        """Return input unchanged."""
        context.metrics.setdefault("stages_executed", []).append("Identity")
        return input_data


class ContextTrackerStage:
    """Mock stage: Track that context was received."""

    def process(self, input_data: str, context: ProcessingContext) -> str:
        """Record context receipt in metrics."""
        context.metrics["context_received"] = True
        context.metrics.setdefault("config_values", []).append(context.config.get("test_key"))
        return input_data


class ErrorRaisingStage:
    """Mock stage: Raise an exception."""

    def process(self, input_data: str, context: ProcessingContext) -> str:
        """Raise ValueError for testing error propagation."""
        raise ValueError("Test error from stage")


class TestPipelineStageProtocol:
    """Test PipelineStage protocol compliance."""

    @pytest.mark.test_id("unit-PIPE-001")
    def test_protocol_compliance_with_process_method(self) -> None:
        """Test that class with process() method implements PipelineStage protocol."""
        # Mock stage implements protocol
        stage = StringToIntStage()
        context = ProcessingContext()

        # Should work with protocol - no runtime type checking needed for structural subtyping
        # Just verify it has the required method signature
        assert hasattr(stage, "process")
        assert callable(stage.process)

        # Verify it works as expected
        result = stage.process("test", context)
        assert isinstance(result, int)
        assert result == 4

    @pytest.mark.test_id("unit-PIPE-002")
    def test_protocol_stage_modifies_context_metrics(self) -> None:
        """Test that stages can modify context metrics (mutable behavior)."""
        stage = StringToIntStage()
        context = ProcessingContext(metrics={})

        # Process data
        stage.process("hello", context)

        # Verify context was modified
        assert "stages_executed" in context.metrics
        assert context.metrics["stages_executed"] == ["StringToInt"]


class TestSingleStageExecution:
    """Test pipeline with single stage."""

    @pytest.mark.test_id("unit-PIPE-003")
    def test_single_stage_pipeline_processes_correctly(self) -> None:
        """Test pipeline with one stage executes correctly."""
        pipeline = Pipeline([StringToIntStage()])
        context = ProcessingContext()

        result = pipeline.process("hello", context)

        assert result == 5  # len("hello") = 5
        assert context.metrics["stages_executed"] == ["StringToInt"]

    @pytest.mark.test_id("unit-PIPE-004")
    def test_single_stage_with_config(self) -> None:
        """Test single stage pipeline receives config from context."""
        pipeline = Pipeline([ContextTrackerStage()])
        context = ProcessingContext(config={"test_key": "test_value"})

        result = pipeline.process("input", context)

        assert result == "input"
        assert context.metrics["context_received"] is True
        assert context.metrics["config_values"] == ["test_value"]

    @pytest.mark.test_id("unit-PIPE-005")
    def test_single_stage_identity_transformation(self) -> None:
        """Test pipeline with identity stage returns input unchanged."""
        pipeline = Pipeline([IdentityStage()])
        context = ProcessingContext()

        result = pipeline.process("test_input", context)

        assert result == "test_input"
        assert context.metrics["stages_executed"] == ["Identity"]


class TestMultiStageChaining:
    """Test pipeline with multiple stages chained together."""

    @pytest.mark.test_id("unit-PIPE-006")
    def test_two_stage_pipeline_chains_correctly(self) -> None:
        """Test output of stage 1 becomes input of stage 2."""
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage()])
        context = ProcessingContext()

        result = pipeline.process("hello", context)

        # len("hello") = 5, 5 * 1.5 = 7.5
        assert result == 7.5
        assert context.metrics["stages_executed"] == ["StringToInt", "IntToFloat"]

    @pytest.mark.test_id("unit-PIPE-007")
    def test_three_stage_pipeline_chains_correctly(self) -> None:
        """Test three stages chain together with correct type flow."""
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage(), FloatToStringStage()])
        context = ProcessingContext()

        result = pipeline.process("test", context)

        # len("test") = 4, 4 * 1.5 = 6.0, "Result: 6.0"
        assert result == "Result: 6.0"
        assert context.metrics["stages_executed"] == ["StringToInt", "IntToFloat", "FloatToString"]

    @pytest.mark.test_id("unit-PIPE-008")
    def test_multi_stage_preserves_data_through_chain(self) -> None:
        """Test data transformations are applied sequentially."""
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage()])
        context = ProcessingContext()

        # Test with different inputs to verify determinism
        result1 = pipeline.process("abc", context)  # len=3, 3*1.5=4.5
        assert result1 == 4.5

        # Reset context for second run
        context2 = ProcessingContext()
        result2 = pipeline.process("abcdef", context2)  # len=6, 6*1.5=9.0
        assert result2 == 9.0


class TestEmptyPipelineHandling:
    """Test pipeline with no stages."""

    @pytest.mark.test_id("unit-PIPE-009")
    def test_empty_pipeline_returns_input_unchanged(self) -> None:
        """Test pipeline with empty stages list returns initial input."""
        pipeline = Pipeline([])
        context = ProcessingContext()

        result = pipeline.process("test_input", context)

        assert result == "test_input"

    @pytest.mark.test_id("unit-PIPE-010")
    def test_empty_pipeline_with_different_types(self) -> None:
        """Test empty pipeline preserves input type."""
        pipeline = Pipeline([])
        context = ProcessingContext()

        # Test string
        assert pipeline.process("string", context) == "string"

        # Test int
        assert pipeline.process(42, context) == 42

        # Test float
        assert pipeline.process(3.14, context) == 3.14

        # Test dict
        test_dict = {"key": "value"}
        assert pipeline.process(test_dict, context) == test_dict


class TestContextPropagation:
    """Test ProcessingContext is passed to all stages."""

    @pytest.mark.test_id("unit-PIPE-011")
    def test_context_passed_to_all_stages(self) -> None:
        """Test same context instance is passed to all stages."""
        pipeline = Pipeline([ContextTrackerStage(), IdentityStage(), ContextTrackerStage()])
        context = ProcessingContext(config={"test_key": "shared_value"})

        pipeline.process("input", context)

        # All stages should have received context
        assert context.metrics["context_received"] is True
        # Config should be same for all stages
        assert context.metrics["config_values"] == ["shared_value", "shared_value"]

    @pytest.mark.test_id("unit-PIPE-012")
    def test_context_metrics_accumulate_across_stages(self) -> None:
        """Test context metrics accumulate as stages execute."""
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage(), FloatToStringStage()])
        context = ProcessingContext(metrics={})

        pipeline.process("test", context)

        # Metrics should show all three stages executed
        assert len(context.metrics["stages_executed"]) == 3
        assert context.metrics["stages_executed"][0] == "StringToInt"
        assert context.metrics["stages_executed"][1] == "IntToFloat"
        assert context.metrics["stages_executed"][2] == "FloatToString"


class TestErrorPropagation:
    """Test exceptions propagate from stages."""

    @pytest.mark.test_id("unit-PIPE-013")
    def test_exception_propagates_from_stage(self) -> None:
        """Test exception raised in stage bubbles up to caller."""
        pipeline = Pipeline([ErrorRaisingStage()])
        context = ProcessingContext()

        with pytest.raises(ValueError, match="Test error from stage"):
            pipeline.process("input", context)

    @pytest.mark.test_id("unit-PIPE-014")
    def test_exception_in_middle_stage_halts_pipeline(self) -> None:
        """Test exception in middle stage prevents later stages from executing."""
        pipeline = Pipeline([StringToIntStage(), ErrorRaisingStage(), FloatToStringStage()])
        context = ProcessingContext()

        with pytest.raises(ValueError, match="Test error from stage"):
            # This will fail because StringToIntStage returns int, not str expected by ErrorRaisingStage
            # Let's fix the test to use proper types
            pipeline.process("input", context)

        # First stage should have executed, but not the third
        assert "stages_executed" in context.metrics
        assert context.metrics["stages_executed"] == ["StringToInt"]


class TestDeterminism:
    """Test pipeline produces deterministic results."""

    @pytest.mark.test_id("unit-PIPE-015")
    def test_same_input_produces_same_output(self) -> None:
        """Test pipeline is deterministic - same input yields same output."""
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage()])

        context1 = ProcessingContext()
        result1 = pipeline.process("hello", context1)

        context2 = ProcessingContext()
        result2 = pipeline.process("hello", context2)

        assert result1 == result2
        assert result1 == 7.5

    @pytest.mark.test_id("unit-PIPE-016")
    def test_different_inputs_produce_different_outputs(self) -> None:
        """Test pipeline correctly transforms different inputs."""
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage()])

        context1 = ProcessingContext()
        result1 = pipeline.process("abc", context1)  # len=3, 3*1.5=4.5

        context2 = ProcessingContext()
        result2 = pipeline.process("abcdef", context2)  # len=6, 6*1.5=9.0

        assert result1 == 4.5
        assert result2 == 9.0
        assert result1 != result2
