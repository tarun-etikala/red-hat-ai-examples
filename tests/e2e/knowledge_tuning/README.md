# E2E Testing for Knowledge-Tuning Workflow on RHOAI

This directory contains end-to-end (E2E) tests for the knowledge-tuning workflow that run on Red Hat OpenShift AI (RHOAI).

## Overview

The E2E tests use [Papermill](https://papermill.readthedocs.io/) to execute Jupyter notebooks programmatically and validate that:

1. **Notebooks execute without errors** - Each notebook in the pipeline runs successfully
2. **Expected outputs are created** - Files and directories are generated as expected
3. **Pipeline runs end-to-end** - All 6 steps complete in sequence

## Test Profiles

Three pre-configured test profiles are available:

| Profile | Model Size | Max Steps | Max Samples | Approx. Time |
|---------|-----------|-----------|-------------|--------------|
| `minimal` | 135M params | 2 | 3 | ~15-30 min |
| `standard` | 360M params | 5 | 5 | ~30-60 min |
| `extended` | 500M params | 10 | 10 | ~1-2 hours |

## Prerequisites

### 1. RHOAI Cluster Setup

Ensure your RHOAI workbench has:

- Python 3.11+ kernel
- GPU access (for model training steps)
- At least 16GB memory
- 50GB+ storage

### 2. Install Dependencies

```bash
# Install E2E test dependencies
pip install -e ".[e2e]"

# Or install individually
pip install papermill nbformat nbclient pytest
```

### 3. Environment Setup

The tests use small models by default. For custom configuration:

```bash
# Optional: Set custom models
export STUDENT_MODEL_NAME="HuggingFaceTB/SmolLM2-135M-Instruct"  # pragma: allowlist secret
export TEACHER_MODEL_NAME="HuggingFaceTB/SmolLM2-360M-Instruct"  # pragma: allowlist secret
```

## Running Tests

### Quick Start - Minimal Profile

```bash
# Run full pipeline with minimal configuration (fastest)
pytest tests/e2e/knowledge_tuning/ -v --e2e-profile=minimal
```

### Run Full Pipeline

```bash
# Standard profile
pytest tests/e2e/knowledge_tuning/test_e2e_pipeline.py::TestKnowledgeTuningE2EPipeline -v --e2e-profile=standard
```

### Run Individual Steps

```bash
# Test specific notebook (e.g., step 2: Data Processing)
pytest tests/e2e/knowledge_tuning/test_e2e_pipeline.py::TestIndividualNotebookExecution::test_notebook_execution[step02_data_processing] -v
```

### Skip Specific Steps

```bash
# Skip model training and evaluation (GPU-intensive steps)
pytest tests/e2e/knowledge_tuning/ -v --skip-steps=5,6
```

### Keep Outputs for Debugging

```bash
# Keep output files after test completion
pytest tests/e2e/knowledge_tuning/ -v --keep-outputs
```

### Use Custom Models

```bash
# Override models via command line
pytest tests/e2e/knowledge_tuning/ -v \
    --student-model="Qwen/Qwen2.5-0.5B-Instruct" \
    --teacher-model="Qwen/Qwen2.5-0.5B-Instruct"
```

## Test Structure

```text
tests/e2e/knowledge_tuning/
├── __init__.py
├── README.md                  # This file
├── config.py                  # Test configuration and profiles
├── conftest.py                # Pytest fixtures
└── test_e2e_pipeline.py       # Main E2E tests
```

### Test Classes

| Class | Description |
|-------|-------------|
| `TestKnowledgeTuningE2EPipeline` | Full pipeline execution tests |
| `TestIndividualNotebookExecution` | Tests for individual notebook steps |
| `TestNotebookOutputValidation` | Output file/directory validation |
| `TestPipelineResilience` | Error handling and edge cases |
| `TestE2EReporting` | Generate execution reports |

## Configuration Options

### Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--e2e-profile` | `minimal` | Test profile: minimal, standard, extended |
| `--keep-outputs` | `false` | Keep output files for debugging |
| `--skip-steps` | `""` | Comma-separated steps to skip (e.g., "1,5,6") |
| `--student-model` | (from profile) | Override student model |
| `--teacher-model` | (from profile) | Override teacher model |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `STUDENT_MODEL_NAME` | Student/base model to fine-tune |
| `TEACHER_MODEL_NAME` | Teacher model for knowledge generation |
| `TEACHER_MODEL_BASE_URL` | API endpoint for teacher model |
| `TEACHER_MODEL_API_KEY` | API key for teacher model |
| `E2E_TEST_MODE` | Set to "true" during E2E tests |

## Small Models for Testing

The following small models are recommended for E2E testing:

| Model | Size | Notes |
|-------|------|-------|
| `HuggingFaceTB/SmolLM2-135M-Instruct` | 135M | Fastest, minimal quality |
| `HuggingFaceTB/SmolLM2-360M-Instruct` | 360M | Good balance |
| `Qwen/Qwen2.5-0.5B-Instruct` | 500M | Higher quality |
| `microsoft/phi-1_5` | 1.3B | Highest quality, slower |

## Expected Outputs

After a successful E2E run, the following outputs should exist:

```text
examples/knowledge-tuning/output/
├── base_model/                    # Step 1: Downloaded base model
│   └── <model_name>/
├── step_02/                       # Step 2: Data processing
│   ├── docling_output/
│   └── seed_data.jsonl
├── step_03/                       # Step 3: Knowledge generation
│   ├── extractive_summary/
│   ├── detailed_summary/
│   ├── key_facts_to_qa/
│   └── document_based_qa/
├── step_04/                       # Step 4: Knowledge mixing
│   └── *.jsonl                    # Training data files
└── fine_tuned_model/              # Step 5: Trained model
    └── <model_name>/
```

## Troubleshooting

### Common Issues

**Kernel not found:**

```bash
# Install the kernel
python -m ipykernel install --user --name python3
```

**GPU not available:**

```bash
# Skip GPU-intensive steps
pytest tests/e2e/knowledge_tuning/ -v --skip-steps=1,5,6
```

**Memory errors:**

- Use `--e2e-profile=minimal` for smaller models
- Reduce `max_samples` in config

**Timeout errors:**

- Increase timeout in config.py
- Use smaller models

### Debugging Failed Tests

1. Use `--keep-outputs` to preserve output files
2. Check the executed notebooks in the workspace
3. Review the execution report in `e2e_execution_report.json`

```bash
# Run with debugging options
pytest tests/e2e/knowledge_tuning/ -v --keep-outputs -s
```

## CI/CD Integration

### GitHub Actions Workflows

Two workflows are provided for E2E testing:

#### 1. E2E Quick Validation (`.github/workflows/e2e-quick.yml`)

Runs automatically on PRs that modify knowledge-tuning examples:

- Validates E2E test infrastructure
- Runs dry-run to verify configuration
- Tests notebook readability
- **No GPU required**

#### 2. E2E Pipeline Tests (`.github/workflows/e2e-tests.yml`)

Manual or scheduled workflow with full E2E capabilities:

```bash
# Trigger via GitHub CLI
gh workflow run e2e-tests.yml \
  -f profile=minimal \
  -f skip_steps="" \
  -f runner=self-hosted-gpu \
  -f run_full_pipeline=true
```

**Workflow Inputs:**

| Input | Options | Description |
|-------|---------|-------------|
| `profile` | minimal/standard/extended | Test profile |
| `skip_steps` | e.g., "1,5,6" | Steps to skip |
| `runner` | ubuntu-latest/self-hosted-gpu/self-hosted-rhoai | Runner type |
| `run_full_pipeline` | true/false | Run full GPU pipeline |

### Setting Up Self-Hosted Runners

For GPU/RHOAI tests, configure self-hosted runners:

1. **GPU Runner** (`self-hosted-gpu`):
   - Machine with NVIDIA GPU
   - CUDA toolkit installed
   - Python 3.12+ with PyTorch

2. **RHOAI Runner** (`self-hosted-rhoai`):
   - Runner inside RHOAI workbench
   - Access to GPU resources
   - Pre-installed ML libraries

See [GitHub self-hosted runners documentation](https://docs.github.com/en/actions/hosting-your-own-runners)

## Contributing

When adding new notebooks to the knowledge-tuning workflow:

1. Add the step to `KNOWLEDGE_TUNING_STEPS` in `config.py`
2. Define expected outputs for validation
3. Update the README with new step information
