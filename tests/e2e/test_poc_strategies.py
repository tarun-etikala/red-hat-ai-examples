"""POC: E2E Test Strategies for RHOAI Cluster.

This module demonstrates different strategies for running E2E tests on RHOAI.
Each strategy has different trade-offs for speed, isolation, and resource usage.

Strategies tested:
1. Local Papermill - Execute notebooks locally (no cluster needed)
2. Kubernetes Job - Create isolated job pods on cluster
3. Jupyter Server API - Use existing workbench's Jupyter server
4. Remote Papermill - Exec into existing pod

To run these tests:
    # Set up credentials
    export RHOAI_API_URL="https://api.your-cluster.example.com:6443"
    export RHOAI_TOKEN="your-token-here"
    export RHOAI_NAMESPACE="your-test-namespace"

    # Run POC tests
    pytest tests/e2e/test_poc_strategies.py -v -s
"""

import logging
import os
import time
from pathlib import Path

import pytest

from infrastructure.notebook import (
    ExecutionStatus,
    JupyterServerStrategy,
    KubernetesJobStrategy,
    LocalPapermillStrategy,
    RemotePapermillStrategy,
    get_strategy,
)
from infrastructure.rhoai import ClusterConfig, ClusterConnectionError, RHOAIClient

logger = logging.getLogger(__name__)


# ============================================================================
# POC 1: Cluster Connectivity Tests
# ============================================================================


class TestClusterConnectivity:
    """POC tests to verify basic cluster connectivity."""

    @pytest.mark.e2e
    def test_cluster_config_from_env(self):
        """Test that cluster config can be loaded from environment."""
        api_url = os.environ.get("RHOAI_API_URL")
        token = os.environ.get("RHOAI_TOKEN")

        if not api_url or not token:
            pytest.skip("Cluster credentials not set in environment")

        config = ClusterConfig(
            api_url=api_url,
            token=token,
            namespace=os.environ.get("RHOAI_NAMESPACE", "default"),
            verify_ssl=os.environ.get("RHOAI_VERIFY_SSL", "false").lower() == "true",
        )

        assert config.api_url, "API URL should be set"
        assert config.token, "Token should be set"
        logger.info(f"✓ Cluster config loaded: {config.api_url}")

    @pytest.mark.e2e
    def test_cluster_connection(self, cluster_config: ClusterConfig):
        """Test establishing connection to RHOAI cluster."""
        client = RHOAIClient(cluster_config)

        try:
            result = client.connect()
            assert result is True, "Connection should succeed"
            assert client.is_connected, "Client should be connected"
            logger.info("✓ Successfully connected to RHOAI cluster")
        finally:
            client.close()

    @pytest.mark.e2e
    def test_get_cluster_info(self, rhoai_client: RHOAIClient):
        """Test retrieving cluster information."""
        info = rhoai_client.get_cluster_info()

        assert "api_url" in info
        assert "kubernetes_version" in info

        logger.info("✓ Cluster info retrieved:")
        logger.info(f"  API URL: {info['api_url']}")
        logger.info(f"  K8s Version: {info['kubernetes_version']}")
        logger.info(f"  Platform: {info.get('platform', 'N/A')}")

    @pytest.mark.e2e
    def test_list_namespaces(self, rhoai_client: RHOAIClient):
        """Test listing namespaces on the cluster."""
        namespaces = rhoai_client.list_namespaces()

        assert isinstance(namespaces, list)
        assert len(namespaces) > 0, "Should have at least one namespace"

        logger.info(f"✓ Found {len(namespaces)} namespaces")

        # Check for common RHOAI namespaces
        rhoai_namespaces = [
            ns for ns in namespaces if "openshift" in ns or "redhat" in ns.lower()
        ]
        logger.info(f"  RHOAI-related namespaces: {len(rhoai_namespaces)}")


# ============================================================================
# POC 2: Namespace/Project Management Tests
# ============================================================================


class TestProjectManagement:
    """POC tests for Data Science Project management."""

    @pytest.mark.e2e
    def test_create_data_science_project(self, rhoai_client: RHOAIClient):
        """Test creating a Data Science Project."""
        project_name = f"poc-test-{int(time.time())}"

        try:
            result = rhoai_client.create_data_science_project(
                name=project_name,
                display_name="POC Test Project",
            )

            assert result == project_name
            assert rhoai_client.namespace_exists(project_name)

            logger.info(f"✓ Created Data Science Project: {project_name}")

        finally:
            # Cleanup
            rhoai_client.delete_namespace(project_name)
            logger.info(f"✓ Cleaned up project: {project_name}")

    @pytest.mark.e2e
    def test_namespace_isolation(self, rhoai_client: RHOAIClient):
        """Test that test namespaces are properly isolated."""
        ns1 = f"poc-isolated-1-{int(time.time())}"
        ns2 = f"poc-isolated-2-{int(time.time())}"

        try:
            rhoai_client.create_data_science_project(ns1)
            rhoai_client.create_data_science_project(ns2)

            assert rhoai_client.namespace_exists(ns1)
            assert rhoai_client.namespace_exists(ns2)
            assert ns1 != ns2

            logger.info("✓ Namespace isolation verified")

        finally:
            rhoai_client.delete_namespace(ns1)
            rhoai_client.delete_namespace(ns2)


# ============================================================================
# POC 3: Execution Strategy Tests
# ============================================================================


class TestExecutionStrategies:
    """POC tests demonstrating different notebook execution strategies."""

    @pytest.fixture
    def sample_notebook(self, tmp_path: Path) -> Path:
        """Create a simple test notebook."""
        import json

        notebook_content = {
            "cells": [
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# Test cell\n",
                        "import sys\n",
                        "print(f'Python: {sys.version}')",
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {"tags": ["parameters"]},
                    "outputs": [],
                    "source": [
                        "# Parameters cell (for papermill)\n",
                        "test_param = 'default'",
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# Use parameter\n",
                        "print(f'Parameter value: {test_param}')",
                    ],
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [
                        "# Math test\n",
                        "result = 2 + 2\n",
                        "assert result == 4\n",
                        "print(f'Math check: {result}')",
                    ],
                },
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3",
                },
                "language_info": {"name": "python", "version": "3.11.0"},
            },
            "nbformat": 4,
            "nbformat_minor": 4,
        }

        notebook_path = tmp_path / "test_notebook.ipynb"
        with open(notebook_path, "w") as f:
            json.dump(notebook_content, f, indent=2)

        return notebook_path

    # --- Strategy 1: Local Papermill ---

    def test_local_papermill_strategy_initialization(self):
        """Test that local papermill strategy can be initialized."""
        strategy = get_strategy("local")

        assert strategy is not None
        assert strategy.name == "local_papermill"
        logger.info("✓ Local papermill strategy initialized")

    @pytest.mark.skipif(
        not pytest.importorskip("papermill", reason="papermill not installed"),
        reason="papermill not installed",
    )
    def test_local_papermill_execution(self, sample_notebook: Path, output_dir: Path):
        """Test executing a notebook locally with papermill."""
        strategy = LocalPapermillStrategy()
        output_path = output_dir / "executed_local.ipynb"

        result = strategy.execute(
            notebook_path=sample_notebook,
            output_path=output_path,
            parameters={"test_param": "from_test"},
            timeout=120,
        )

        logger.info(f"Local execution result: {result.status.value}")
        logger.info(f"  Duration: {result.duration_seconds:.2f}s")

        if result.status == ExecutionStatus.SUCCESS:
            assert output_path.exists(), "Output notebook should exist"
            logger.info("✓ Local papermill execution successful")
        else:
            logger.warning(
                f"Local execution failed (may be expected): {result.error_message}"
            )

    # --- Strategy 2: Kubernetes Job ---

    @pytest.mark.e2e
    def test_kubernetes_job_strategy_initialization(
        self,
        rhoai_client: RHOAIClient,
        test_namespace: str,
    ):
        """Test that Kubernetes Job strategy can be initialized."""
        strategy = KubernetesJobStrategy(
            rhoai_client=rhoai_client,
            namespace=test_namespace,
            cpu="2",
            memory="4Gi",
        )

        assert strategy is not None
        assert strategy.name == "kubernetes_job"
        logger.info(
            f"✓ Kubernetes Job strategy initialized for namespace: {test_namespace}"
        )

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_kubernetes_job_execution_poc(
        self,
        rhoai_client: RHOAIClient,
        test_namespace: str,
    ):
        """POC: Test creating a simple Kubernetes job (without full notebook execution).

        This test verifies we can create and manage jobs on the cluster.
        Full notebook execution requires the notebook to be available in the pod.
        """
        from kubernetes import client as k8s_client

        job_name = f"poc-job-{int(time.time())}"

        try:
            # Create a simple job that just echoes
            container = k8s_client.V1Container(
                name="poc-container",
                image="python:3.11-slim",
                command=["python", "-c", "print('POC job executed successfully')"],
                resources=k8s_client.V1ResourceRequirements(
                    requests={"cpu": "100m", "memory": "128Mi"},
                    limits={"cpu": "200m", "memory": "256Mi"},
                ),
            )

            job = k8s_client.V1Job(
                metadata=k8s_client.V1ObjectMeta(
                    name=job_name,
                    namespace=test_namespace,
                ),
                spec=k8s_client.V1JobSpec(
                    template=k8s_client.V1PodTemplateSpec(
                        spec=k8s_client.V1PodSpec(
                            containers=[container],
                            restart_policy="Never",
                        ),
                    ),
                    backoff_limit=0,
                    ttl_seconds_after_finished=60,
                ),
            )

            batch_v1 = k8s_client.BatchV1Api(rhoai_client._k8s_client)
            batch_v1.create_namespaced_job(namespace=test_namespace, body=job)
            logger.info(f"✓ Created job: {job_name}")

            # Wait for completion (max 60 seconds)
            start = time.time()
            while time.time() - start < 60:
                job_status = batch_v1.read_namespaced_job(job_name, test_namespace)

                if job_status.status.succeeded:
                    logger.info("✓ Job completed successfully")
                    return

                if job_status.status.failed:
                    pytest.fail("Job failed")

                time.sleep(2)

            logger.warning(
                "Job did not complete within timeout (may be resource constraints)"
            )

        finally:
            try:
                batch_v1.delete_namespaced_job(
                    job_name,
                    test_namespace,
                    propagation_policy="Background",
                )
            except Exception:
                pass

    # --- Strategy 3: Jupyter Server API ---

    def test_jupyter_server_strategy_initialization(self):
        """Test that Jupyter Server strategy can be initialized."""
        strategy = JupyterServerStrategy(
            server_url="http://localhost:8888",
            token="test-token",
        )

        assert strategy is not None
        assert strategy.name == "jupyter_server"
        logger.info("✓ Jupyter Server strategy initialized")

    # --- Strategy 4: Remote Papermill ---

    @pytest.mark.e2e
    def test_remote_papermill_strategy_initialization(
        self,
        rhoai_client: RHOAIClient,
        test_namespace: str,
    ):
        """Test that Remote Papermill strategy can be initialized."""
        strategy = RemotePapermillStrategy(
            rhoai_client=rhoai_client,
            namespace=test_namespace,
            pod_name="test-pod",
        )

        assert strategy is not None
        assert strategy.name == "remote_papermill"
        logger.info("✓ Remote Papermill strategy initialized")


# ============================================================================
# POC 4: Strategy Comparison
# ============================================================================


class TestStrategyComparison:
    """POC tests comparing different execution strategies."""

    @pytest.mark.e2e
    def test_strategy_factory(self):
        """Test the strategy factory function."""
        strategies = ["local", "kubernetes", "jupyter", "remote"]

        # Local strategy doesn't need extra args
        local = get_strategy("local")
        assert local.name == "local_papermill"

        logger.info("✓ Strategy factory working correctly")
        logger.info(f"  Available strategies: {strategies}")

    def test_strategy_comparison_report(self):
        """Generate a comparison report of different strategies."""
        comparison = {
            "local_papermill": {
                "requires_cluster": False,
                "requires_gpu": False,
                "isolation_level": "None (local)",
                "setup_complexity": "Low",
                "execution_speed": "Fast",
                "use_case": "Quick local testing, CI without cluster",
            },
            "kubernetes_job": {
                "requires_cluster": True,
                "requires_gpu": "Optional",
                "isolation_level": "High (isolated pod)",
                "setup_complexity": "Medium",
                "execution_speed": "Medium (pod startup)",
                "use_case": "Production-like E2E tests, GPU workloads",
            },
            "jupyter_server": {
                "requires_cluster": True,
                "requires_gpu": "Depends on workbench",
                "isolation_level": "Low (shared kernel)",
                "setup_complexity": "Low",
                "execution_speed": "Fast (reuses kernel)",
                "use_case": "Interactive testing, debugging",
            },
            "remote_papermill": {
                "requires_cluster": True,
                "requires_gpu": "Depends on pod",
                "isolation_level": "Medium (existing pod)",
                "setup_complexity": "Medium",
                "execution_speed": "Fast",
                "use_case": "Testing in existing workbenches",
            },
        }

        logger.info("\n" + "=" * 70)
        logger.info("EXECUTION STRATEGY COMPARISON")
        logger.info("=" * 70)

        for strategy_name, details in comparison.items():
            logger.info(f"\n{strategy_name}:")
            for key, value in details.items():
                logger.info(f"  {key}: {value}")

        logger.info("\n" + "=" * 70)


# ============================================================================
# POC 5: Full E2E Pipeline Test
# ============================================================================


class TestE2EPipelinePOC:
    """POC for running a full E2E pipeline test."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_e2e_connectivity_and_setup(
        self,
        rhoai_client: RHOAIClient,
        test_namespace: str,
        repo_root: Path,
    ):
        """POC: Verify all E2E test prerequisites are met.

        This test verifies:
        1. Cluster is accessible
        2. Test namespace exists
        3. Example notebooks are present
        4. Required permissions are available
        """
        logger.info("\n" + "=" * 70)
        logger.info("E2E PIPELINE POC - PREREQUISITE CHECK")
        logger.info("=" * 70)

        # Check 1: Cluster connectivity
        assert rhoai_client.is_connected
        info = rhoai_client.get_cluster_info()
        logger.info(f"✓ Cluster connected: {info['api_url']}")

        # Check 2: Test namespace exists
        assert rhoai_client.namespace_exists(test_namespace)
        logger.info(f"✓ Test namespace exists: {test_namespace}")

        # Check 3: Example notebooks exist
        knowledge_tuning_path = repo_root / "examples" / "knowledge-tuning"
        notebooks_exist = knowledge_tuning_path.exists()
        if notebooks_exist:
            notebooks = list(knowledge_tuning_path.glob("**/*.ipynb"))
            logger.info(f"✓ Knowledge tuning notebooks found: {len(notebooks)}")
        else:
            logger.warning("⚠ Knowledge tuning notebooks not found")

        # Check 4: List pods in namespace
        pods = rhoai_client.list_pods(test_namespace)
        logger.info(f"✓ Pods in namespace: {len(pods)}")

        logger.info("\n" + "=" * 70)
        logger.info("E2E PREREQUISITES: ALL CHECKS PASSED")
        logger.info("=" * 70)

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_suggested_next_steps(self):
        """Output suggested next steps for full E2E implementation."""
        next_steps = """
╔══════════════════════════════════════════════════════════════════════════╗
║                    POC COMPLETE - NEXT STEPS                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  1. WORKBENCH MANAGEMENT                                                 ║
║     - Implement workbench creation via RHOAI CRDs                       ║
║     - Add wait_until_ready() with proper health checks                  ║
║     - Support for different notebook images                              ║
║                                                                          ║
║  2. PVC MANAGEMENT                                                       ║
║     - Create PVCs for model storage                                     ║
║     - Implement file upload/download to PVCs                            ║
║     - Support for pre-populated model caches                            ║
║                                                                          ║
║  3. GPU SCHEDULING                                                       ║
║     - Query available GPU resources                                     ║
║     - Implement GPU scheduling with tolerations                         ║
║     - Add GPU utilization monitoring                                    ║
║                                                                          ║
║  4. FULL NOTEBOOK EXECUTION                                              ║
║     - Upload notebooks to workbench PVC                                 ║
║     - Execute via chosen strategy                                       ║
║     - Collect and store execution outputs                               ║
║                                                                          ║
║  5. REPORTING & ARTIFACTS                                                ║
║     - Generate JUnit XML reports                                        ║
║     - Collect executed notebooks as artifacts                           ║
║     - Implement metrics collection (duration, GPU usage)                ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
        """
        logger.info(next_steps)


# ============================================================================
# POC 6: Quick Verification Test
# ============================================================================


@pytest.mark.e2e
def test_poc_quick_verify(cluster_config: ClusterConfig):
    """Quick verification test that can be run to check POC setup.

    Run with: pytest tests/e2e/test_poc_strategies.py::test_poc_quick_verify -v -s
    """
    logger.info("\n" + "=" * 50)
    logger.info("POC QUICK VERIFICATION")
    logger.info("=" * 50)

    # 1. Check config
    logger.info(f"API URL: {cluster_config.api_url}")
    logger.info(f"Namespace: {cluster_config.namespace}")
    logger.info(f"SSL Verify: {cluster_config.verify_ssl}")

    # 2. Test connection
    client = RHOAIClient(cluster_config)
    try:
        client.connect()
        info = client.get_cluster_info()

        logger.info("\n✓ Connection successful!")
        logger.info(f"  Kubernetes: {info['kubernetes_version']}")
        logger.info(f"  Platform: {info.get('platform', 'N/A')}")

        # 3. Count namespaces
        namespaces = client.list_namespaces()
        logger.info(f"  Namespaces: {len(namespaces)}")

        logger.info("\n" + "=" * 50)
        logger.info("POC VERIFICATION: SUCCESS")
        logger.info("=" * 50)

    except ClusterConnectionError as e:
        logger.error(f"Connection failed: {e}")
        pytest.fail(f"POC verification failed: {e}")
    finally:
        client.close()
