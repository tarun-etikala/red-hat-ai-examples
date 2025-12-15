"""RHOAI Cluster Client for E2E test automation.

This module provides a client for interacting with Red Hat OpenShift AI clusters.
It handles authentication, namespace management, and workbench operations.
"""

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ClusterConnectionError(Exception):
    """Raised when cluster connection fails."""


class WorkbenchError(Exception):
    """Raised when workbench operations fail."""


@dataclass
class ClusterConfig:
    """RHOAI cluster configuration.

    Attributes:
        api_url: The OpenShift API server URL (e.g., https://api.cluster.example.com:6443)
        token: Bearer token for authentication
        namespace: Default namespace for operations
        verify_ssl: Whether to verify SSL certificates (default True)
    """

    api_url: str
    token: str
    namespace: str = "default"
    verify_ssl: bool = True

    @classmethod
    def from_env(cls) -> "ClusterConfig":
        """Create ClusterConfig from environment variables.

        Required env vars:
            RHOAI_API_URL: OpenShift API URL
            RHOAI_TOKEN: Bearer token

        Optional env vars:
            RHOAI_NAMESPACE: Namespace (default: 'default')
            RHOAI_VERIFY_SSL: Verify SSL ('true'/'false', default: 'true')
        """
        api_url = os.environ.get("RHOAI_API_URL")
        token = os.environ.get("RHOAI_TOKEN")

        if not api_url or not token:
            raise ValueError(
                "Missing required environment variables: RHOAI_API_URL and RHOAI_TOKEN"
            )

        return cls(
            api_url=api_url,
            token=token,
            namespace=os.environ.get("RHOAI_NAMESPACE", "default"),
            verify_ssl=os.environ.get("RHOAI_VERIFY_SSL", "true").lower() == "true",
        )


@dataclass
class WorkbenchSpec:
    """Specification for creating a workbench.

    Attributes:
        name: Workbench name
        image: Container image for the workbench
        cpu: CPU request (e.g., "4")
        memory: Memory request (e.g., "16Gi")
        gpu: Number of GPUs (0 for none)
        gpu_type: GPU resource type (e.g., "nvidia.com/gpu")
        storage_size: PVC size for workspace (e.g., "50Gi")
        env_vars: Environment variables to set
    """

    name: str
    image: str = "quay.io/modh/odh-generic-data-science-notebook:v3-20241111"
    cpu: str = "4"
    memory: str = "16Gi"
    gpu: int = 0
    gpu_type: str = "nvidia.com/gpu"
    storage_size: str = "50Gi"
    env_vars: Dict[str, str] = field(default_factory=dict)


class WorkbenchStatus(Enum):
    """Workbench pod status."""

    PENDING = "pending"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


class RHOAIClient:
    """Client for interacting with RHOAI cluster.

    This client provides methods for:
    - Connecting to RHOAI clusters
    - Managing Data Science Projects (namespaces)
    - Creating and managing Workbenches
    - Executing operations within workbenches

    Example:
        >>> config = ClusterConfig.from_env()
        >>> client = RHOAIClient(config)
        >>> client.connect()
        >>> project = client.create_data_science_project("test-project")
    """

    def __init__(self, config: ClusterConfig):
        """Initialize the RHOAI client.

        Args:
            config: Cluster configuration
        """
        self.config = config
        self._k8s_client = None
        self._dyn_client = None
        self._connected = False

    def connect(self) -> bool:
        """Establish connection to the RHOAI cluster.

        Returns:
            True if connection successful

        Raises:
            ClusterConnectionError: If connection fails
        """
        try:
            from kubernetes import client
            from openshift.dynamic import DynamicClient

            # Configure kubernetes client
            configuration = client.Configuration()
            configuration.host = self.config.api_url
            configuration.api_key = {"authorization": f"Bearer {self.config.token}"}
            configuration.verify_ssl = self.config.verify_ssl

            if not self.config.verify_ssl:
                import urllib3

                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            self._k8s_client = client.ApiClient(configuration)
            self._dyn_client = DynamicClient(self._k8s_client)

            # Test connection by getting cluster version
            version_api = client.VersionApi(self._k8s_client)
            version_info = version_api.get_code()

            logger.info(f"Connected to RHOAI cluster: {self.config.api_url}")
            logger.info(f"Kubernetes version: {version_info.git_version}")

            self._connected = True
            return True

        except ImportError as e:
            raise ClusterConnectionError(
                f"Required packages not installed: {e}. "
                "Install with: pip install kubernetes openshift-client"
            ) from e
        except Exception as e:
            raise ClusterConnectionError(f"Failed to connect to cluster: {e}") from e

    @property
    def is_connected(self) -> bool:
        """Check if client is connected to cluster."""
        return self._connected

    def get_cluster_info(self) -> Dict[str, Any]:
        """Get basic cluster information.

        Returns:
            Dictionary with cluster info (version, api_url, etc.)
        """
        if not self._connected:
            raise ClusterConnectionError("Not connected. Call connect() first.")

        from kubernetes import client

        version_api = client.VersionApi(self._k8s_client)
        version_info = version_api.get_code()

        return {
            "api_url": self.config.api_url,
            "kubernetes_version": version_info.git_version,
            "platform": version_info.platform,
            "build_date": version_info.build_date,
        }

    def list_namespaces(self) -> list:
        """List all accessible namespaces.

        Returns:
            List of namespace names
        """
        if not self._connected:
            raise ClusterConnectionError("Not connected. Call connect() first.")

        from kubernetes import client

        core_v1 = client.CoreV1Api(self._k8s_client)
        namespaces = core_v1.list_namespace()

        return [ns.metadata.name for ns in namespaces.items]

    def namespace_exists(self, namespace: str) -> bool:
        """Check if a namespace exists.

        Args:
            namespace: Namespace name to check

        Returns:
            True if namespace exists
        """
        if not self._connected:
            raise ClusterConnectionError("Not connected. Call connect() first.")

        from kubernetes import client
        from kubernetes.client.rest import ApiException

        core_v1 = client.CoreV1Api(self._k8s_client)
        try:
            core_v1.read_namespace(namespace)
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            raise

    def create_data_science_project(
        self, name: str, display_name: Optional[str] = None
    ) -> str:
        """Create a Data Science Project (namespace with RHOAI labels).

        Args:
            name: Project/namespace name
            display_name: Optional display name

        Returns:
            Created namespace name
        """
        if not self._connected:
            raise ClusterConnectionError("Not connected. Call connect() first.")

        from kubernetes import client
        from kubernetes.client.rest import ApiException

        core_v1 = client.CoreV1Api(self._k8s_client)

        # Create namespace with RHOAI annotations
        namespace = client.V1Namespace(
            metadata=client.V1ObjectMeta(
                name=name,
                labels={
                    "opendatahub.io/dashboard": "true",
                    "modelmesh-enabled": "true",
                },
                annotations={
                    "openshift.io/display-name": display_name or name,
                    "openshift.io/description": f"Test project: {name}",
                },
            )
        )

        try:
            core_v1.create_namespace(namespace)
            logger.info(f"Created Data Science Project: {name}")
            return name
        except ApiException as e:
            if e.status == 409:  # Already exists
                logger.info(f"Data Science Project already exists: {name}")
                return name
            raise

    def delete_namespace(self, namespace: str) -> bool:
        """Delete a namespace.

        Args:
            namespace: Namespace to delete

        Returns:
            True if deleted or didn't exist
        """
        if not self._connected:
            raise ClusterConnectionError("Not connected. Call connect() first.")

        from kubernetes import client
        from kubernetes.client.rest import ApiException

        core_v1 = client.CoreV1Api(self._k8s_client)

        try:
            core_v1.delete_namespace(namespace)
            logger.info(f"Deleted namespace: {namespace}")
            return True
        except ApiException as e:
            if e.status == 404:
                return True
            raise

    def get_workbench_status(self, name: str, namespace: str) -> WorkbenchStatus:
        """Get the status of a workbench.

        Args:
            name: Workbench name
            namespace: Namespace containing the workbench

        Returns:
            WorkbenchStatus enum value
        """
        if not self._connected:
            raise ClusterConnectionError("Not connected. Call connect() first.")

        from kubernetes import client
        from kubernetes.client.rest import ApiException

        core_v1 = client.CoreV1Api(self._k8s_client)

        try:
            # Workbenches are typically StatefulSets with specific labels
            pod_list = core_v1.list_namespaced_pod(
                namespace=namespace, label_selector=f"notebook-name={name}"
            )

            if not pod_list.items:
                return WorkbenchStatus.STOPPED

            pod = pod_list.items[0]
            phase = pod.status.phase

            if phase == "Running":
                return WorkbenchStatus.RUNNING
            elif phase == "Pending":
                return WorkbenchStatus.PENDING
            elif phase in ("Failed", "Unknown"):
                return WorkbenchStatus.FAILED
            else:
                return WorkbenchStatus.UNKNOWN

        except ApiException:
            return WorkbenchStatus.UNKNOWN

    def list_pods(self, namespace: str, label_selector: Optional[str] = None) -> list:
        """List pods in a namespace.

        Args:
            namespace: Namespace to list pods from
            label_selector: Optional label selector

        Returns:
            List of pod information dicts
        """
        if not self._connected:
            raise ClusterConnectionError("Not connected. Call connect() first.")

        from kubernetes import client

        core_v1 = client.CoreV1Api(self._k8s_client)

        if label_selector:
            pods = core_v1.list_namespaced_pod(namespace, label_selector=label_selector)
        else:
            pods = core_v1.list_namespaced_pod(namespace)

        return [
            {
                "name": pod.metadata.name,
                "status": pod.status.phase,
                "labels": pod.metadata.labels or {},
                "created": pod.metadata.creation_timestamp,
            }
            for pod in pods.items
        ]

    def exec_in_pod(
        self,
        pod_name: str,
        namespace: str,
        command: list,
        container: Optional[str] = None,
    ) -> tuple:
        """Execute a command in a pod.

        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            command: Command to execute as list
            container: Optional container name

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        if not self._connected:
            raise ClusterConnectionError("Not connected. Call connect() first.")

        from kubernetes import client
        from kubernetes.stream import stream

        core_v1 = client.CoreV1Api(self._k8s_client)

        kwargs = {
            "name": pod_name,
            "namespace": namespace,
            "command": command,
            "stderr": True,
            "stdin": False,
            "stdout": True,
            "tty": False,
        }

        if container:
            kwargs["container"] = container

        resp = stream(core_v1.connect_get_namespaced_pod_exec, **kwargs)

        # The stream response contains the output
        return resp, "", 0

    def cleanup(self, namespace: str, wait: bool = True, timeout: int = 120) -> None:
        """Clean up test resources by deleting namespace.

        Args:
            namespace: Namespace to clean up
            wait: Wait for namespace to be fully deleted
            timeout: Timeout in seconds when waiting
        """
        self.delete_namespace(namespace)

        if wait:
            start_time = time.time()
            while time.time() - start_time < timeout:
                if not self.namespace_exists(namespace):
                    logger.info(f"Namespace {namespace} fully deleted")
                    return
                time.sleep(2)

            logger.warning(f"Timeout waiting for namespace {namespace} deletion")

    def close(self) -> None:
        """Close the client connection."""
        if self._k8s_client:
            self._k8s_client.close()
        self._connected = False
        logger.info("Closed RHOAI client connection")
