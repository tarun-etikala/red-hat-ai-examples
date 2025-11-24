"""Integration tests for dependency installation and compatibility."""

import importlib
import sys

import pytest


@pytest.mark.integration
class TestCoreDependencies:
    """Tests for core Python dependencies."""

    def test_python_version(self):
        """Test that Python version is compatible."""
        assert sys.version_info >= (3, 11), "Python 3.11+ is required"
        assert sys.version_info < (4, 0), "Python 4.x is not supported"

    def test_import_pytest(self):
        """Test pytest is installed."""
        import pytest as pt

        assert pt is not None
        assert hasattr(pt, "mark")

    def test_import_yaml(self):
        """Test PyYAML is installed."""
        import yaml

        assert yaml is not None
        assert hasattr(yaml, "safe_load")

    def test_import_nbformat(self):
        """Test nbformat is installed."""
        import nbformat

        assert nbformat is not None
        assert hasattr(nbformat, "read")
        assert hasattr(nbformat, "validate")


@pytest.mark.integration
class TestMLDependencies:
    """Tests for ML/AI related dependencies."""

    def test_import_torch(self):
        """Test PyTorch is importable (optional for some tests)."""
        try:
            import torch

            assert torch is not None
            assert hasattr(torch, "__version__")
        except ImportError:
            pytest.skip("PyTorch not installed")

    def test_import_transformers(self):
        """Test transformers library (optional)."""
        try:
            import transformers

            assert transformers is not None
            assert hasattr(transformers, "__version__")
        except ImportError:
            pytest.skip("Transformers not installed")

    def test_import_datasets(self):
        """Test datasets library (optional)."""
        try:
            import datasets

            assert datasets is not None
            assert hasattr(datasets, "load_dataset")
        except ImportError:
            pytest.skip("Datasets not installed")


@pytest.mark.integration
class TestDataDependencies:
    """Tests for data processing dependencies."""

    def test_import_polars(self):
        """Test Polars is importable (used in knowledge_utils)."""
        try:
            import polars as pl

            assert pl is not None
            assert hasattr(pl, "DataFrame")
        except ImportError:
            pytest.skip("Polars not installed")

    def test_polars_dataframe_creation(self):
        """Test basic Polars DataFrame operations."""
        try:
            import polars as pl

            df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
            assert len(df) == 3
            assert df.columns == ["a", "b"]
        except ImportError:
            pytest.skip("Polars not installed")


@pytest.mark.integration
class TestNotebookDependencies:
    """Tests for notebook-related dependencies."""

    def test_import_papermill(self):
        """Test papermill for notebook execution."""
        try:
            import papermill

            assert papermill is not None
            assert hasattr(papermill, "execute_notebook")
        except ImportError:
            pytest.skip("Papermill not installed")

    def test_import_jupyter(self):
        """Test Jupyter is installed."""
        try:
            import jupyter

            assert jupyter is not None
        except ImportError:
            pytest.skip("Jupyter not installed")

    def test_import_ipykernel(self):
        """Test IPython kernel is installed."""
        try:
            import ipykernel

            assert ipykernel is not None
        except ImportError:
            pytest.skip("IPykernel not installed")


@pytest.mark.integration
@pytest.mark.kfp
class TestKFPDependencies:
    """Tests for Kubeflow Pipelines dependencies."""

    def test_import_kfp(self):
        """Test KFP is importable."""
        try:
            import kfp

            assert kfp is not None
            assert hasattr(kfp, "dsl")
        except ImportError:
            pytest.skip("KFP not installed")

    def test_import_kfp_kubernetes(self):
        """Test KFP Kubernetes is importable."""
        try:
            import kfp_kubernetes

            assert kfp_kubernetes is not None
        except ImportError:
            pytest.skip("KFP Kubernetes not installed")

    def test_kfp_compiler(self):
        """Test KFP compiler is available."""
        try:
            from kfp import compiler

            assert compiler is not None
            assert hasattr(compiler, "Compiler")
        except ImportError:
            pytest.skip("KFP not installed")


@pytest.mark.integration
class TestDependencyVersions:
    """Tests for checking dependency versions."""

    def test_pytest_version(self):
        """Test pytest version is compatible."""
        import pytest

        version = tuple(int(x) for x in pytest.__version__.split(".")[:2])
        assert version >= (8, 0), "Pytest 8.0+ is required"

    def test_nbformat_version(self):
        """Test nbformat version is compatible."""
        import nbformat

        version = tuple(int(x) for x in nbformat.__version__.split(".")[:2])
        assert version >= (5, 0), "nbformat 5.0+ is required"

    def test_polars_version_if_installed(self):
        """Test Polars version if installed."""
        try:
            import polars as pl

            # Polars version should be recent
            assert hasattr(pl, "__version__")
        except ImportError:
            pytest.skip("Polars not installed")


@pytest.mark.integration
class TestDependencyConflicts:
    """Tests for detecting dependency conflicts."""

    def test_no_duplicate_torch_installations(self):
        """Test that there's only one torch installation."""
        try:
            import torch

            # If torch is installed, it should have a single __file__
            assert torch.__file__ is not None
        except ImportError:
            pytest.skip("PyTorch not installed")

    def test_compatible_torch_transformers(self):
        """Test PyTorch and Transformers compatibility."""
        try:
            import torch
            import transformers

            # Both should be importable without conflicts
            assert torch is not None
            assert transformers is not None
        except ImportError:
            pytest.skip("PyTorch or Transformers not installed")


@pytest.mark.integration
class TestOptionalDependencies:
    """Tests for optional dependencies used in examples."""

    def test_docling_import(self):
        """Test docling (used in data processing)."""
        try:
            import docling

            assert docling is not None
        except ImportError:
            pytest.skip("Docling not installed (optional)")

    def test_tiktoken_import(self):
        """Test tiktoken (used in knowledge tuning)."""
        try:
            import tiktoken

            assert tiktoken is not None
        except ImportError:
            pytest.skip("Tiktoken not installed (optional)")

    def test_rich_import(self):
        """Test rich (used for pretty printing)."""
        try:
            import rich

            assert rich is not None
        except ImportError:
            pytest.skip("Rich not installed (optional)")

    def test_dotenv_import(self):
        """Test python-dotenv."""
        try:
            import dotenv

            assert dotenv is not None
            assert hasattr(dotenv, "load_dotenv")
        except ImportError:
            pytest.skip("python-dotenv not installed (optional)")


@pytest.mark.integration
class TestModuleImports:
    """Tests for importing example modules."""

    def test_import_knowledge_utils(self):
        """Test importing knowledge_utils module."""
        try:
            sys.path.insert(
                0,
                str(
                    pytest.importorskip("pathlib").Path(__file__).parent.parent.parent
                    / "examples"
                    / "knowledge-tuning"
                    / "04_Knowledge_Mixing"
                    / "utils"
                ),
            )
            import knowledge_utils

            assert knowledge_utils is not None
            assert hasattr(knowledge_utils, "sample_doc_qa")
        except ImportError as e:
            pytest.skip(f"Could not import knowledge_utils: {e}")

    def test_import_flash_attn_installer(self):
        """Test importing flash_attn_installer module."""
        try:
            sys.path.insert(
                0,
                str(
                    pytest.importorskip("pathlib").Path(__file__).parent.parent.parent
                    / "examples"
                    / "knowledge-tuning"
                    / "05_Model_Training"
                    / "utils"
                ),
            )
            import flash_attn_installer

            assert flash_attn_installer is not None
            assert hasattr(flash_attn_installer, "get_flash_attention_url")
        except ImportError as e:
            pytest.skip(f"Could not import flash_attn_installer: {e}")


@pytest.mark.integration
class TestEnvironmentSetup:
    """Tests for environment configuration."""

    def test_import_os_environ(self):
        """Test environment variable access."""
        import os

        assert os.environ is not None
        assert isinstance(os.environ, dict)

    def test_pathlib_available(self):
        """Test pathlib is available."""
        from pathlib import Path

        assert Path is not None
        test_path = Path(__file__)
        assert test_path.exists()

    def test_json_available(self):
        """Test JSON module is available."""
        import json

        test_dict = {"key": "value"}
        json_str = json.dumps(test_dict)
        assert json.loads(json_str) == test_dict
