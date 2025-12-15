# E2E Integration Testing Plan for RHOAI Cluster

## Executive Summary

This document outlines a comprehensive plan for creating, automating, executing, and reviewing E2E integration tests for notebook-based examples on Red Hat OpenShift AI (RHOAI) clusters. The infrastructure is designed to be reusable, extensible, and maintainable for all current and future examples.

---

## Table of Contents

1. [Test Coverage Strategy](#1-test-coverage-strategy)
2. [Environment Considerations](#2-environment-considerations)
3. [Hardware Requirements](#3-hardware-requirements)
4. [Test Result Storage](#4-test-result-storage)
5. [Architecture Overview](#5-architecture-overview)
6. [Folder Structure](#6-folder-structure)
7. [Implementation Details](#7-implementation-details)
8. [Forked PR Workflow](#8-forked-pr-workflow)
9. [Implementation Tasks](#9-implementation-tasks)

---

## 1. Test Coverage Strategy

### 1.1 Test Pyramid for RHOAI Examples

```text
                    ╭─────────────────────╮
                    │   E2E RHOAI Tests   │  ← Expensive, Slow, High Fidelity
                    │   (Full Pipeline)   │
                    ╰─────────────────────╯
               ╭─────────────────────────────────╮
               │    Integration Tests             │  ← GPU Required, Medium Speed
               │    (Individual Notebooks)        │
               ╰─────────────────────────────────╯
          ╭─────────────────────────────────────────────╮
          │         Smoke Tests                          │  ← Fast, No GPU
          │         (Structure, Imports, Dependencies)   │
          ╰─────────────────────────────────────────────╯
     ╭─────────────────────────────────────────────────────────╮
     │              Validation Tests (Static Analysis)          │  ← Fastest, No Resources
     │              (Syntax, Metadata, Content Cleanliness)     │
     ╰─────────────────────────────────────────────────────────╯
```

### 1.2 Test Coverage by Trigger

| Trigger | Validation | Smoke | Integration | Full E2E Pipeline |
|---------|------------|-------|-------------|-------------------|
| **PR (Forked)** | ✅ All | ✅ All | ❌ Skip* | ❌ Skip |
| **PR (Trusted)** | ✅ All | ✅ All | ⚡ Selective** | ❌ Skip |
| **Nightly** | ✅ All | ✅ All | ✅ All Examples | ✅ All Examples |
| **Release** | ✅ All | ✅ All | ✅ All Examples | ✅ All Examples + Multi-env |
| **Manual** | Configurable | Configurable | Configurable | Configurable |

**\* Reasoning for PR coverage:**

- **Forked PRs**: Cannot access cluster secrets securely. Run only local tests (validation + smoke).
- **Trusted PRs**: Run selective integration tests on notebooks that changed.
- Security: Cluster credentials should never be exposed to forked PR workflows.

**\*\* Selective Integration:**

- Only test notebooks/examples that have changes in the PR
- Use path-based filtering to determine affected examples
- Skip expensive GPU tests if only documentation changed

### 1.3 Test Types Detailed

#### Validation Tests (PR Blocking)

- **Purpose**: Catch syntax errors, structural issues, metadata problems
- **Runtime**: < 1 minute
- **Resources**: None (runs on GitHub Actions runner)
- **When**: Every PR, every push

#### Smoke Tests (PR Blocking)

- **Purpose**: Verify example structure, dependencies, imports
- **Runtime**: < 5 minutes
- **Resources**: None (GitHub Actions runner)
- **When**: Every PR, every push

#### Integration Tests (Nightly)

- **Purpose**: Execute individual notebooks on RHOAI cluster
- **Runtime**: 15-60 minutes per notebook
- **Resources**: RHOAI cluster with GPU
- **When**: Nightly, Release, Manual

#### E2E Pipeline Tests (Nightly/Release)

- **Purpose**: Execute full multi-step workflows in sequence
- **Runtime**: 2-4 hours per example
- **Resources**: RHOAI cluster with GPU, persistent storage
- **When**: Nightly, Release

---

## 2. Environment Considerations

### 2.1 Disconnected Environments

**Recommendation: YES - Test disconnected environments**

**Reasoning:**

- Many enterprise RHOAI deployments are air-gapped for security
- Notebook examples often download models/datasets at runtime
- Must verify examples work with pre-cached assets

**Implementation Strategy:**

```text
┌─────────────────────────────────────────────────────────────┐
│                    Disconnected Test Flow                    │
├─────────────────────────────────────────────────────────────┤
│  1. Pre-test Setup (connected phase)                        │
│     ├── Download models to PVC                              │
│     ├── Cache datasets to local storage                     │
│     └── Mirror container images                             │
│                                                             │
│  2. Test Execution (disconnected phase)                     │
│     ├── Network policy blocks external access               │
│     ├── Notebooks use local paths for models/data           │
│     └── Verify no external calls fail                       │
│                                                             │
│  3. Validation                                              │
│     └── Assert all operations completed successfully        │
└─────────────────────────────────────────────────────────────┘
```

**Coverage:**

- **Nightly**: Optional (configurable flag)
- **Release**: Required for 1+ example per category

### 2.2 FIPS Environments

**Recommendation: YES - Test FIPS environments for releases**

**Reasoning:**

- Government and regulated industry customers require FIPS 140-2/140-3 compliance
- Cryptographic libraries behave differently in FIPS mode
- Some Python packages may fail in FIPS-enabled environments

**Implementation Strategy:**

- Maintain a separate FIPS-enabled RHOAI cluster for testing
- Run release validation tests on FIPS cluster
- Test critical cryptographic operations (SSL connections, tokenizers)

**Coverage:**

- **Nightly**: ❌ Skip (cost/resource constraints)
- **Release**: ✅ Run on FIPS cluster (at minimum smoke + 1 full E2E per example category)

### 2.3 Environment Matrix

| Environment | PR | Nightly | Release |
|-------------|-----|---------|---------|
| Standard RHOAI | ⚡ Selective | ✅ Full | ✅ Full |
| Disconnected | ❌ | ⚡ Optional | ✅ Required |
| FIPS | ❌ | ❌ | ✅ Required |

---

## 3. Hardware Requirements

### 3.1 Per-Example Requirements

Based on analysis of existing examples:

| Example | Min GPU | Recommended GPU | Memory | Storage | Est. Runtime |
|---------|---------|-----------------|--------|---------|--------------|
| **knowledge-tuning** | 1x A100-40GB | 1x A100-80GB | 100GB | 200GB PVC | 3-4 hours |
| **fine-tuning/osft** | 2x L40S-48GB | 2x A100-40GB | 96GB | 100GB PVC | 20-30 min |
| **fine-tuning/sft** | 1x L40-48GB | 1x A100-40GB | 64GB | 100GB PVC | 15-20 min |
| **llmcompressor** | 1x A100-40GB | 1x A100-80GB | 64GB | 100GB PVC | 30-60 min |
| **domain_customization_kfp** | 1x A100-40GB | 2x A100-40GB | 128GB | 200GB PVC | 2-3 hours |

### 3.2 Cluster Requirements

**Minimum Test Cluster:**

```yaml
nodes:
  - type: GPU Worker
    count: 2
    gpu: NVIDIA A100-40GB (or L40S-48GB)
    cpu: 64 cores
    memory: 256GB

storage:
  - type: PVC
    size: 500GB
    storageClass: ocs-storagecluster-cephfs

networking:
  - LoadBalancer for RHOAI routes
  - Optional: Network policies for disconnected testing
```

**Recommended Test Cluster (for parallel testing):**

```yaml
nodes:
  - type: GPU Worker
    count: 4
    gpu: NVIDIA A100-80GB
    cpu: 96 cores
    memory: 512GB

storage:
  - type: PVC
    size: 1TB
    storageClass: ocs-storagecluster-cephfs
```

### 3.3 Resource Optimization Strategies

1. **Sequential execution** for memory-intensive notebooks
2. **Namespace isolation** per test run to prevent conflicts
3. **PVC cleanup** after test completion
4. **GPU time-slicing** for lighter workloads (smoke tests)

---

## 4. Test Result Storage

### 4.1 Retention Policy

| Artifact Type | PR | Nightly | Release | Reasoning |
|---------------|-----|---------|---------|-----------|
| Test logs | 7 days | 30 days | 1 year | Debug recent failures |
| JUnit XML | 7 days | 30 days | 1 year | CI/CD integration |
| Notebook outputs | 3 days | 14 days | 90 days | Large files, review executed cells |
| Model checkpoints | ❌ Delete | 7 days | 30 days | Very large, only needed for debugging |
| Metrics/Telemetry | 30 days | 90 days | 2 years | Trend analysis |
| Screenshots/HTML | 7 days | 30 days | 90 days | Visual verification |

### 4.2 Storage Implementation

```yaml
# Artifact storage tiers
storage:
  hot:  # S3-compatible, fast access
    bucket: rhoai-test-results-hot
    retention: 30 days
    contents:
      - test-logs/
      - junit-reports/
      - notebook-outputs/

  cold:  # S3 Glacier or equivalent
    bucket: rhoai-test-results-archive
    retention: 2 years
    contents:
      - release-artifacts/
      - metrics-historical/
```

### 4.3 Results Dashboard

- **Primary**: GitHub Actions workflow summaries
- **Secondary**: Grafana dashboard for long-term metrics
- **Notifications**: Slack/Email for nightly/release failures

---

## 5. Architecture Overview

### 5.1 High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GitHub Repository                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ examples/       │  │ tests/          │  │ .github/        │                  │
│  │ ├─knowledge-    │  │ ├─e2e/          │  │ workflows/      │                  │
│  │ │  tuning/      │  │ ├─integration/  │  │ ├─pr-tests.yml  │                  │
│  │ ├─fine-tuning/  │  │ ├─validation/   │  │ ├─nightly.yml   │                  │
│  │ └─llmcompressor │  │ └─fixtures/     │  │ └─release.yml   │                  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │  PR Workflow    │ │ Nightly Workflow│ │ Release Workflow│
          │  (Validation +  │ │ (Full E2E on    │ │ (Multi-env +    │
          │   Smoke Only)   │ │  RHOAI Cluster) │ │  FIPS + Discon) │
          └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
                   │                   │                   │
                   ▼                   ▼                   ▼
          ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
          │ GitHub-hosted   │ │ Self-hosted     │ │ Self-hosted     │
          │ Runner          │ │ Runner + RHOAI  │ │ Runner + Multi  │
          │ (No GPU)        │ │ Cluster Access  │ │ Cluster Access  │
          └─────────────────┘ └────────┬────────┘ └────────┬────────┘
                                       │                   │
                              ┌────────▼───────────────────▼────────┐
                              │           RHOAI Cluster(s)          │
                              │  ┌─────────────────────────────────┐│
                              │  │      Test Namespace             ││
                              │  │  ┌───────────┐ ┌───────────┐   ││
                              │  │  │ Workbench │ │ Workbench │   ││
                              │  │  │ (Test 1)  │ │ (Test 2)  │   ││
                              │  │  └───────────┘ └───────────┘   ││
                              │  │  ┌─────────────────────────┐   ││
                              │  │  │   Shared PVC (Models)   │   ││
                              │  │  └─────────────────────────┘   ││
                              │  └─────────────────────────────────┘│
                              └─────────────────────────────────────┘
```

### 5.2 Notebook Execution Architecture on RHOAI

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        RHOAI Notebook Execution Flow                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────┐     ┌──────────────────────────────────────────────────┐     │
│  │  Test Runner │     │              RHOAI Cluster                        │     │
│  │  (Python)    │     │                                                   │     │
│  │              │     │  ┌────────────────────────────────────────────┐  │     │
│  │  1. Auth     │────▶│  │           Data Science Project             │  │     │
│  │  2. Setup    │     │  │                                            │  │     │
│  │  3. Execute  │     │  │   ┌──────────────────────────────────────┐ │  │     │
│  │  4. Monitor  │     │  │   │         Workbench Pod                 │ │  │     │
│  │  5. Collect  │◀────│  │   │  ┌─────────────────────────────────┐ │ │  │     │
│  │     Results  │     │  │   │  │ JupyterLab + Kernel             │ │ │  │     │
│  └──────────────┘     │  │   │  │                                 │ │ │  │     │
│                       │  │   │  │  ┌─────────────────────────┐   │ │ │  │     │
│                       │  │   │  │  │  Notebook Execution     │   │ │ │  │     │
│                       │  │   │  │  │  (papermill/nbclient)   │   │ │ │  │     │
│                       │  │   │  │  └─────────────────────────┘   │ │ │  │     │
│                       │  │   │  │                                 │ │ │  │     │
│                       │  │   │  │  GPU: nvidia.com/gpu: 1        │ │ │  │     │
│                       │  │   │  └─────────────────────────────────┘ │ │  │     │
│                       │  │   │                                      │ │  │     │
│                       │  │   │  ┌────────────────┐ ┌─────────────┐ │ │  │     │
│                       │  │   │  │   Model PVC    │ │ Output PVC  │ │ │  │     │
│                       │  │   │  │   (ReadOnly)   │ │ (ReadWrite) │ │ │  │     │
│                       │  │   │  └────────────────┘ └─────────────┘ │ │  │     │
│                       │  │   └──────────────────────────────────────┘ │  │     │
│                       │  └────────────────────────────────────────────┘  │     │
│                       └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Execution Methods

**Option A: Remote Notebook Execution via Kubernetes API**

```python
# Execute notebook inside RHOAI workbench pod
from rhoai_test_framework import RHOAIClient

client = RHOAIClient(cluster_url, token)
workbench = client.create_workbench(
    name="test-knowledge-tuning",
    image="jupyter-minimal-cuda:2025.2",
    gpu=1,
    memory="100Gi"
)
result = workbench.execute_notebook(
    notebook_path="examples/knowledge-tuning/01_Base_Model_Evaluation/Base_Model_Evaluation.ipynb",
    timeout=3600
)
```

**Option B: Papermill-based Execution (Recommended)**

```python
# Use papermill to execute notebooks with parameters
import papermill as pm

pm.execute_notebook(
    input_path='Base_Model_Evaluation.ipynb',
    output_path='output/Base_Model_Evaluation_executed.ipynb',
    parameters={'MODEL_NAME': 'test-model'},
    kernel_name='python3',
    cwd='/path/to/notebook/dir'
)
```

---

## 6. Folder Structure

### 6.1 Proposed Directory Layout

```text
red-hat-ai-examples/
├── .github/
│   ├── workflows/
│   │   ├── pr-validation.yml          # Fast checks for all PRs
│   │   ├── pr-smoke.yml               # Smoke tests for all PRs
│   │   ├── nightly-integration.yml    # Nightly RHOAI integration tests
│   │   ├── nightly-e2e.yml            # Nightly full E2E pipeline tests
│   │   ├── release-validation.yml     # Release validation suite
│   │   └── manual-test.yml            # Manual trigger with options
│   └── actions/
│       ├── setup-rhoai/               # Reusable action for RHOAI setup
│       │   └── action.yml
│       ├── execute-notebook/          # Reusable notebook execution action
│       │   └── action.yml
│       └── collect-results/           # Results collection action
│           └── action.yml
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures
│   ├── pytest.ini                     # Pytest configuration
│   │
│   ├── validation/                    # Static validation (existing)
│   │   ├── test_notebook_structure.py
│   │   ├── test_notebook_content.py
│   │   ├── test_notebook_syntax.py
│   │   └── test_pyproject_toml.py
│   │
│   ├── examples/                      # Example-specific smoke tests (existing)
│   │   ├── knowledge_tuning/
│   │   ├── fine_tuning/
│   │   └── llmcompressor/
│   │
│   ├── integration/                   # NEW: Individual notebook execution tests
│   │   ├── __init__.py
│   │   ├── conftest.py               # RHOAI cluster fixtures
│   │   ├── base.py                   # Base test class for notebook tests
│   │   │
│   │   ├── knowledge_tuning/
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py           # Example-specific fixtures
│   │   │   ├── test_01_base_model_evaluation.py
│   │   │   ├── test_02_data_processing.py
│   │   │   ├── test_03_knowledge_generation.py
│   │   │   ├── test_04_knowledge_mixing.py
│   │   │   ├── test_05_model_training.py
│   │   │   └── test_06_evaluation.py
│   │   │
│   │   ├── fine_tuning/
│   │   │   ├── osft/
│   │   │   │   └── test_osft_notebook.py
│   │   │   └── sft/
│   │   │       └── test_sft_notebook.py
│   │   │
│   │   └── llmcompressor/
│   │       └── test_workbench_example.py
│   │
│   ├── e2e/                          # NEW: Full pipeline E2E tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── base.py                   # Base E2E test class
│   │   │
│   │   ├── test_knowledge_tuning_pipeline.py
│   │   ├── test_fine_tuning_osft_pipeline.py
│   │   ├── test_fine_tuning_sft_pipeline.py
│   │   └── test_llmcompressor_pipeline.py
│   │
│   └── fixtures/                     # Shared test fixtures and data
│       ├── __init__.py
│       ├── sample_data/
│       │   ├── sample_dataset.jsonl
│       │   └── sample_config.yaml
│       └── mock_responses/
│           └── model_outputs.json
│
├── infrastructure/                    # NEW: Test infrastructure code
│   ├── __init__.py
│   ├── rhoai/
│   │   ├── __init__.py
│   │   ├── client.py                 # RHOAI cluster client
│   │   ├── workbench.py              # Workbench management
│   │   ├── project.py                # Project/namespace management
│   │   └── resources.py              # PVC, secrets, configmaps
│   │
│   ├── notebook/
│   │   ├── __init__.py
│   │   ├── executor.py               # Notebook execution engine
│   │   ├── validator.py              # Output validation
│   │   └── reporter.py               # Results reporting
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── cluster_profiles.yaml     # Cluster configurations
│   │   ├── example_manifests.yaml    # Example test configurations
│   │   └── hardware_profiles.yaml    # Hardware profile definitions
│   │
│   └── utils/
│       ├── __init__.py
│       ├── kubernetes.py             # K8s utilities
│       ├── logging.py                # Logging configuration
│       └── retry.py                  # Retry mechanisms
│
├── scripts/                          # NEW: Helper scripts
│   ├── run_integration_tests.py      # Local integration test runner
│   ├── setup_test_cluster.py         # Cluster setup automation
│   ├── cleanup_test_resources.py     # Resource cleanup
│   └── generate_test_report.py       # Report generation
│
└── docs/
    ├── E2E_TESTING_PLAN.md           # This document
    ├── TESTING.md                    # Existing testing guide (update)
    └── test_infrastructure/
        ├── ARCHITECTURE.md           # Detailed architecture docs
        ├── RUNBOOK.md                # Operational runbook
        └── TROUBLESHOOTING.md        # Common issues and solutions
```

### 6.2 Configuration Files

**`infrastructure/config/example_manifests.yaml`**

```yaml
examples:
  knowledge-tuning:
    display_name: "Knowledge Tuning"
    description: "InstructLab-based knowledge tuning workflow"
    path: "examples/knowledge-tuning"

    steps:
      - name: "01_Base_Model_Evaluation"
        notebook: "Base_Model_Evaluation.ipynb"
        timeout: 1800  # 30 minutes
        gpu_required: true
        dependencies: []

      - name: "02_Data_Processing"
        notebook: "Data_Processing.ipynb"
        timeout: 1800
        gpu_required: false
        dependencies: ["01_Base_Model_Evaluation"]

      - name: "03_Knowledge_Generation"
        notebook: "Knowledge_Generation.ipynb"
        timeout: 3600  # 1 hour
        gpu_required: true
        dependencies: ["02_Data_Processing"]

      - name: "04_Knowledge_Mixing"
        notebook: "Knowledge_Mixing.ipynb"
        timeout: 1800
        gpu_required: false
        dependencies: ["03_Knowledge_Generation"]

      - name: "05_Model_Training"
        notebook: "Model_Training.ipynb"
        timeout: 7200  # 2 hours
        gpu_required: true
        dependencies: ["04_Knowledge_Mixing"]

      - name: "06_Evaluation"
        notebook: "Evaluation.ipynb"
        timeout: 3600
        gpu_required: true
        dependencies: ["05_Model_Training"]

    hardware_profile:
      cpu: "100"
      memory: "100Gi"
      gpu: 1
      gpu_type: "nvidia.com/gpu"
      storage: "200Gi"

    environment:
      STUDENT_MODEL: "RedHatAI/Llama-3.1-8B-Instruct"
      TEACHER_MODEL: "openai/gpt-oss-120b"

    tags:
      - "llm"
      - "knowledge-tuning"
      - "instructlab"
```

---

## 7. Implementation Details

### 7.1 Core Test Framework Classes

**`infrastructure/rhoai/client.py`**

```python
"""RHOAI Cluster Client for test automation."""

from dataclasses import dataclass
from typing import Optional
import logging

from kubernetes import client, config
from openshift.dynamic import DynamicClient

logger = logging.getLogger(__name__)


@dataclass
class ClusterConfig:
    """RHOAI cluster configuration."""
    api_url: str
    token: str
    namespace: str
    verify_ssl: bool = True


class RHOAIClient:
    """Client for interacting with RHOAI cluster."""

    def __init__(self, cluster_config: ClusterConfig):
        self.config = cluster_config
        self._k8s_client: Optional[client.ApiClient] = None
        self._dyn_client: Optional[DynamicClient] = None

    def connect(self) -> None:
        """Establish connection to RHOAI cluster."""
        configuration = client.Configuration()
        configuration.host = self.config.api_url
        configuration.api_key = {"authorization": f"Bearer {self.config.token}"}
        configuration.verify_ssl = self.config.verify_ssl

        self._k8s_client = client.ApiClient(configuration)
        self._dyn_client = DynamicClient(self._k8s_client)

        logger.info(f"Connected to RHOAI cluster: {self.config.api_url}")

    def create_data_science_project(self, name: str) -> "DataScienceProject":
        """Create a new Data Science Project for testing."""
        # Implementation
        pass

    def create_workbench(
        self,
        project: "DataScienceProject",
        name: str,
        image: str,
        hardware_profile: dict,
    ) -> "Workbench":
        """Create a workbench in the project."""
        # Implementation
        pass

    def cleanup(self, project_name: str) -> None:
        """Clean up test resources."""
        # Implementation
        pass
```

**`infrastructure/notebook/executor.py`**

```python
"""Notebook execution engine for RHOAI testing."""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List
import logging

import papermill as pm
from nbformat import NotebookNode

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Notebook execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ExecutionResult:
    """Result of notebook execution."""
    status: ExecutionStatus
    notebook_path: str
    output_path: str
    duration_seconds: float
    error_message: Optional[str] = None
    cell_outputs: Optional[List[dict]] = None


class NotebookExecutor:
    """Execute Jupyter notebooks with monitoring and validation."""

    def __init__(
        self,
        workbench_connection: "WorkbenchConnection",
        output_dir: Path,
    ):
        self.workbench = workbench_connection
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def execute(
        self,
        notebook_path: Path,
        parameters: Optional[dict] = None,
        timeout: int = 3600,
        kernel_name: str = "python3",
    ) -> ExecutionResult:
        """
        Execute a notebook and return results.

        Args:
            notebook_path: Path to the input notebook
            parameters: Parameters to inject into the notebook
            timeout: Maximum execution time in seconds
            kernel_name: Jupyter kernel to use

        Returns:
            ExecutionResult with status and outputs
        """
        output_path = self.output_dir / f"{notebook_path.stem}_executed.ipynb"
        start_time = time.time()

        try:
            logger.info(f"Executing notebook: {notebook_path}")

            pm.execute_notebook(
                input_path=str(notebook_path),
                output_path=str(output_path),
                parameters=parameters or {},
                kernel_name=kernel_name,
                cwd=str(notebook_path.parent),
                progress_bar=False,
                request_save_on_cell_execute=True,
            )

            duration = time.time() - start_time
            logger.info(f"Notebook executed successfully in {duration:.2f}s")

            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                notebook_path=str(notebook_path),
                output_path=str(output_path),
                duration_seconds=duration,
            )

        except pm.PapermillExecutionError as e:
            duration = time.time() - start_time
            logger.error(f"Notebook execution failed: {e}")

            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                notebook_path=str(notebook_path),
                output_path=str(output_path),
                duration_seconds=duration,
                error_message=str(e),
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.exception(f"Unexpected error during execution: {e}")

            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                notebook_path=str(notebook_path),
                output_path=str(output_path),
                duration_seconds=duration,
                error_message=str(e),
            )

    def execute_pipeline(
        self,
        notebooks: List[Path],
        shared_parameters: Optional[dict] = None,
    ) -> List[ExecutionResult]:
        """Execute multiple notebooks in sequence (for E2E tests)."""
        results = []

        for notebook in notebooks:
            result = self.execute(notebook, parameters=shared_parameters)
            results.append(result)

            if result.status != ExecutionStatus.SUCCESS:
                logger.error(f"Pipeline stopped due to failure in {notebook}")
                break

        return results
```

### 7.2 Integration Test Base Class

**`tests/integration/base.py`**

```python
"""Base class for RHOAI integration tests."""

import pytest
from pathlib import Path
from typing import Generator, Optional
import logging

from infrastructure.rhoai.client import RHOAIClient, ClusterConfig
from infrastructure.notebook.executor import NotebookExecutor, ExecutionStatus

logger = logging.getLogger(__name__)


class RHOAIIntegrationTest:
    """Base class for RHOAI notebook integration tests."""

    # Override in subclasses
    EXAMPLE_PATH: str = ""
    HARDWARE_PROFILE: dict = {
        "cpu": "8",
        "memory": "32Gi",
        "gpu": 0,
    }

    @pytest.fixture(scope="class")
    def rhoai_client(self, cluster_config) -> Generator[RHOAIClient, None, None]:
        """Create RHOAI client for the test class."""
        client = RHOAIClient(cluster_config)
        client.connect()
        yield client

    @pytest.fixture(scope="class")
    def test_project(self, rhoai_client, request) -> Generator:
        """Create isolated project for test class."""
        project_name = f"test-{request.node.name[:20]}-{int(time.time())}"
        project = rhoai_client.create_data_science_project(project_name)

        yield project

        # Cleanup after all tests in class complete
        rhoai_client.cleanup(project_name)

    @pytest.fixture(scope="class")
    def workbench(self, rhoai_client, test_project) -> Generator:
        """Create workbench for notebook execution."""
        wb = rhoai_client.create_workbench(
            project=test_project,
            name="test-workbench",
            image="jupyter-minimal-cuda:2025.2",
            hardware_profile=self.HARDWARE_PROFILE,
        )
        wb.wait_until_ready(timeout=600)

        yield wb

        wb.stop()

    @pytest.fixture
    def notebook_executor(self, workbench, tmp_path) -> NotebookExecutor:
        """Create notebook executor."""
        return NotebookExecutor(
            workbench_connection=workbench.connection,
            output_dir=tmp_path / "outputs",
        )

    def execute_and_validate(
        self,
        executor: NotebookExecutor,
        notebook_path: Path,
        timeout: int = 3600,
        expected_outputs: Optional[list] = None,
    ) -> None:
        """Execute notebook and validate results."""
        result = executor.execute(notebook_path, timeout=timeout)

        assert result.status == ExecutionStatus.SUCCESS, (
            f"Notebook {notebook_path.name} failed: {result.error_message}"
        )

        if expected_outputs:
            # Validate expected outputs exist
            self._validate_outputs(result, expected_outputs)

    def _validate_outputs(self, result, expected_outputs: list) -> None:
        """Validate that expected outputs were generated."""
        # Implementation for output validation
        pass
```

### 7.3 Example Integration Test

**`tests/integration/knowledge_tuning/test_01_base_model_evaluation.py`**

```python
"""Integration tests for Knowledge Tuning - Base Model Evaluation notebook."""

import pytest
from pathlib import Path

from tests.integration.base import RHOAIIntegrationTest
from infrastructure.notebook.executor import ExecutionStatus


@pytest.mark.integration
@pytest.mark.knowledge_tuning
class TestBaseModelEvaluation(RHOAIIntegrationTest):
    """Integration tests for Base Model Evaluation notebook."""

    EXAMPLE_PATH = "examples/knowledge-tuning"
    HARDWARE_PROFILE = {
        "cpu": "100",
        "memory": "100Gi",
        "gpu": 1,
    }

    @pytest.fixture
    def notebook_path(self, repo_root) -> Path:
        """Get path to the notebook."""
        return (
            repo_root
            / self.EXAMPLE_PATH
            / "01_Base_Model_Evaluation"
            / "Base_Model_Evaluation.ipynb"
        )

    def test_notebook_executes_successfully(
        self,
        notebook_executor,
        notebook_path,
    ):
        """Test that Base Model Evaluation notebook executes without errors."""
        result = notebook_executor.execute(
            notebook_path=notebook_path,
            timeout=1800,  # 30 minutes
            parameters={
                "MODEL_NAME": "RedHatAI/Llama-3.1-8B-Instruct",
            },
        )

        assert result.status == ExecutionStatus.SUCCESS, (
            f"Notebook execution failed: {result.error_message}"
        )

    def test_model_loads_correctly(
        self,
        notebook_executor,
        notebook_path,
    ):
        """Test that the model loads and generates output."""
        result = notebook_executor.execute(notebook_path, timeout=1800)

        assert result.status == ExecutionStatus.SUCCESS
        # Additional validation of model output

    def test_gpu_utilization(
        self,
        notebook_executor,
        notebook_path,
        workbench,
    ):
        """Test that GPU is properly utilized during execution."""
        # Monitor GPU during execution
        result = notebook_executor.execute(notebook_path, timeout=1800)

        assert result.status == ExecutionStatus.SUCCESS
        # Verify GPU was used (check nvidia-smi logs)
```

### 7.4 E2E Pipeline Test

**`tests/e2e/test_knowledge_tuning_pipeline.py`**

```python
"""E2E pipeline test for Knowledge Tuning example."""

import pytest
from pathlib import Path
from typing import List

from tests.integration.base import RHOAIIntegrationTest
from infrastructure.notebook.executor import ExecutionStatus, ExecutionResult


@pytest.mark.e2e
@pytest.mark.knowledge_tuning
@pytest.mark.slow
class TestKnowledgeTuningPipeline(RHOAIIntegrationTest):
    """E2E test for complete Knowledge Tuning workflow."""

    EXAMPLE_PATH = "examples/knowledge-tuning"
    HARDWARE_PROFILE = {
        "cpu": "100",
        "memory": "100Gi",
        "gpu": 1,
    }

    @pytest.fixture
    def pipeline_notebooks(self, repo_root) -> List[Path]:
        """Get ordered list of notebooks in pipeline."""
        base_path = repo_root / self.EXAMPLE_PATH
        return [
            base_path / "01_Base_Model_Evaluation" / "Base_Model_Evaluation.ipynb",
            base_path / "02_Data_Processing" / "Data_Processing.ipynb",
            base_path / "03_Knowledge_Generation" / "Knowledge_Generation.ipynb",
            base_path / "04_Knowledge_Mixing" / "Knowledge_Mixing.ipynb",
            base_path / "05_Model_Training" / "Model_Training.ipynb",
            base_path / "06_Evaluation" / "Evaluation.ipynb",
        ]

    def test_full_pipeline_execution(
        self,
        notebook_executor,
        pipeline_notebooks,
    ):
        """Test complete knowledge tuning pipeline execution."""
        results: List[ExecutionResult] = []

        for notebook in pipeline_notebooks:
            result = notebook_executor.execute(
                notebook_path=notebook,
                timeout=7200,  # 2 hours max per notebook
            )
            results.append(result)

            # Fail fast if any notebook fails
            assert result.status == ExecutionStatus.SUCCESS, (
                f"Pipeline failed at {notebook.name}: {result.error_message}"
            )

        # Validate all notebooks completed
        assert len(results) == len(pipeline_notebooks)
        assert all(r.status == ExecutionStatus.SUCCESS for r in results)

        # Calculate total pipeline duration
        total_duration = sum(r.duration_seconds for r in results)
        print(f"Total pipeline duration: {total_duration/3600:.2f} hours")

    def test_pipeline_outputs_exist(
        self,
        notebook_executor,
        pipeline_notebooks,
        test_project,
    ):
        """Test that pipeline generates expected output artifacts."""
        # Execute pipeline
        results = notebook_executor.execute_pipeline(pipeline_notebooks)

        # Verify outputs
        expected_outputs = [
            "output/step_02/processed_data/",
            "output/step_03/generated_qa/",
            "output/step_04/training_mix/",
            "output/step_05/checkpoints/",
            "output/step_06/evaluation_results/",
        ]

        for output_path in expected_outputs:
            # Verify output exists in PVC
            assert test_project.pvc_path_exists(output_path), (
                f"Expected output not found: {output_path}"
            )
```

### 7.5 GitHub Actions Workflow

**`.github/workflows/nightly-integration.yml`**

```yaml
name: Nightly Integration Tests

on:
  schedule:
    # Run at 2 AM UTC every day
    - cron: '0 2 * * *'
  workflow_dispatch:
    inputs:
      example:
        description: 'Example to test (all, knowledge-tuning, fine-tuning, llmcompressor)'
        required: false
        default: 'all'
      environment:
        description: 'Test environment (standard, disconnected, fips)'
        required: false
        default: 'standard'

env:
  PYTHON_VERSION: '3.12'

jobs:
  setup:
    name: Setup Test Matrix
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.set-matrix.outputs.matrix }}
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set test matrix
        id: set-matrix
        run: |
          if [[ "${{ github.event.inputs.example }}" == "all" || -z "${{ github.event.inputs.example }}" ]]; then
            echo 'matrix={"example":["knowledge-tuning","fine-tuning/osft","fine-tuning/sft","llmcompressor"]}' >> $GITHUB_OUTPUT
          else
            echo 'matrix={"example":["${{ github.event.inputs.example }}"]}' >> $GITHUB_OUTPUT
          fi

  integration-tests:
    name: Integration - ${{ matrix.example }}
    needs: setup
    runs-on: [self-hosted, rhoai-gpu]
    timeout-minutes: 240
    strategy:
      fail-fast: false
      matrix: ${{ fromJson(needs.setup.outputs.matrix) }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[test]"
          pip install papermill kubernetes openshift-client

      - name: Configure RHOAI access
        env:
          RHOAI_API_URL: ${{ secrets.RHOAI_API_URL }}
          RHOAI_TOKEN: ${{ secrets.RHOAI_TOKEN }}
        run: |
          echo "RHOAI_API_URL=${RHOAI_API_URL}" >> $GITHUB_ENV
          echo "RHOAI_TOKEN=${RHOAI_TOKEN}" >> $GITHUB_ENV

      - name: Run integration tests
        run: |
          pytest tests/integration/${{ matrix.example }}/ \
            -v \
            --tb=long \
            --junit-xml=integration-results-${{ matrix.example }}.xml \
            --timeout=7200 \
            -m "integration"

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: integration-results-${{ matrix.example }}
          path: |
            integration-results-*.xml
            outputs/
          retention-days: 30

      - name: Upload executed notebooks
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: executed-notebooks-${{ matrix.example }}
          path: outputs/*_executed.ipynb
          retention-days: 14

  e2e-tests:
    name: E2E Pipeline Tests
    needs: integration-tests
    runs-on: [self-hosted, rhoai-gpu]
    timeout-minutes: 480

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -e ".[test]"
          pip install papermill kubernetes openshift-client

      - name: Run E2E tests
        env:
          RHOAI_API_URL: ${{ secrets.RHOAI_API_URL }}
          RHOAI_TOKEN: ${{ secrets.RHOAI_TOKEN }}
        run: |
          pytest tests/e2e/ \
            -v \
            --tb=long \
            --junit-xml=e2e-results.xml \
            --timeout=14400 \
            -m "e2e"

      - name: Upload E2E results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-results
          path: e2e-results.xml
          retention-days: 30

  report:
    name: Generate Report
    needs: [integration-tests, e2e-tests]
    if: always()
    runs-on: ubuntu-latest

    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4

      - name: Generate summary report
        run: |
          echo "## Nightly Test Results" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Example | Status | Duration |" >> $GITHUB_STEP_SUMMARY
          echo "|---------|--------|----------|" >> $GITHUB_STEP_SUMMARY
          # Parse JUnit XML and generate summary

      - name: Notify on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Nightly RHOAI tests failed! Check: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 8. Forked PR Workflow

### 8.1 Security Considerations

Forked PRs cannot access repository secrets for security reasons. This means:

1. **No cluster access** in forked PR workflows
2. **Only local tests** (validation + smoke) can run
3. **Maintainer approval required** before integration tests run

### 8.2 Forked PR Workflow

**`.github/workflows/pr-validation.yml`**

```yaml
name: PR Validation

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

jobs:
  validation:
    name: Validation Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -e ".[test]"

      - name: Run validation tests
        run: pytest tests/validation/ -v

      - name: Run smoke tests
        run: pytest tests/examples/ -v

  # This job only runs for trusted PRs (from repo members)
  integration-check:
    name: Integration Test Check
    if: github.event.pull_request.head.repo.full_name == github.repository
    needs: validation
    runs-on: ubuntu-latest
    steps:
      - name: Check for example changes
        id: changes
        uses: dorny/paths-filter@v2
        with:
          filters: |
            knowledge-tuning:
              - 'examples/knowledge-tuning/**'
            fine-tuning:
              - 'examples/fine-tuning/**'
            llmcompressor:
              - 'examples/llmcompressor/**'

      - name: Trigger selective integration tests
        if: steps.changes.outputs.knowledge-tuning == 'true'
        run: |
          echo "Would trigger knowledge-tuning integration tests"
          # In reality, dispatch to integration workflow
```

### 8.3 Manual Integration Test Trigger for Forked PRs

Maintainers can manually trigger integration tests for forked PRs after review:

```yaml
# .github/workflows/manual-integration.yml
name: Manual Integration Test

on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: 'PR number to test'
        required: true
      example:
        description: 'Example to test'
        required: true
        type: choice
        options:
          - knowledge-tuning
          - fine-tuning/osft
          - fine-tuning/sft
          - llmcompressor

jobs:
  test:
    name: Integration Test for PR #${{ inputs.pr_number }}
    runs-on: [self-hosted, rhoai-gpu]
    steps:
      - name: Checkout PR
        uses: actions/checkout@v4
        with:
          ref: refs/pull/${{ inputs.pr_number }}/head

      - name: Run integration tests
        env:
          RHOAI_API_URL: ${{ secrets.RHOAI_API_URL }}
          RHOAI_TOKEN: ${{ secrets.RHOAI_TOKEN }}
        run: |
          pytest tests/integration/${{ inputs.example }}/ -v -m integration
```

---

## 9. Implementation Tasks

### Phase 1: Foundation (Week 1-2)

| # | Task | Priority | Effort |
|---|------|----------|--------|
| 1.1 | Create `infrastructure/` directory structure | High | S |
| 1.2 | Implement `RHOAIClient` class for cluster interaction | High | M |
| 1.3 | Implement `NotebookExecutor` with papermill | High | M |
| 1.4 | Create base test class `RHOAIIntegrationTest` | High | M |
| 1.5 | Set up test fixtures in `tests/integration/conftest.py` | High | S |
| 1.6 | Create `example_manifests.yaml` configuration | Medium | S |

### Phase 2: Integration Tests (Week 2-3)

| # | Task | Priority | Effort |
|---|------|----------|--------|
| 2.1 | Implement knowledge-tuning integration tests (all 6 notebooks) | High | L |
| 2.2 | Implement fine-tuning/osft integration test | High | M |
| 2.3 | Implement fine-tuning/sft integration test | High | M |
| 2.4 | Implement llmcompressor integration test | Medium | M |
| 2.5 | Add test markers and pytest configuration | Medium | S |

### Phase 3: E2E Pipeline Tests (Week 3-4)

| # | Task | Priority | Effort |
|---|------|----------|--------|
| 3.1 | Implement E2E pipeline test for knowledge-tuning | High | L |
| 3.2 | Implement E2E pipeline test for fine-tuning examples | Medium | M |
| 3.3 | Add output validation and artifact collection | High | M |
| 3.4 | Implement pipeline dependency management | Medium | M |

### Phase 4: CI/CD Workflows (Week 4-5)

| # | Task | Priority | Effort |
|---|------|----------|--------|
| 4.1 | Create `pr-validation.yml` workflow | High | S |
| 4.2 | Create `nightly-integration.yml` workflow | High | M |
| 4.3 | Create `nightly-e2e.yml` workflow | High | M |
| 4.4 | Create `release-validation.yml` workflow | Medium | M |
| 4.5 | Create `manual-test.yml` workflow for forked PRs | Medium | S |
| 4.6 | Set up self-hosted runner configuration | High | M |
| 4.7 | Configure secrets for RHOAI cluster access | High | S |

### Phase 5: Reporting & Observability (Week 5-6)

| # | Task | Priority | Effort |
|---|------|----------|--------|
| 5.1 | Implement test result reporter | Medium | M |
| 5.2 | Set up artifact storage (S3 buckets) | Medium | S |
| 5.3 | Configure Slack/Email notifications | Low | S |
| 5.4 | Create Grafana dashboard for test metrics | Low | M |
| 5.5 | Write operational runbook | Medium | M |

### Phase 6: Advanced Features (Week 6-8)

| # | Task | Priority | Effort |
|---|------|----------|--------|
| 6.1 | Implement disconnected environment testing | Medium | L |
| 6.2 | Set up FIPS cluster for release testing | Low | L |
| 6.3 | Add GPU monitoring during tests | Low | M |
| 6.4 | Implement test parallelization | Low | M |
| 6.5 | Create troubleshooting documentation | Medium | S |

### Effort Legend

- **S** = Small (< 4 hours)
- **M** = Medium (4-16 hours)
- **L** = Large (> 16 hours)

---

## Appendix A: Architecture Diagram

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    GitHub Repository                                    │
│                                                                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │  PR Event   │    │  Schedule   │    │  Release    │    │   Manual    │             │
│  │  (Forked)   │    │  (Nightly)  │    │   Tag       │    │  Dispatch   │             │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘             │
│         │                  │                  │                  │                    │
│         ▼                  ▼                  ▼                  ▼                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │ Validation  │    │ Integration │    │  Release    │    │  Selective  │             │
│  │ + Smoke     │    │  + E2E      │    │ Validation  │    │   Tests     │             │
│  │ (GH Runner) │    │ (Self-host) │    │ (Multi-env) │    │             │             │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘             │
└─────────┼──────────────────┼──────────────────┼──────────────────┼────────────────────┘
          │                  │                  │                  │
          │                  │                  │                  │
          │            ┌─────▼──────────────────▼──────────────────▼─────┐
          │            │              Self-Hosted Runner                  │
          │            │         (With RHOAI Cluster Access)             │
          │            │                                                  │
          │            │  ┌────────────────────────────────────────────┐ │
          │            │  │            Test Framework                   │ │
          │            │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
          │            │  │  │  RHOAI   │  │ Notebook │  │  Result  │  │ │
          │            │  │  │  Client  │  │ Executor │  │ Reporter │  │ │
          │            │  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  │ │
          │            │  └───────┼─────────────┼─────────────┼────────┘ │
          │            └──────────┼─────────────┼─────────────┼──────────┘
          │                       │             │             │
          │                       ▼             │             │
          │            ┌──────────────────────────────────────┼──────────┐
          │            │           RHOAI Cluster              │          │
          │            │  ┌────────────────────────────────┐  │          │
          │            │  │      Test Namespace            │  │          │
          │            │  │                                │  │          │
          │            │  │  ┌──────────────────────────┐  │  │          │
          │            │  │  │      Workbench Pod       │  │  │          │
          │            │  │  │  ┌────────────────────┐  │  │  │          │
          │            │  │  │  │   JupyterLab +     │◄─┼──┼──┘          │
          │            │  │  │  │   Papermill        │  │  │             │
          │            │  │  │  │                    │  │  │             │
          │            │  │  │  │  📓 Notebook       │  │  │             │
          │            │  │  │  │  Execution         │  │  │             │
          │            │  │  │  └────────────────────┘  │  │             │
          │            │  │  │                          │  │             │
          │            │  │  │  🎮 GPU: A100-40GB      │  │             │
          │            │  │  └──────────────────────────┘  │             │
          │            │  │                                │             │
          │            │  │  ┌──────────┐  ┌──────────┐   │             │
          │            │  │  │Model PVC │  │Output PVC│   │             │
          │            │  │  └──────────┘  └──────────┘   │             │
          │            │  └────────────────────────────────┘             │
          │            └─────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────┐
│   Results &     │
│   Artifacts     │
│  ┌───────────┐  │
│  │ JUnit XML │  │
│  │ Notebooks │  │
│  │  Metrics  │  │
│  └───────────┘  │
└─────────────────┘
```

---

## Appendix B: Quick Reference

### Test Commands

```bash
# Run all local tests
pytest tests/validation/ tests/examples/ -v

# Run integration tests (requires cluster access)
pytest tests/integration/ -v -m integration

# Run E2E tests (requires cluster access)
pytest tests/e2e/ -v -m e2e

# Run specific example
pytest tests/integration/knowledge_tuning/ -v

# Run with specific marker
pytest -m "integration and not slow" -v
```

### Environment Variables

| Variable | Description | Required For |
|----------|-------------|--------------|
| `RHOAI_API_URL` | RHOAI cluster API endpoint | Integration/E2E |
| `RHOAI_TOKEN` | Service account token | Integration/E2E |
| `RHOAI_NAMESPACE` | Test namespace | Integration/E2E |
| `TEST_GPU_TYPE` | GPU type to request | Integration/E2E |
| `TEST_TIMEOUT` | Default test timeout | All |

---

*Document Version: 1.0*
*Last Updated: December 2024*
