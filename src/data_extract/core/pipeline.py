"""Pipeline architecture for modular data processing.

This module defines the protocol-based pipeline architecture:
- PipelineStage: Protocol defining contract for all pipeline stages
- Pipeline: Orchestrator class that chains multiple stages together

All pipeline stages implement the PipelineStage protocol with Generic[Input, Output]
type parameters for compile-time type safety.
"""

from typing import Any, Generic, List, Protocol, TypeVar

from data_extract.core.models import ProcessingContext

# Type variables for generic pipeline stage
Input = TypeVar("Input", contravariant=True)
Output = TypeVar("Output", covariant=True)


class PipelineStage(Protocol, Generic[Input, Output]):
    """Protocol defining the contract for all pipeline stages.

    All pipeline stages must implement this protocol to ensure consistent
    interfaces and enable type-safe pipeline orchestration.

    Type Parameters:
        Input: Type of input data accepted by this stage
        Output: Type of output data produced by this stage

    Example:
        >>> class MyStage:
        ...     def process(self, input_data: str, context: ProcessingContext) -> int:
        ...         return len(input_data)
        ...
        >>> # MyStage implements PipelineStage[str, int]

    Contract Requirements:
        1. process() method must accept input_data of type Input
        2. process() method must accept context: ProcessingContext
        3. process() method must return data of type Output
        4. Stages should be stateless - all state in ProcessingContext
        5. Stages should be deterministic for audit reproducibility
    """

    def process(self, input_data: Input, context: ProcessingContext) -> Output:
        """Process input data and return transformed output.

        Args:
            input_data: Input data to process (type defined by Input type parameter)
            context: Shared processing context (config, logger, metrics)

        Returns:
            Processed output data (type defined by Output type parameter)

        Raises:
            ProcessingError: For recoverable errors (log, skip file, continue batch)
            CriticalError: For unrecoverable errors (halt processing immediately)
        """
        ...


# Type variable for pipeline data flow
T = TypeVar("T")


class Pipeline:
    """Pipeline orchestrator that chains multiple stages together.

    Orchestrates execution of multiple pipeline stages by passing the output
    of each stage as input to the next stage. Ensures ProcessingContext is
    propagated through all stages.

    Attributes:
        stages: List of pipeline stages to execute in sequence

    Example:
        >>> # Define mock stages
        >>> class StringToInt:
        ...     def process(self, data: str, context: ProcessingContext) -> int:
        ...         return len(data)
        ...
        >>> class IntToFloat:
        ...     def process(self, data: int, context: ProcessingContext) -> float:
        ...         return float(data) * 1.5
        ...
        >>> # Create and run pipeline
        >>> pipeline = Pipeline([StringToInt(), IntToFloat()])
        >>> context = ProcessingContext()
        >>> result = pipeline.process("hello", context)
        >>> print(result)  # 7.5 (len("hello") = 5, 5 * 1.5 = 7.5)
    """

    def __init__(self, stages: List[PipelineStage]) -> None:
        """Initialize pipeline with list of stages.

        Args:
            stages: List of pipeline stages to execute in sequence.
                   Each stage's output type must match next stage's input type.
        """
        self.stages = stages

    def process(self, initial_input: Any, context: ProcessingContext) -> Any:
        """Execute all pipeline stages in sequence.

        Chains stages by passing output of stage N as input to stage N+1.
        ProcessingContext is passed to all stages for config, logging, and metrics.

        Args:
            initial_input: Input data for first pipeline stage
            context: Shared processing context (config, logger, metrics)

        Returns:
            Output from the final pipeline stage

        Raises:
            ProcessingError: If a recoverable error occurs in any stage
            CriticalError: If an unrecoverable error occurs in any stage

        Example:
            >>> pipeline = Pipeline([ExtractStage(), NormalizeStage(), ChunkStage()])
            >>> context = ProcessingContext(config={"chunk_size": 512})
            >>> chunks = pipeline.process(raw_document, context)
        """
        current_data = initial_input

        for stage in self.stages:
            current_data = stage.process(current_data, context)

        return current_data
