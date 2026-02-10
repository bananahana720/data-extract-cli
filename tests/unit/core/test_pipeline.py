"""Unit tests for pipeline architecture.

Tests cover:
- PipelineStage Protocol compliance
- Pipeline orchestration with mock stages
- Data flow between stages
- ProcessingContext propagation
- Edge cases (empty pipeline, single stage)
"""

from src.data_extract.core.models import ProcessingContext
from src.data_extract.core.pipeline import Pipeline


# Mock pipeline stages for testing
class StringToIntStage:
    """Mock stage: converts string to int (length)."""

    def process(self, input_data: str, context: ProcessingContext) -> int:
        """Return length of input string."""
        # Track stage execution in metrics
        if "stages_executed" not in context.metrics:
            context.metrics["stages_executed"] = []
        context.metrics["stages_executed"].append("StringToIntStage")
        return len(input_data)


class IntToFloatStage:
    """Mock stage: converts int to float (multiply by 1.5)."""

    def process(self, input_data: int, context: ProcessingContext) -> float:
        """Multiply input by 1.5."""
        if "stages_executed" not in context.metrics:
            context.metrics["stages_executed"] = []
        context.metrics["stages_executed"].append("IntToFloatStage")
        return float(input_data) * 1.5


class FloatToStringStage:
    """Mock stage: converts float to string."""

    def process(self, input_data: float, context: ProcessingContext) -> str:
        """Convert float to string with 2 decimal places."""
        if "stages_executed" not in context.metrics:
            context.metrics["stages_executed"] = []
        context.metrics["stages_executed"].append("FloatToStringStage")
        return f"{input_data:.2f}"


class IdentityStage:
    """Mock stage: returns input unchanged (for testing)."""

    def process(self, input_data: str, context: ProcessingContext) -> str:
        """Return input unchanged."""
        if "stages_executed" not in context.metrics:
            context.metrics["stages_executed"] = []
        context.metrics["stages_executed"].append("IdentityStage")
        return input_data


class TestPipelineStageProtocol:
    """Test PipelineStage Protocol compliance."""

    def test_mock_stage_implements_protocol(self):
        """Test that mock stages implement PipelineStage protocol."""
        # Protocol compliance is checked at type-checking time (mypy)
        # Runtime test verifies process() method exists
        stage = StringToIntStage()
        context = ProcessingContext()

        # Should have process method
        assert hasattr(stage, "process")
        assert callable(stage.process)

        # Should accept correct parameters
        result = stage.process("hello", context)
        assert isinstance(result, int)

    def test_stage_process_signature(self):
        """Test stage process() method has correct signature."""
        stage = IntToFloatStage()
        context = ProcessingContext()

        # Should accept input_data and context parameters
        result = stage.process(10, context)
        assert result == 15.0

    def test_multiple_stages_implement_protocol(self):
        """Test that all mock stages implement the protocol."""
        stages = [
            StringToIntStage(),
            IntToFloatStage(),
            FloatToStringStage(),
            IdentityStage(),
        ]

        for stage in stages:
            assert hasattr(stage, "process")
            assert callable(stage.process)


class TestPipelineOrchestrator:
    """Test Pipeline orchestrator class."""

    def test_pipeline_creation(self):
        """Test Pipeline instantiation with list of stages."""
        stages = [StringToIntStage(), IntToFloatStage()]
        pipeline = Pipeline(stages)

        assert pipeline.stages == stages
        assert len(pipeline.stages) == 2

    def test_pipeline_single_stage(self):
        """Test Pipeline with single stage (edge case)."""
        stage = StringToIntStage()
        pipeline = Pipeline([stage])
        context = ProcessingContext()

        result = pipeline.process("hello", context)
        assert result == 5  # len("hello")

    def test_pipeline_two_stages(self):
        """Test Pipeline chains two stages correctly."""
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage()])
        context = ProcessingContext()

        result = pipeline.process("hello", context)
        # len("hello") = 5, 5 * 1.5 = 7.5
        assert result == 7.5

    def test_pipeline_three_stages(self):
        """Test Pipeline chains three stages correctly."""
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage(), FloatToStringStage()])
        context = ProcessingContext()

        result = pipeline.process("hello", context)
        # len("hello") = 5, 5 * 1.5 = 7.5, "7.50"
        assert result == "7.50"

    def test_pipeline_empty_stages(self):
        """Test Pipeline with no stages returns input unchanged."""
        pipeline = Pipeline([])
        context = ProcessingContext()

        result = pipeline.process("hello", context)
        assert result == "hello"

    def test_pipeline_context_propagation(self):
        """Test ProcessingContext is passed through all stages."""
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage(), FloatToStringStage()])
        context = ProcessingContext(config={"test_key": "test_value"})

        pipeline.process("hello", context)

        # All stages should have been executed (tracked in metrics)
        assert "stages_executed" in context.metrics
        assert len(context.metrics["stages_executed"]) == 3
        assert "StringToIntStage" in context.metrics["stages_executed"]
        assert "IntToFloatStage" in context.metrics["stages_executed"]
        assert "FloatToStringStage" in context.metrics["stages_executed"]

    def test_pipeline_context_config_accessible(self):
        """Test pipeline stages can access ProcessingContext config."""

        class ConfigAccessStage:
            """Stage that accesses config from context."""

            def process(self, input_data: str, context: ProcessingContext) -> str:
                # Access config value
                prefix = context.config.get("prefix", "")
                return f"{prefix}{input_data}"

        pipeline = Pipeline([ConfigAccessStage()])
        context = ProcessingContext(config={"prefix": "PROCESSED:"})

        result = pipeline.process("data", context)
        assert result == "PROCESSED:data"

    def test_pipeline_metrics_accumulation(self):
        """Test pipeline stages can accumulate metrics."""

        class MetricsStage:
            """Stage that updates metrics."""

            def process(self, input_data: int, context: ProcessingContext) -> int:
                if "count" not in context.metrics:
                    context.metrics["count"] = 0
                context.metrics["count"] += 1
                return input_data + 1

        pipeline = Pipeline([MetricsStage(), MetricsStage(), MetricsStage()])
        context = ProcessingContext()

        result = pipeline.process(0, context)
        assert result == 3  # 0 + 1 + 1 + 1
        assert context.metrics["count"] == 3  # 3 stages executed

    def test_pipeline_data_flow_types(self):
        """Test pipeline correctly flows different data types between stages."""
        # str -> int -> float -> str
        pipeline = Pipeline([StringToIntStage(), IntToFloatStage(), FloatToStringStage()])
        context = ProcessingContext()

        # Input: string
        result = pipeline.process("testing", context)

        # Output: string (after int and float transformations)
        assert isinstance(result, str)
        # len("testing") = 7, 7 * 1.5 = 10.5, "10.50"
        assert result == "10.50"

    def test_pipeline_with_identity_stage(self):
        """Test pipeline with identity stage (returns input unchanged)."""
        pipeline = Pipeline([IdentityStage(), IdentityStage()])
        context = ProcessingContext()

        result = pipeline.process("data", context)
        assert result == "data"
        assert len(context.metrics["stages_executed"]) == 2
