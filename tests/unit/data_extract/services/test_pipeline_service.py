import sys
import types
from pathlib import Path

sys.modules.setdefault("textstat", types.SimpleNamespace())
from data_extract.services.pipeline_service import PipelineService  # noqa: E402


def test_auto_profile_uses_advanced_for_pdf_without_semantic() -> None:
    assert PipelineService._should_use_advanced_pipeline(
        include_semantic=False,
        pipeline_profile="auto",
        file_path=Path("sample.pdf"),
    )


def test_auto_profile_keeps_legacy_for_txt_without_semantic() -> None:
    assert not PipelineService._should_use_advanced_pipeline(
        include_semantic=False,
        pipeline_profile="auto",
        file_path=Path("sample.txt"),
    )


def test_legacy_profile_disables_advanced_even_for_pdf() -> None:
    assert not PipelineService._should_use_advanced_pipeline(
        include_semantic=True,
        pipeline_profile="legacy",
        file_path=Path("sample.pdf"),
    )


def test_advanced_profile_enables_advanced_for_all_inputs() -> None:
    assert PipelineService._should_use_advanced_pipeline(
        include_semantic=False,
        pipeline_profile="advanced",
        file_path=Path("sample.txt"),
    )
