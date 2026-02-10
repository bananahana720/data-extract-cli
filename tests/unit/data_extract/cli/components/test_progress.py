"""Unit tests for CLI progress tracking components."""

import time

import pytest

from data_extract.cli.components.progress import (
    FileProgress,
    PipelineProgress,
    PipelineStage,
    StageProgress,
)

pytestmark = [pytest.mark.P1, pytest.mark.unit]


class TestPipelineStage:
    """Tests for PipelineStage enum."""

    def test_pipeline_stages(self):
        """Test PipelineStage enum values."""
        assert PipelineStage.EXTRACT == "extract"
        assert PipelineStage.NORMALIZE == "normalize"
        assert PipelineStage.CHUNK == "chunk"
        assert PipelineStage.SEMANTIC == "semantic"
        assert PipelineStage.OUTPUT == "output"

    def test_all_stages_present(self):
        """Test that all 5 stages are defined."""
        stages = [
            PipelineStage.EXTRACT,
            PipelineStage.NORMALIZE,
            PipelineStage.CHUNK,
            PipelineStage.SEMANTIC,
            PipelineStage.OUTPUT,
        ]
        assert len(stages) == 5


class TestStageProgress:
    """Tests for StageProgress dataclass."""

    def test_stage_progress_initialization(self):
        """Test StageProgress initialization."""
        stage = StageProgress(name="extract", total=10)
        assert stage.name == "extract"
        assert stage.total == 10
        assert stage.completed == 0
        assert not stage.started

    def test_stage_progress_defaults(self):
        """Test StageProgress default values."""
        stage = StageProgress(name="normalize")
        assert stage.name == "normalize"
        assert stage.total == 0
        assert stage.completed == 0
        assert not stage.started


class TestPipelineProgress:
    """Tests for PipelineProgress class."""

    def test_initialization(self, mock_console):
        """Test PipelineProgress initialization."""
        progress = PipelineProgress(total_files=10, console=mock_console)
        assert progress.total_files == 10
        assert progress.completed == 0
        assert progress.current_file is None
        assert not progress.is_started
        assert not progress.is_stopped

    def test_stages_initialization(self, mock_console):
        """Test that all 5 stages are initialized."""
        progress = PipelineProgress(total_files=5, console=mock_console)
        assert len(progress.stages) == 5
        assert "extract" in progress.stages
        assert "normalize" in progress.stages
        assert "chunk" in progress.stages
        assert "semantic" in progress.stages
        assert "output" in progress.stages

    def test_percentage_zero_files(self, mock_console):
        """Test percentage calculation with zero files."""
        progress = PipelineProgress(total_files=0, console=mock_console)
        assert progress.percentage == 100.0

    def test_percentage_calculation(self, mock_console):
        """Test percentage calculation."""
        progress = PipelineProgress(total_files=10, console=mock_console)
        progress._completed = 5
        assert progress.percentage == 50.0

    def test_file_count_property(self, mock_console):
        """Test file_count property."""
        progress = PipelineProgress(total_files=10, console=mock_console)
        progress._completed = 3
        assert progress.file_count == "3/10"

    def test_elapsed_before_start(self, mock_console):
        """Test elapsed time before start."""
        progress = PipelineProgress(total_files=5, console=mock_console)
        assert progress.elapsed == 0.0

    def test_elapsed_after_start(self, mock_console):
        """Test elapsed time after start."""
        progress = PipelineProgress(total_files=5, console=mock_console)
        progress._start_time = time.time() - 5.0
        assert progress.elapsed >= 5.0

    def test_eta_no_progress(self, mock_console):
        """Test ETA calculation with no progress."""
        progress = PipelineProgress(total_files=10, console=mock_console)
        assert progress.get_eta() is None

    def test_eta_with_progress(self, mock_console):
        """Test ETA calculation with progress."""
        progress = PipelineProgress(total_files=10, console=mock_console)
        progress._start_time = time.time() - 10.0
        progress._completed = 5

        eta = progress.get_eta()
        assert eta is not None
        assert eta > 0

    def test_start(self, string_console):
        """Test starting progress tracking."""
        progress = PipelineProgress(total_files=5, console=string_console)
        progress.start()

        assert progress.is_started
        assert not progress.is_stopped
        assert progress._start_time is not None
        assert progress._progress is not None

    def test_stop(self, string_console):
        """Test stopping progress tracking."""
        progress = PipelineProgress(total_files=5, console=string_console)
        progress.start()
        progress.stop()

        assert not progress.is_started
        assert progress.is_stopped

    def test_context_manager(self, string_console):
        """Test PipelineProgress as context manager."""
        progress = PipelineProgress(total_files=5, console=string_console)

        assert not progress.is_started

        with progress as p:
            assert p is progress
            assert p.is_started

        assert not progress.is_started
        assert progress.is_stopped

    def test_start_stage(self, mock_console):
        """Test starting a stage."""
        progress = PipelineProgress(total_files=5, console=mock_console)
        progress.start_stage("extract")

        assert progress.stages["extract"].started

    def test_complete_stage(self, mock_console):
        """Test completing a stage for one file."""
        progress = PipelineProgress(total_files=5, console=mock_console)
        progress.complete_stage("extract")

        assert progress.stages["extract"].completed == 1

    def test_update_stage(self, string_console):
        """Test updating stage progress."""
        progress = PipelineProgress(total_files=5, console=string_console)
        progress.start()
        progress.update_stage("extract", 3)

        assert progress.stages["extract"].completed == 3
        assert progress.stages["extract"].started

    def test_update_stage_output_updates_completed(self, string_console):
        """Test that updating output stage updates overall completed count."""
        progress = PipelineProgress(total_files=5, console=string_console)
        progress.start()
        progress.update_stage("output", 2)

        assert progress.completed == 2

    def test_update_file(self, string_console):
        """Test updating current file."""
        progress = PipelineProgress(total_files=5, console=string_console)
        progress.start()
        progress.update_file("test.pdf", "extract")

        assert progress.current_file == "test.pdf"

    def test_advance(self, string_console):
        """Test advancing progress by one file."""
        progress = PipelineProgress(total_files=5, console=string_console)
        progress.start()

        assert progress.completed == 0
        progress.advance()
        assert progress.completed == 1
        progress.advance()
        assert progress.completed == 2

    def test_is_complete(self, mock_console):
        """Test is_complete method."""
        progress = PipelineProgress(total_files=3, console=mock_console)
        assert not progress.is_complete()

        progress._completed = 3
        assert progress.is_complete()

        progress._completed = 4
        assert progress.is_complete()

    def test_get_status(self, mock_console):
        """Test get_status returns comprehensive status dict."""
        progress = PipelineProgress(total_files=10, console=mock_console)
        progress._completed = 5
        progress._current_file = "test.pdf"
        progress._start_time = time.time()

        status = progress.get_status()

        assert status["percentage"] == 50.0
        assert status["completed"] == 5
        assert status["total"] == 10
        assert status["filename"] == "test.pdf"
        assert status["current_file"] == "test.pdf"
        assert "elapsed" in status
        assert "eta" in status
        assert "remaining" in status

    def test_reset(self, string_console):
        """Test resetting progress for new batch."""
        progress = PipelineProgress(total_files=5, console=string_console)
        progress.start()
        progress._completed = 3
        progress._current_file = "test.pdf"
        progress.update_stage("extract", 3)

        progress.reset(total_files=10)

        assert progress.total_files == 10
        assert progress.completed == 0
        assert progress.current_file is None
        assert not progress.is_started
        assert not progress.is_stopped
        assert progress.stages["extract"].completed == 0
        assert progress.stages["extract"].total == 10


class TestFileProgress:
    """Tests for FileProgress class."""

    def test_initialization(self, mock_console):
        """Test FileProgress initialization."""
        progress = FileProgress(total_files=10, console=mock_console)
        assert progress.total_files == 10
        assert progress.current == 0
        assert progress.current_file is None

    def test_initialization_with_filename(self, mock_console):
        """Test FileProgress initialization with filename."""
        progress = FileProgress(total_files=5, filename="test.pdf", console=mock_console)
        assert progress.current_file == "test.pdf"

    def test_initialization_default_stages(self, mock_console):
        """Test FileProgress initialization with default stages."""
        progress = FileProgress(total_files=10, console=mock_console)
        assert progress._total_stages == 5

    def test_initialization_custom_stages(self, mock_console):
        """Test FileProgress initialization with custom stages."""
        progress = FileProgress(total_files=10, total_stages=3, console=mock_console)
        assert progress._total_stages == 3

    def test_update(self, string_console):
        """Test updating file progress."""
        progress = FileProgress(total_files=10, console=string_console)
        progress.start()
        progress.update(current=3, filename="file3.pdf")

        assert progress.current == 3
        assert progress.current_file == "file3.pdf"

    def test_start(self, string_console):
        """Test starting file progress display."""
        progress = FileProgress(total_files=5, console=string_console)
        progress.start()

        assert progress._progress is not None
        assert progress._task_id is not None
        assert progress._start_time is not None

    def test_stop(self, string_console):
        """Test stopping file progress display."""
        progress = FileProgress(total_files=5, console=string_console)
        progress.start()

        assert progress._progress is not None
        progress.stop()
        # After stop, progress object still exists but is stopped

    def test_context_manager(self, mock_console):
        """Test FileProgress as context manager."""
        progress = FileProgress(total_files=5, console=mock_console)

        with progress as p:
            assert p is progress
            # Progress should not auto-start in FileProgress
            # (unlike PipelineProgress which does)

    def test_properties(self, mock_console):
        """Test FileProgress properties."""
        progress = FileProgress(total_files=20, filename="initial.pdf", console=mock_console)

        assert progress.current_file == "initial.pdf"
        assert progress.total_files == 20
        assert progress.current == 0

        progress.update(5, "file5.pdf")
        assert progress.current == 5
        assert progress.current_file == "file5.pdf"
