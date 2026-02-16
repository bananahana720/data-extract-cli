"""Regression test for CLI conftest DOCX fixture dependency handling."""

import builtins

import pytest

from tests.test_cli import conftest as cli_conftest


def test_get_docx_document_skips_when_docx_dependency_is_missing(monkeypatch):
    """Verify DOCX fixture helper skips tests when python-docx is unavailable."""

    original_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "docx":
            raise ModuleNotFoundError("No module named 'docx'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(pytest.skip.Exception) as exc_info:
        cli_conftest._get_docx_document()

    assert "python-docx is required for DOCX fixtures" in str(exc_info.value)
