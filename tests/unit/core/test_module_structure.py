"""Unit tests for pipeline module structure.

Tests cover:
- All module directories exist
- All modules have __init__.py files
- All modules are importable
- Module docstrings describe purpose
"""

from pathlib import Path


class TestModuleStructure:
    """Test pipeline stage module structure."""

    def test_all_module_directories_exist(self):
        """Test all pipeline stage directories exist."""
        project_root = Path(__file__).parent.parent.parent.parent
        src_path = project_root / "src" / "data_extract"

        expected_modules = ["extract", "normalize", "chunk", "semantic", "output"]

        for module in expected_modules:
            module_path = src_path / module
            assert (
                module_path.exists()
            ), f"Module directory '{module}' does not exist at {module_path}"
            assert module_path.is_dir(), f"'{module}' exists but is not a directory"

    def test_all_modules_have_init_py(self):
        """Test all module directories contain __init__.py."""
        project_root = Path(__file__).parent.parent.parent.parent
        src_path = project_root / "src" / "data_extract"

        expected_modules = ["extract", "normalize", "chunk", "semantic", "output"]

        for module in expected_modules:
            init_path = src_path / module / "__init__.py"
            assert init_path.exists(), f"Module '{module}' missing __init__.py at {init_path}"
            assert init_path.is_file(), f"'{module}/__init__.py' exists but is not a file"

    def test_all_modules_importable(self):
        """Test all pipeline stage modules can be imported."""
        # Should not raise ImportError
        import src.data_extract.chunk
        import src.data_extract.extract
        import src.data_extract.normalize
        import src.data_extract.output
        import src.data_extract.semantic

        # Verify imports succeeded
        assert src.data_extract.extract is not None
        assert src.data_extract.normalize is not None
        assert src.data_extract.chunk is not None
        assert src.data_extract.semantic is not None
        assert src.data_extract.output is not None

    def test_modules_have_docstrings(self):
        """Test all modules have descriptive docstrings."""
        import src.data_extract.chunk
        import src.data_extract.extract
        import src.data_extract.normalize
        import src.data_extract.output
        import src.data_extract.semantic

        modules = [
            ("extract", src.data_extract.extract),
            ("normalize", src.data_extract.normalize),
            ("chunk", src.data_extract.chunk),
            ("semantic", src.data_extract.semantic),
            ("output", src.data_extract.output),
        ]

        for name, module in modules:
            assert module.__doc__ is not None, f"Module '{name}' is missing a docstring"
            assert len(module.__doc__.strip()) > 0, f"Module '{name}' has empty docstring"

    def test_extract_module_docstring_content(self):
        """Test extract module docstring describes purpose."""
        import src.data_extract.extract

        doc = src.data_extract.extract.__doc__
        assert "extraction" in doc.lower() or "extract" in doc.lower()
        assert "document" in doc.lower()

    def test_normalize_module_docstring_content(self):
        """Test normalize module docstring describes purpose."""
        import src.data_extract.normalize

        doc = src.data_extract.normalize.__doc__
        assert "normalization" in doc.lower() or "normalize" in doc.lower()
        assert "text" in doc.lower() or "cleaning" in doc.lower()

    def test_chunk_module_docstring_content(self):
        """Test chunk module docstring describes purpose."""
        import src.data_extract.chunk

        doc = src.data_extract.chunk.__doc__
        assert "chunk" in doc.lower()
        assert "semantic" in doc.lower() or "rag" in doc.lower()

    def test_semantic_module_docstring_content(self):
        """Test semantic module docstring describes purpose."""
        import src.data_extract.semantic

        doc = src.data_extract.semantic.__doc__
        assert "semantic" in doc.lower() or "similarity" in doc.lower()
        assert "analysis" in doc.lower()

    def test_output_module_docstring_content(self):
        """Test output module docstring describes purpose."""
        import src.data_extract.output

        doc = src.data_extract.output.__doc__
        assert "output" in doc.lower() or "format" in doc.lower()
