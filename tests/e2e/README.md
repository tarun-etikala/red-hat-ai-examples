# E2E Testing POC for RHOAI

This POC demonstrates different strategies for running E2E tests on Red Hat OpenShift AI (RHOAI) clusters.

## Overview

The POC implements four different execution strategies, each with different trade-offs:

| Strategy | Cluster Required | GPU Support | Use Case |
|----------|-----------------|-------------|----------|
| **Local Papermill** | No | Local only | Quick tests, CI without cluster |
| **Kubernetes Job** | Yes | Yes | Production-like E2E, isolated pods |
| **Jupyter Server API** | Yes | Workbench dependent | Interactive testing, debugging |
| **Remote Papermill** | Yes | Workbench dependent | Testing in existing workbenches |

## Quick Start

### 1. Set up credentials

```bash
# Get your RHOAI cluster credentials
export RHOAI_API_URL=$(oc whoami --show-server)
export RHOAI_TOKEN=$(oc whoami -t)
export RHOAI_NAMESPACE="your-test-namespace"
export RHOAI_VERIFY_SSL="false"  # Set to true for production clusters
```

### 2. Install dependencies

```bash
pip install kubernetes openshift-client papermill nbformat
```

### 3. Run POC tests

```bash
# Quick verification (requires credentials)
python scripts/run_e2e_poc.py --quick

# Run all POC tests
python scripts/run_e2e_poc.py --run-tests

# Run specific strategy tests
python scripts/run_e2e_poc.py --strategy connectivity
python scripts/run_e2e_poc.py --strategy local
python scripts/run_e2e_poc.py --strategy kubernetes
```

### 4. Run pytest directly

```bash
# Run all E2E tests
pytest tests/e2e/test_poc_strategies.py -v -s -m e2e

# Run quick verification
pytest tests/e2e/test_poc_strategies.py::test_poc_quick_verify -v -s

# Run connectivity tests
pytest tests/e2e/test_poc_strategies.py::TestClusterConnectivity -v -s

# Run project management tests
pytest tests/e2e/test_poc_strategies.py::TestProjectManagement -v -s

# Run strategy tests
pytest tests/e2e/test_poc_strategies.py::TestExecutionStrategies -v -s
```

## Test Structure

```text
tests/e2e/
├── __init__.py
├── conftest.py              # Pytest fixtures for RHOAI
├── test_poc_strategies.py   # POC test suite
├── env_example.txt          # Example environment variables
└── README.md                # This file

infrastructure/
├── rhoai/
│   ├── __init__.py
│   └── client.py            # RHOAI cluster client
├── notebook/
│   ├── __init__.py
│   └── executor.py          # Notebook execution strategies
└── config/
    └── cluster_profiles.yaml # Cluster configuration
```

## POC Tests

### 1. Cluster Connectivity Tests (`TestClusterConnectivity`)

- `test_cluster_config_from_env` - Load config from environment
- `test_cluster_connection` - Establish connection to RHOAI
- `test_get_cluster_info` - Retrieve cluster information
- `test_list_namespaces` - List accessible namespaces

### 2. Project Management Tests (`TestProjectManagement`)

- `test_create_data_science_project` - Create/delete DSP
- `test_namespace_isolation` - Verify namespace isolation

### 3. Execution Strategy Tests (`TestExecutionStrategies`)

- `test_local_papermill_strategy_initialization`
- `test_local_papermill_execution`
- `test_kubernetes_job_strategy_initialization`
- `test_kubernetes_job_execution_poc`
- `test_jupyter_server_strategy_initialization`
- `test_remote_papermill_strategy_initialization`

### 4. Strategy Comparison (`TestStrategyComparison`)

- `test_strategy_factory` - Test strategy factory function
- `test_strategy_comparison_report` - Generate comparison report

### 5. E2E Pipeline POC (`TestE2EPipelinePOC`)

- `test_e2e_connectivity_and_setup` - Verify all prerequisites
- `test_suggested_next_steps` - Output implementation roadmap

## Execution Strategies

### Local Papermill

```python
from infrastructure.notebook import LocalPapermillStrategy

strategy = LocalPapermillStrategy(kernel_name="python3")
result = strategy.execute(
    notebook_path=Path("my_notebook.ipynb"),
    output_path=Path("output.ipynb"),
    parameters={"param1": "value1"},
    timeout=3600,
)
```

### Kubernetes Job

```python
from infrastructure.rhoai import RHOAIClient, ClusterConfig
from infrastructure.notebook import KubernetesJobStrategy

config = ClusterConfig.from_env()
client = RHOAIClient(config)
client.connect()

strategy = KubernetesJobStrategy(
    rhoai_client=client,
    namespace="test-namespace",
    cpu="4",
    memory="16Gi",
    gpu=1,
)
```

### Jupyter Server API

```python
from infrastructure.notebook import JupyterServerStrategy

strategy = JupyterServerStrategy(
    server_url="https://workbench.apps.cluster.example.com",
    token="jupyter-token",
)
```

### Remote Papermill

```python
from infrastructure.notebook import RemotePapermillStrategy

strategy = RemotePapermillStrategy(
    rhoai_client=client,
    namespace="test-namespace",
    pod_name="workbench-pod-name",
)
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `RHOAI_API_URL` | Yes | OpenShift API URL |
| `RHOAI_TOKEN` | Yes | Bearer token for auth |
| `RHOAI_NAMESPACE` | No | Default namespace (default: `default`) |
| `RHOAI_VERIFY_SSL` | No | Verify SSL (default: `true`) |

## Next Steps

After verifying this POC works with your cluster:

1. **Workbench Management** - Implement RHOAI CRD-based workbench creation
2. **PVC Management** - Create PVCs for model/data storage
3. **GPU Scheduling** - Add GPU resource detection and scheduling
4. **Full Notebook Execution** - Upload notebooks and execute full pipelines
5. **Reporting** - Generate JUnit XML and artifact collection

See `TestE2EPipelinePOC.test_suggested_next_steps` for detailed roadmap.
