# Running E2E Tests on RHOAI - Step-by-Step Guide

This guide walks you through running the knowledge-tuning E2E tests on a Red Hat OpenShift AI (RHOAI) cluster.

## Prerequisites

Before starting, ensure you have:

- ✅ Access to a RHOAI cluster
- ✅ A workbench with GPU access (for full pipeline)
- ✅ At least 16GB memory allocated
- ✅ 50GB+ persistent storage

## Step 1: Create a Workbench

1. Log in to your RHOAI Dashboard
2. Navigate to **Projects** → Select or create your project
3. Click **Workbenches** → **Create workbench**
4. Configure:
   - **Name**: `knowledge-tuning-e2e-test`
   - **Image**: `Jupyter | Minimal | CUDA | Python 3.12`
   - **Version**: `2025.2` (or latest)
   - **Hardware Profile**: Select one with GPU access
   - **Storage**: 50GB+ PVC

5. Click **Create workbench** and wait for it to start

## Step 2: Clone the Repository

Open JupyterLab terminal and run:

```bash
# Clone the repository
git clone https://github.com/red-hat-data-services/red-hat-ai-examples.git
cd red-hat-ai-examples
```

## Step 3: Install Dependencies

```bash
# Install E2E test dependencies
pip install papermill nbformat nbclient pytest ipykernel jupyter-client

# Verify installation
python -c "import papermill; print('✅ Papermill installed')"
```

## Step 4: Run E2E Tests

### Option A: Quick Validation (No GPU Required)

Test that the setup works by running a dry-run:

```bash
cd tests/e2e/knowledge_tuning
python run_e2e.py --dry-run --profile minimal
```

### Option B: Run Data Processing Steps Only (No GPU)

Skip GPU-intensive steps for quick validation:

```bash
# Using pytest
pytest tests/e2e/knowledge_tuning/ -v --e2e-profile=minimal --skip-steps=1,5,6

# OR using the standalone script
python tests/e2e/knowledge_tuning/run_e2e.py --profile minimal --skip-steps=1,5,6
```

### Option C: Run Full Pipeline (Requires GPU)

```bash
# Full pipeline with minimal profile (~30 min)
pytest tests/e2e/knowledge_tuning/ -v --e2e-profile=minimal

# Keep outputs for inspection
pytest tests/e2e/knowledge_tuning/ -v --e2e-profile=minimal --keep-outputs
```

### Option D: Run Specific Steps

```bash
# Run only steps 2, 3, 4 (Data Processing, Knowledge Gen, Mixing)
pytest tests/e2e/knowledge_tuning/ -v --skip-steps=1,5,6

# Run only step 2 (Data Processing)
python tests/e2e/knowledge_tuning/run_e2e.py --steps=2
```

## Step 5: Check Results

### View Execution Report

```bash
# If using --keep-outputs
cat examples/knowledge-tuning/test_output/e2e_execution_report.json | python -m json.tool

# OR using run_e2e.py
cat examples/knowledge-tuning/e2e_output/e2e_report.json | python -m json.tool
```

### Check Created Files

```bash
# List output directories
ls -la examples/knowledge-tuning/output/

# Check specific step outputs
ls -la examples/knowledge-tuning/output/step_02/
ls -la examples/knowledge-tuning/output/step_03/
```

## Command Reference

### pytest Options

| Option | Description | Example |
|--------|-------------|---------|
| `--e2e-profile` | Test profile (minimal/standard/extended) | `--e2e-profile=minimal` |
| `--skip-steps` | Skip specific steps | `--skip-steps=1,5,6` |
| `--keep-outputs` | Keep output files for debugging | `--keep-outputs` |
| `--student-model` | Override student model | `--student-model="Qwen/Qwen2.5-0.5B-Instruct"` |
| `--teacher-model` | Override teacher model | `--teacher-model="Qwen/Qwen2.5-0.5B-Instruct"` |

### run_e2e.py Options

| Option | Description | Example |
|--------|-------------|---------|
| `--profile` | Test profile | `--profile minimal` |
| `--steps` | Run only specific steps | `--steps 2,3,4` |
| `--skip-steps` | Skip specific steps | `--skip-steps 1,5,6` |
| `--dry-run` | Show what would run | `--dry-run` |
| `--output-dir` | Custom output directory | `--output-dir /tmp/e2e` |

## Test Profiles Comparison

| Profile | Student Model | Training Steps | Samples | Est. Time |
|---------|--------------|----------------|---------|-----------|
| `minimal` | SmolLM2-135M | 2 | 3 | ~15-30 min |
| `standard` | SmolLM2-360M | 5 | 5 | ~30-60 min |
| `extended` | Qwen2.5-0.5B | 10 | 10 | ~1-2 hours |

## Troubleshooting

### "Kernel not found" Error

```bash
# Install the Python kernel
python -m ipykernel install --user --name python3

# Verify
jupyter kernelspec list
```

### "CUDA out of memory" Error

Use a smaller model or skip GPU steps:

```bash
# Use minimal profile
pytest tests/e2e/knowledge_tuning/ -v --e2e-profile=minimal

# Or skip GPU steps
pytest tests/e2e/knowledge_tuning/ -v --skip-steps=1,5,6
```

### Timeout Errors

Increase timeout by editing `config.py` or run with fewer samples:

```bash
# Use minimal profile (lower max_samples)
pytest tests/e2e/knowledge_tuning/ -v --e2e-profile=minimal
```

### View Failed Notebook

If a notebook fails, check the executed notebook:

```bash
# List executed notebooks
ls -la examples/knowledge-tuning/test_output/

# Open in JupyterLab to see the error
# Navigate to: examples/knowledge-tuning/test_output/executed_XX_*.ipynb
```

## Example: Complete E2E Run

```bash
# 1. Navigate to repo
cd ~/red-hat-ai-examples

# 2. Install dependencies
pip install papermill nbformat nbclient pytest

# 3. Dry run first
cd tests/e2e/knowledge_tuning
python run_e2e.py --dry-run

# 4. Run minimal E2E test
cd ~/red-hat-ai-examples
pytest tests/e2e/knowledge_tuning/ -v --e2e-profile=minimal --keep-outputs

# 5. Check results
cat examples/knowledge-tuning/test_output/e2e_execution_report.json | python -m json.tool
```

## Expected Output (Success)

```text
============================================================
KNOWLEDGE-TUNING E2E PIPELINE TEST
============================================================
Profile: HuggingFaceTB/SmolLM2-135M-Instruct
Workspace: /tmp/pytest-xxx/e2e_knowledge_tuning0
Steps to execute: 6
============================================================

──────────────────────────────────────────────────
Executing: Step 01: Base Model Evaluation
──────────────────────────────────────────────────
✅ Step 01: Base Model Evaluation completed in 120.5s
   ✅ All expected outputs created

──────────────────────────────────────────────────
Executing: Step 02: Data Processing
──────────────────────────────────────────────────
✅ Step 02: Data Processing completed in 45.2s
   ✅ All expected outputs created

... (continues for all steps) ...

============================================================
PIPELINE EXECUTION SUMMARY
============================================================
Total steps: 6
Passed: 6
Failed: 0
```
