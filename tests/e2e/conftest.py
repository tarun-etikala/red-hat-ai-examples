"""Pytest fixtures for E2E tests on RHOAI cluster."""

import logging
import os
from pathlib import Path
from typing import Generator, Optional

import pytest

from infrastructure.notebook import ExecutionStrategy, get_strategy
from infrastructure.rhoai import ClusterConfig, ClusterConnectionError, RHOAIClient

logger = logging.getLogger(__name__)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "e2e: marks tests as E2E tests (require cluster)"
    )
    config.addinivalue_line("markers", "integration: marks integration tests")
    config.addinivalue_line(
        "markers", "strategy(name): marks test for specific execution strategy"
    )
    config.addinivalue_line("markers", "gpu: marks tests requiring GPU")


@pytest.fixture(scope="session")
def cluster_config() -> Optional[ClusterConfig]:
    """Get cluster configuration from environment.

    Required environment variables:
        RHOAI_API_URL: OpenShift API URL
        RHOAI_TOKEN: Bearer token for authentication

    Optional:
        RHOAI_NAMESPACE: Test namespace (default: 'e2e-test')
        RHOAI_VERIFY_SSL: Verify SSL (default: 'true')
    """
    try:
        config = ClusterConfig(
            api_url=os.environ.get("RHOAI_API_URL", ""),
            token=os.environ.get("RHOAI_TOKEN", ""),
            namespace=os.environ.get("RHOAI_NAMESPACE", "e2e-test"),
            verify_ssl=os.environ.get("RHOAI_VERIFY_SSL", "true").lower() == "true",
        )

        if not config.api_url or not config.token:
            pytest.skip(
                "RHOAI cluster credentials not configured. "
                "Set RHOAI_API_URL and RHOAI_TOKEN environment variables."
            )

        return config

    except Exception as e:
        pytest.skip(f"Failed to configure cluster: {e}")
        return None


@pytest.fixture(scope="session")
def rhoai_client(cluster_config: ClusterConfig) -> Generator[RHOAIClient, None, None]:
    """Create and connect RHOAI client.

    This fixture:
    1. Creates a client with the cluster config
    2. Establishes connection
    3. Yields the connected client
    4. Closes connection on teardown
    """
    if cluster_config is None:
        pytest.skip("No cluster configuration available")

    client = RHOAIClient(cluster_config)

    try:
        client.connect()
        yield client
    except ClusterConnectionError as e:
        pytest.skip(f"Could not connect to cluster: {e}")
    finally:
        client.close()


@pytest.fixture(scope="session")
def test_namespace(
    rhoai_client: RHOAIClient, cluster_config: ClusterConfig
) -> Generator[str, None, None]:
    """Create an isolated test namespace.

    Creates a unique namespace for the test session and cleans it up after.
    """
    import time

    namespace = f"e2e-test-{int(time.time())}"

    try:
        rhoai_client.create_data_science_project(
            name=namespace,
            display_name=f"E2E Test {time.strftime('%Y-%m-%d %H:%M')}",
        )
        logger.info(f"Created test namespace: {namespace}")

        yield namespace

    finally:
        # Cleanup
        try:
            rhoai_client.cleanup(namespace, wait=False)
            logger.info(f"Scheduled cleanup for namespace: {namespace}")
        except Exception as e:
            logger.warning(f"Failed to cleanup namespace {namespace}: {e}")


@pytest.fixture
def local_strategy() -> ExecutionStrategy:
    """Get local papermill execution strategy."""
    return get_strategy("local")


@pytest.fixture
def kubernetes_strategy(
    rhoai_client: RHOAIClient, test_namespace: str
) -> ExecutionStrategy:
    """Get Kubernetes Job execution strategy."""
    return get_strategy(
        "kubernetes",
        rhoai_client=rhoai_client,
        namespace=test_namespace,
    )


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    """Get temporary output directory for executed notebooks."""
    output = tmp_path / "notebook_outputs"
    output.mkdir(parents=True, exist_ok=True)
    return output


@pytest.fixture(scope="session")
def example_notebooks(repo_root: Path) -> dict:
    """Get paths to example notebooks organized by example."""
    examples = {}

    # Knowledge tuning notebooks
    kt_path = repo_root / "examples" / "knowledge-tuning"
    if kt_path.exists():
        examples["knowledge_tuning"] = {
            "base_evaluation": kt_path
            / "01_Base_Model_Evaluation"
            / "Base_Model_Evaluation.ipynb",
            "data_processing": kt_path / "02_Data_Processing" / "Data_Processing.ipynb",
            "knowledge_generation": kt_path
            / "03_Knowledge_Generation"
            / "Knowledge_Generation.ipynb",
            "knowledge_mixing": kt_path
            / "04_Knowledge_Mixing"
            / "Knowledge_Mixing.ipynb",
            "model_training": kt_path / "05_Model_Training" / "Model_Training.ipynb",
            "evaluation": kt_path / "06_Evaluation" / "Evaluation.ipynb",
        }

    # Fine-tuning notebooks
    ft_path = repo_root / "examples" / "fine-tuning"
    if ft_path.exists():
        examples["fine_tuning"] = {
            "osft": ft_path / "osft" / "osft-example.ipynb",
            "sft": ft_path / "training-hub" / "sft" / "sft.ipynb",
        }

    # LLMCompressor notebook
    llmc_path = repo_root / "examples" / "llmcompressor"
    if llmc_path.exists():
        examples["llmcompressor"] = {
            "workbench": llmc_path / "workbench_example.ipynb",
        }

    return examples


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Get repository root path."""
    return Path(__file__).parent.parent.parent
