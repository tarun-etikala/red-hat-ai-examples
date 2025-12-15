"""
Pytest fixtures for E2E testing of knowledge-tuning workflow on RHOAI.

This module provides fixtures for:
- Workspace setup and cleanup
- Configuration management
- Notebook execution utilities
- Output validation helpers
"""

import os
import shutil
from pathlib import Path
from typing import Generator

import pytest

from .config import KNOWLEDGE_TUNING_STEPS, E2ETestConfig, TestProfiles


def pytest_configure(config):
    """Register custom markers for E2E tests."""
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "rhoai: Tests that run on RHOAI cluster")
    config.addinivalue_line("markers", "gpu: Tests that require GPU")
    config.addinivalue_line("markers", "slow: Long-running tests")


def pytest_addoption(parser):
    """Add custom command line options for E2E tests."""
    parser.addoption(
        "--e2e-profile",
        action="store",
        default="minimal",
        choices=["minimal", "standard", "extended"],
        help="E2E test profile: minimal (fast), standard, or extended (thorough)",
    )
    parser.addoption(
        "--keep-outputs",
        action="store_true",
        default=False,
        help="Keep output files after test completion for debugging",
    )
    parser.addoption(
        "--skip-steps",
        action="store",
        default="",
        help="Comma-separated list of step numbers to skip (e.g., '1,5,6')",
    )
    parser.addoption(
        "--student-model",
        action="store",
        default=None,
        help="Override student model name",
    )
    parser.addoption(
        "--teacher-model",
        action="store",
        default=None,
        help="Override teacher model name",
    )


@pytest.fixture(scope="session")
def e2e_config(request) -> E2ETestConfig:
    """Get E2E test configuration based on selected profile."""
    profile_name = request.config.getoption("--e2e-profile")

    profiles = {
        "minimal": TestProfiles.minimal,
        "standard": TestProfiles.standard,
        "extended": TestProfiles.extended,
    }

    config = profiles[profile_name]()

    # Apply command-line overrides
    if request.config.getoption("--student-model"):
        config.student_model_name = request.config.getoption("--student-model")
    if request.config.getoption("--teacher-model"):
        config.teacher_model_name = request.config.getoption("--teacher-model")

    return config


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Get repository root path."""
    return Path(__file__).parent.parent.parent.parent


@pytest.fixture(scope="session")
def knowledge_tuning_path(repo_root) -> Path:
    """Get knowledge-tuning example directory path."""
    path = repo_root / "examples" / "knowledge-tuning"
    if not path.exists():
        pytest.skip("knowledge-tuning directory not found")
    return path


@pytest.fixture(scope="session")
def workflow_steps(request):
    """Get workflow steps, respecting --skip-steps option."""
    skip_steps_str = request.config.getoption("--skip-steps")
    if skip_steps_str:
        skip_steps = {int(s.strip()) for s in skip_steps_str.split(",")}
    else:
        skip_steps = set()

    return [
        step for step in KNOWLEDGE_TUNING_STEPS if step.step_number not in skip_steps
    ]


@pytest.fixture(scope="session")
def e2e_workspace(
    request, tmp_path_factory, knowledge_tuning_path, e2e_config
) -> Generator[Path, None, None]:
    """
    Create and manage the E2E test workspace.

    This fixture:
    1. Creates a temporary workspace directory
    2. Sets up the output directory structure
    3. Configures environment variables
    4. Cleans up after tests (unless --keep-outputs is set)
    """
    # Create workspace in tmp or use a persistent location for debugging
    keep_outputs = request.config.getoption("--keep-outputs")

    if keep_outputs:
        # Use a predictable location for debugging
        workspace = knowledge_tuning_path / "test_output"
        if workspace.exists():
            shutil.rmtree(workspace)
    else:
        workspace = tmp_path_factory.mktemp("e2e_knowledge_tuning")

    # Create output directory structure
    output_dir = workspace / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create step-specific output directories
    for step_dir in ["step_02", "step_03", "step_04", "base_model", "fine_tuned_model"]:
        (output_dir / step_dir).mkdir(parents=True, exist_ok=True)

    # Update config with workspace paths
    e2e_config.workspace_dir = knowledge_tuning_path
    e2e_config.output_dir = output_dir

    # Set environment variables
    env_vars = e2e_config.get_env_vars()
    for key, value in env_vars.items():
        os.environ[key] = value

    yield workspace

    # Cleanup (unless keeping outputs)
    if not keep_outputs:
        # Environment cleanup
        for key in env_vars:
            os.environ.pop(key, None)


def parse_pyproject_dependencies(pyproject_path: Path) -> list:
    """Parse dependencies from pyproject.toml file."""
    try:
        # Try tomllib (Python 3.11+) or tomli
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return []

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Get dependencies from [project.dependencies]
        deps = data.get("project", {}).get("dependencies", [])
        return deps
    except Exception:
        return []


def install_notebook_dependencies(notebook_dir: Path) -> bool:
    """Install dependencies from pyproject.toml in the notebook directory.

    This function extracts dependencies and installs them directly with pip,
    bypassing Python version constraints in the project metadata.
    """
    import subprocess
    import sys

    pyproject_path = notebook_dir / "pyproject.toml"

    if not pyproject_path.exists():
        return True

    deps = parse_pyproject_dependencies(pyproject_path)
    if not deps:
        return True

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q"] + deps,
            capture_output=True,
            text=True,
            timeout=600,
        )
        return result.returncode == 0
    except Exception:
        return True  # Continue even if install fails


@pytest.fixture(scope="session")
def notebook_executor(e2e_config, e2e_workspace):
    """
    Provides a notebook execution utility.

    Returns a callable that executes notebooks with proper configuration.
    Note: Environment variables are set in the e2e_workspace fixture.
    Notebooks read configuration from environment variables, not papermill parameters.
    """
    try:
        import papermill as pm
    except ImportError:
        pytest.skip("papermill not installed. Run: pip install papermill")

    def execute_notebook(
        notebook_path: Path,
        output_path: Path,
        parameters: dict = None,
        timeout: int = None,
        install_deps: bool = True,
    ) -> dict:
        """
        Execute a notebook using papermill.

        Args:
            notebook_path: Path to the input notebook
            output_path: Path to save the executed notebook
            parameters: Optional parameters (unused - kept for API compatibility)
            timeout: Execution timeout in seconds
            install_deps: Whether to install notebook dependencies first

        Returns:
            dict with execution results
        """
        # Install dependencies from notebook's pyproject.toml
        if install_deps:
            install_notebook_dependencies(notebook_path.parent)

        try:
            # Execute notebook WITHOUT passing parameters
            # Notebooks read config from environment variables set in e2e_workspace
            result_nb = pm.execute_notebook(
                str(notebook_path),
                str(output_path),
                cwd=str(notebook_path.parent),
                kernel_name="python3",
                progress_bar=False,
                request_save_on_cell_execute=True,
            )

            return {
                "success": True,
                "notebook": result_nb,
                "output_path": output_path,
                "error": None,
            }

        except pm.PapermillExecutionError as e:
            return {
                "success": False,
                "notebook": None,
                "output_path": output_path,
                "error": str(e),
                "cell_index": getattr(e, "cell_index", None),
                "ename": getattr(e, "ename", None),
                "evalue": getattr(e, "evalue", None),
            }

    return execute_notebook


@pytest.fixture
def output_validator(e2e_workspace, knowledge_tuning_path):
    """
    Provides utilities for validating notebook outputs.
    """

    class OutputValidator:
        def __init__(self):
            self.workspace = e2e_workspace
            self.knowledge_tuning_path = knowledge_tuning_path

        def file_exists(self, relative_path: str) -> bool:
            """Check if a file exists relative to knowledge-tuning directory."""
            full_path = self.knowledge_tuning_path / relative_path
            return full_path.exists()

        def dir_exists(self, relative_path: str) -> bool:
            """Check if a directory exists relative to knowledge-tuning directory."""
            full_path = self.knowledge_tuning_path / relative_path
            return full_path.is_dir()

        def dir_not_empty(self, relative_path: str) -> bool:
            """Check if a directory exists and contains files."""
            full_path = self.knowledge_tuning_path / relative_path
            if not full_path.is_dir():
                return False
            return any(full_path.iterdir())

        def file_has_content(self, relative_path: str, min_size: int = 1) -> bool:
            """Check if a file exists and has minimum content size."""
            full_path = self.knowledge_tuning_path / relative_path
            if not full_path.exists():
                return False
            return full_path.stat().st_size >= min_size

        def jsonl_has_records(self, relative_path: str, min_records: int = 1) -> bool:
            """Check if a JSONL file has minimum number of records."""
            import json

            full_path = self.knowledge_tuning_path / relative_path
            if not full_path.exists():
                return False

            count = 0
            with open(full_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            json.loads(line)
                            count += 1
                        except json.JSONDecodeError:
                            pass

            return count >= min_records

        def get_validation_report(self, expected_outputs: list) -> dict:
            """Generate a validation report for expected outputs."""
            report = {"passed": [], "failed": [], "all_passed": True}

            for output in expected_outputs:
                if self.file_exists(output) or self.dir_exists(output):
                    report["passed"].append(output)
                else:
                    report["failed"].append(output)
                    report["all_passed"] = False

            return report

    return OutputValidator()


@pytest.fixture(scope="session")
def gpu_available():
    """Check if GPU is available for testing."""
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False


@pytest.fixture(scope="session")
def execution_results():
    """
    Shared storage for execution results across tests.

    This allows later tests to check results from earlier steps.
    """
    return {}
