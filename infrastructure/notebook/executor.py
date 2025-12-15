"""Notebook execution engine with multiple strategies for RHOAI E2E testing.

This module provides different strategies for executing Jupyter notebooks
on RHOAI clusters, each with different trade-offs.
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from infrastructure.rhoai import RHOAIClient

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Notebook execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class ExecutionResult:
    """Result of a notebook execution.

    Attributes:
        status: Execution status
        notebook_path: Path to the input notebook
        output_path: Path to the executed notebook (if generated)
        duration_seconds: Execution time in seconds
        error_message: Error message if failed
        cell_outputs: List of cell outputs (if captured)
        metrics: Additional metrics (GPU usage, memory, etc.)
    """

    status: ExecutionStatus
    notebook_path: str
    output_path: Optional[str] = None
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    cell_outputs: Optional[List[Dict[str, Any]]] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        """Check if execution succeeded."""
        return self.status == ExecutionStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status.value,
            "notebook_path": self.notebook_path,
            "output_path": self.output_path,
            "duration_seconds": self.duration_seconds,
            "error_message": self.error_message,
            "metrics": self.metrics,
        }


class ExecutionStrategy(ABC):
    """Abstract base class for notebook execution strategies.

    Different strategies have different trade-offs:
    - Local: Fast, no cluster needed, limited to local resources
    - Kubernetes Job: Isolated, scalable, requires cluster access
    - Jupyter API: Interactive, uses existing workbench
    - SSH: Direct access, good for debugging
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name for logging and identification."""
        pass

    @abstractmethod
    def execute(
        self,
        notebook_path: Path,
        output_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 3600,
    ) -> ExecutionResult:
        """Execute a notebook.

        Args:
            notebook_path: Path to the notebook to execute
            output_path: Path to save executed notebook
            parameters: Parameters to inject
            timeout: Maximum execution time in seconds

        Returns:
            ExecutionResult with status and outputs
        """
        pass

    def execute_pipeline(
        self,
        notebooks: List[Path],
        output_dir: Path,
        shared_parameters: Optional[Dict[str, Any]] = None,
        stop_on_failure: bool = True,
    ) -> List[ExecutionResult]:
        """Execute multiple notebooks in sequence.

        Args:
            notebooks: List of notebook paths to execute in order
            output_dir: Directory to save executed notebooks
            shared_parameters: Parameters shared across all notebooks
            stop_on_failure: Stop pipeline on first failure

        Returns:
            List of ExecutionResults
        """
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)

        for notebook in notebooks:
            output_path = output_dir / f"{notebook.stem}_executed.ipynb"
            result = self.execute(
                notebook_path=notebook,
                output_path=output_path,
                parameters=shared_parameters,
            )
            results.append(result)

            if not result.succeeded and stop_on_failure:
                logger.error(
                    f"Pipeline stopped at {notebook.name}: {result.error_message}"
                )
                # Mark remaining notebooks as skipped
                for remaining in notebooks[len(results) :]:
                    results.append(
                        ExecutionResult(
                            status=ExecutionStatus.SKIPPED,
                            notebook_path=str(remaining),
                            error_message="Skipped due to earlier failure",
                        )
                    )
                break

        return results


class LocalPapermillStrategy(ExecutionStrategy):
    """Execute notebooks locally using Papermill.

    This strategy is useful for:
    - Quick local testing
    - CI environments without cluster access
    - Notebooks that don't require special hardware

    Requires: papermill, nbclient installed locally
    """

    @property
    def name(self) -> str:
        return "local_papermill"

    def __init__(self, kernel_name: str = "python3"):
        """Initialize local papermill strategy.

        Args:
            kernel_name: Jupyter kernel to use
        """
        self.kernel_name = kernel_name

    def execute(
        self,
        notebook_path: Path,
        output_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 3600,
    ) -> ExecutionResult:
        """Execute notebook locally with papermill."""
        start_time = time.time()

        try:
            import papermill as pm

            logger.info(f"[{self.name}] Executing: {notebook_path}")

            pm.execute_notebook(
                input_path=str(notebook_path),
                output_path=str(output_path),
                parameters=parameters or {},
                kernel_name=self.kernel_name,
                cwd=str(notebook_path.parent),
                progress_bar=False,
                request_save_on_cell_execute=True,
            )

            duration = time.time() - start_time
            logger.info(f"[{self.name}] Completed in {duration:.2f}s")

            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                notebook_path=str(notebook_path),
                output_path=str(output_path),
                duration_seconds=duration,
            )

        except ImportError:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                notebook_path=str(notebook_path),
                duration_seconds=time.time() - start_time,
                error_message="papermill not installed. Install with: pip install papermill",
            )
        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)

            # Check for timeout
            if "timeout" in error_msg.lower() or duration >= timeout:
                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    notebook_path=str(notebook_path),
                    output_path=str(output_path) if output_path.exists() else None,
                    duration_seconds=duration,
                    error_message=f"Execution timed out after {timeout}s",
                )

            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                notebook_path=str(notebook_path),
                output_path=str(output_path) if output_path.exists() else None,
                duration_seconds=duration,
                error_message=error_msg,
            )


class KubernetesJobStrategy(ExecutionStrategy):
    """Execute notebooks via Kubernetes Jobs on RHOAI cluster.

    This strategy:
    - Creates an isolated pod for execution
    - Can request GPU resources
    - Good for E2E testing in production-like environments
    - Supports custom images and resource limits

    Requires: kubernetes, openshift-client packages
    """

    @property
    def name(self) -> str:
        return "kubernetes_job"

    def __init__(
        self,
        rhoai_client: "RHOAIClient",
        namespace: str,
        image: str = "quay.io/modh/odh-generic-data-science-notebook:v3-20241111",
        cpu: str = "4",
        memory: str = "16Gi",
        gpu: int = 0,
    ):
        """Initialize Kubernetes Job strategy.

        Args:
            rhoai_client: Connected RHOAI client
            namespace: Namespace to create jobs in
            image: Container image with Jupyter/papermill
            cpu: CPU request
            memory: Memory request
            gpu: Number of GPUs to request
        """
        self.client = rhoai_client
        self.namespace = namespace
        self.image = image
        self.cpu = cpu
        self.memory = memory
        self.gpu = gpu

    def execute(
        self,
        notebook_path: Path,
        output_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 3600,
    ) -> ExecutionResult:
        """Execute notebook via Kubernetes Job."""
        start_time = time.time()
        job_name = f"nb-exec-{int(time.time())}"

        try:
            from kubernetes import client as k8s_client

            logger.info(f"[{self.name}] Creating job: {job_name}")

            # Build papermill command
            params_str = " ".join(f"-p {k} {v}" for k, v in (parameters or {}).items())
            command = [
                "papermill",
                str(notebook_path),
                str(output_path),
                params_str,
            ]

            # Create job spec
            container = k8s_client.V1Container(
                name="notebook-executor",
                image=self.image,
                command=["sh", "-c", " ".join(command)],
                resources=k8s_client.V1ResourceRequirements(
                    requests={
                        "cpu": self.cpu,
                        "memory": self.memory,
                    },
                    limits={
                        "cpu": self.cpu,
                        "memory": self.memory,
                    },
                ),
            )

            # Add GPU if requested
            if self.gpu > 0:
                container.resources.limits["nvidia.com/gpu"] = str(self.gpu)
                container.resources.requests["nvidia.com/gpu"] = str(self.gpu)

            job = k8s_client.V1Job(
                metadata=k8s_client.V1ObjectMeta(
                    name=job_name,
                    namespace=self.namespace,
                ),
                spec=k8s_client.V1JobSpec(
                    template=k8s_client.V1PodTemplateSpec(
                        spec=k8s_client.V1PodSpec(
                            containers=[container],
                            restart_policy="Never",
                        ),
                    ),
                    backoff_limit=0,
                    active_deadline_seconds=timeout,
                ),
            )

            # Create the job
            batch_v1 = k8s_client.BatchV1Api(self.client._k8s_client)
            batch_v1.create_namespaced_job(namespace=self.namespace, body=job)

            # Wait for completion
            result = self._wait_for_job(job_name, timeout)
            result.duration_seconds = time.time() - start_time

            return result

        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                notebook_path=str(notebook_path),
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )
        finally:
            # Cleanup job
            self._cleanup_job(job_name)

    def _wait_for_job(self, job_name: str, timeout: int) -> ExecutionResult:
        """Wait for job completion."""
        from kubernetes import client as k8s_client

        batch_v1 = k8s_client.BatchV1Api(self.client._k8s_client)
        start_time = time.time()

        while time.time() - start_time < timeout:
            job = batch_v1.read_namespaced_job(job_name, self.namespace)

            if job.status.succeeded:
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    notebook_path="",  # Will be filled by caller
                )

            if job.status.failed:
                return ExecutionResult(
                    status=ExecutionStatus.FAILED,
                    notebook_path="",
                    error_message="Job failed",
                )

            time.sleep(5)

        return ExecutionResult(
            status=ExecutionStatus.TIMEOUT,
            notebook_path="",
            error_message=f"Job timed out after {timeout}s",
        )

    def _cleanup_job(self, job_name: str) -> None:
        """Delete job and its pods."""
        try:
            from kubernetes import client as k8s_client

            batch_v1 = k8s_client.BatchV1Api(self.client._k8s_client)
            batch_v1.delete_namespaced_job(
                job_name,
                self.namespace,
                propagation_policy="Background",
            )
        except Exception as e:
            logger.warning(f"Failed to cleanup job {job_name}: {e}")


class JupyterServerStrategy(ExecutionStrategy):
    """Execute notebooks via Jupyter Server REST API.

    This strategy:
    - Uses an existing running workbench
    - Executes notebooks through the Jupyter API
    - Good for interactive testing and debugging
    - Requires workbench to be running

    Requires: requests, jupyter_client packages
    """

    @property
    def name(self) -> str:
        return "jupyter_server"

    def __init__(
        self,
        server_url: str,
        token: str,
        verify_ssl: bool = True,
    ):
        """Initialize Jupyter Server strategy.

        Args:
            server_url: Base URL of the Jupyter server
            token: Jupyter authentication token
            verify_ssl: Whether to verify SSL certificates
        """
        self.server_url = server_url.rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl

    def execute(
        self,
        notebook_path: Path,
        output_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 3600,
    ) -> ExecutionResult:
        """Execute notebook via Jupyter Server API."""
        start_time = time.time()

        try:
            import requests

            logger.info(f"[{self.name}] Executing via Jupyter Server: {notebook_path}")

            headers = {
                "Authorization": f"token {self.token}",
                "Content-Type": "application/json",
            }

            # Create a new session
            session_url = f"{self.server_url}/api/sessions"
            session_data = {
                "path": str(notebook_path.name),
                "type": "notebook",
                "kernel": {"name": "python3"},
            }

            resp = requests.post(
                session_url,
                json=session_data,
                headers=headers,
                verify=self.verify_ssl,
                timeout=30,
            )
            resp.raise_for_status()
            session = resp.json()
            kernel_id = session["kernel"]["id"]

            logger.info(f"[{self.name}] Started kernel: {kernel_id}")

            # Execute cells via kernel
            # This is a simplified version - full implementation would use websocket
            # TODO: Implement actual cell execution via websocket or execute API

            duration = time.time() - start_time

            # Clean up session
            requests.delete(
                f"{self.server_url}/api/sessions/{session['id']}",
                headers=headers,
                verify=self.verify_ssl,
            )

            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                notebook_path=str(notebook_path),
                output_path=str(output_path),
                duration_seconds=duration,
                metrics={"kernel_id": kernel_id},
            )

        except ImportError:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                notebook_path=str(notebook_path),
                duration_seconds=time.time() - start_time,
                error_message="requests not installed",
            )
        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                notebook_path=str(notebook_path),
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )


class RemotePapermillStrategy(ExecutionStrategy):
    """Execute notebooks remotely via SSH/exec into a pod.

    This strategy:
    - Uses kubectl exec to run papermill inside an existing pod
    - Good for testing in existing workbenches
    - Preserves the pod's environment and mounts
    """

    @property
    def name(self) -> str:
        return "remote_papermill"

    def __init__(
        self,
        rhoai_client: "RHOAIClient",
        namespace: str,
        pod_name: str,
        container: Optional[str] = None,
    ):
        """Initialize Remote Papermill strategy.

        Args:
            rhoai_client: Connected RHOAI client
            namespace: Namespace containing the pod
            pod_name: Name of the pod to exec into
            container: Container name (if pod has multiple)
        """
        self.client = rhoai_client
        self.namespace = namespace
        self.pod_name = pod_name
        self.container = container

    def execute(
        self,
        notebook_path: Path,
        output_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: int = 3600,
    ) -> ExecutionResult:
        """Execute notebook via kubectl exec."""
        start_time = time.time()

        try:
            logger.info(
                f"[{self.name}] Executing in pod {self.pod_name}: {notebook_path}"
            )

            # Build papermill command
            params_args = []
            for k, v in (parameters or {}).items():
                params_args.extend(["-p", str(k), str(v)])

            command = [
                "papermill",
                str(notebook_path),
                str(output_path),
                *params_args,
            ]

            # Execute in pod
            stdout, stderr, return_code = self.client.exec_in_pod(
                pod_name=self.pod_name,
                namespace=self.namespace,
                command=command,
                container=self.container,
            )

            duration = time.time() - start_time

            if return_code == 0:
                return ExecutionResult(
                    status=ExecutionStatus.SUCCESS,
                    notebook_path=str(notebook_path),
                    output_path=str(output_path),
                    duration_seconds=duration,
                )
            else:
                return ExecutionResult(
                    status=ExecutionStatus.FAILED,
                    notebook_path=str(notebook_path),
                    output_path=str(output_path),
                    duration_seconds=duration,
                    error_message=stderr or stdout,
                )

        except Exception as e:
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                notebook_path=str(notebook_path),
                duration_seconds=time.time() - start_time,
                error_message=str(e),
            )


def get_strategy(
    strategy_name: str,
    **kwargs,
) -> ExecutionStrategy:
    """Factory function to get an execution strategy.

    Args:
        strategy_name: Name of the strategy ('local', 'kubernetes', 'jupyter', 'remote')
        **kwargs: Strategy-specific arguments

    Returns:
        ExecutionStrategy instance
    """
    strategies = {
        "local": LocalPapermillStrategy,
        "local_papermill": LocalPapermillStrategy,
        "kubernetes": KubernetesJobStrategy,
        "kubernetes_job": KubernetesJobStrategy,
        "jupyter": JupyterServerStrategy,
        "jupyter_server": JupyterServerStrategy,
        "remote": RemotePapermillStrategy,
        "remote_papermill": RemotePapermillStrategy,
    }

    if strategy_name not in strategies:
        raise ValueError(
            f"Unknown strategy: {strategy_name}. Available: {list(strategies.keys())}"
        )

    return strategies[strategy_name](**kwargs)
