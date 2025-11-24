"""Shared pytest fixtures and configuration for all tests."""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest


# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def examples_dir(project_root: Path) -> Path:
    """Return the examples directory."""
    return project_root / "examples"


@pytest.fixture(scope="session")
def test_fixtures_dir() -> Path:
    """Return the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_env(temp_dir: Path) -> Generator[dict, None, None]:
    """Provide temporary environment variables and clean up after test."""
    original_env = os.environ.copy()
    temp_env_vars = {
        "TMPDIR": str(temp_dir),
        "TEST_MODE": "true",
    }
    os.environ.update(temp_env_vars)

    yield temp_env_vars

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="session")
def gpu_available() -> bool:
    """Check if GPU is available for testing."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


@pytest.fixture(scope="session")
def skip_if_no_gpu(gpu_available: bool):
    """Skip test if GPU is not available."""
    if not gpu_available:
        pytest.skip("GPU not available")


@pytest.fixture(scope="session")
def kfp_available() -> bool:
    """Check if KFP is available for testing."""
    try:
        import kfp

        return True
    except ImportError:
        return False


@pytest.fixture(scope="session")
def skip_if_no_kfp(kfp_available: bool):
    """Skip test if KFP is not available."""
    if not kfp_available:
        pytest.skip("KFP not installed")


@pytest.fixture
def sample_env_file(temp_dir: Path) -> Path:
    """Create a sample .env file for testing."""
    env_file = temp_dir / ".env"
    env_content = """
# Sample environment variables for testing
MODEL_NAME=test-model
DATASET_PATH=/tmp/test-dataset
HF_TOKEN=test-token-123
OUTPUT_DIR=/tmp/output
"""
    env_file.write_text(env_content.strip())
    return env_file


@pytest.fixture
def sample_jsonl_file(temp_dir: Path) -> Path:
    """Create a sample JSONL file for testing."""
    jsonl_file = temp_dir / "sample.jsonl"
    jsonl_content = """{"messages": [{"role": "user", "content": "What is AI?"}, {"role": "assistant", "content": "AI stands for Artificial Intelligence."}]}
{"messages": [{"role": "user", "content": "What is ML?"}, {"role": "assistant", "content": "ML stands for Machine Learning."}]}
{"messages": [{"role": "user", "content": "What is RHOAI?"}, {"role": "assistant", "content": "RHOAI is Red Hat OpenShift AI."}]}
"""
    jsonl_file.write_text(jsonl_content.strip())
    return jsonl_file


@pytest.fixture
def mock_model_config(temp_dir: Path) -> dict:
    """Provide a mock model configuration for testing."""
    return {
        "model_name": "test-model",
        "model_type": "llama",
        "hidden_size": 768,
        "num_attention_heads": 12,
        "num_hidden_layers": 6,
        "vocab_size": 32000,
        "max_position_embeddings": 2048,
    }


@pytest.fixture
def mock_training_config(temp_dir: Path) -> dict:
    """Provide a mock training configuration for testing."""
    return {
        "num_train_epochs": 1,
        "per_device_train_batch_size": 2,
        "learning_rate": 5e-5,
        "output_dir": str(temp_dir / "output"),
        "logging_steps": 10,
        "save_steps": 100,
    }


# Notebook fixtures
@pytest.fixture
def minimal_notebook() -> dict:
    """Create a minimal valid notebook structure for testing."""
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": ["# Test Notebook\n", "\n", "This is a test notebook."],
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["print('Hello, World!')"],
            },
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11.0",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


@pytest.fixture
def notebook_with_outputs() -> dict:
    """Create a notebook with outputs for testing."""
    return {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [
                    {
                        "name": "stdout",
                        "output_type": "stream",
                        "text": ["Hello, World!\n"],
                    }
                ],
                "source": ["print('Hello, World!')"],
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


# Helper functions available to all tests
def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (slower)"
    )
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test (slowest)")
    config.addinivalue_line("markers", "unit: mark test as unit test (fast)")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark tests based on their directory
        if "tests/unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "tests/e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "tests/notebooks" in str(item.fspath):
            item.add_marker(pytest.mark.notebook)

        # Auto-skip GPU tests if no GPU available
        if "gpu" in item.keywords:
            try:
                import torch

                if not torch.cuda.is_available():
                    item.add_marker(
                        pytest.mark.skip(reason="GPU not available for testing")
                    )
            except ImportError:
                item.add_marker(
                    pytest.mark.skip(reason="PyTorch not installed, cannot test GPU")
                )


# Session-scoped cleanup
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """Clean up test artifacts after test session."""
    yield
    # Cleanup logic here if needed
    pass
