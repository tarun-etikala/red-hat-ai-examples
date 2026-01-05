# KFP-based E2E Testing for Knowledge-Tuning

This directory contains Kubeflow Pipelines (KFP) resources for running E2E tests on RHOAI Data Science Pipelines.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GitHub Actions                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Compile KFP Pipeline (Python → YAML)                                     │
│  2. Submit to RHOAI Data Science Pipelines                                   │
│  3. Wait for completion & report results                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RHOAI Data Science Pipelines                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     KFP Pipeline Run                                 │   │
│  │                                                                      │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │   │
│  │  │ Step 1 │─▶│ Step 2 │─▶│ Step 3 │─▶│ Step 4 │─▶│ Step 5 │─▶ 6    │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘        │   │
│  │                                                                      │   │
│  │  Each step:                                                          │   │
│  │  • Runs in a container                                               │   │
│  │  • Executes notebook via Papermill                                   │   │
│  │  • Logs visible in DSP UI                                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `components.py` | KFP component definitions |
| `pipeline.py` | Pipeline definitions |
| `submit_pipeline.py` | CLI tool to compile & submit pipelines |
| `README.md` | This documentation |

## Prerequisites

1. **RHOAI with Data Science Pipelines** enabled
2. **Data Science Project** with DSP instance created
3. **GitHub Secrets** configured:

   - `OPENSHIFT_TOKEN`: Service account token
   - `RHOAI_DSP_ROUTE`: Data Science Pipelines route URL

## Getting the DSP Route

```bash
# Get the DSP route from your RHOAI namespace
oc get route -n <your-dsp-namespace> | grep ds-pipeline

# Example output:
# ds-pipeline-dspa   ds-pipeline-dspa-your-ns.apps.cluster.example.com
```

The route URL would be: `https://ds-pipeline-dspa-your-ns.apps.cluster.example.com`

## Quick Start

### Option 1: Via GitHub Actions

```bash
# Run single notebook test
gh workflow run e2e-kfp.yml \
  -f pipeline=single-notebook \
  -f notebook=02_Data_Processing

# Run full E2E pipeline
gh workflow run e2e-kfp.yml \
  -f pipeline=full-e2e
```

### Option 2: Local CLI

```bash
# Install KFP
pip install kfp==2.7.0

# Compile only (for inspection)
python submit_pipeline.py \
  --pipeline single-notebook \
  --route dummy \
  --compile-only

# Submit to RHOAI
export OPENSHIFT_TOKEN="your-token"
python submit_pipeline.py \
  --pipeline single-notebook \
  --route https://ds-pipeline-dspa.apps.xxx \
  --wait
```

### Option 3: RHOAI UI

1. Compile the pipeline locally:

   ```bash
   python submit_pipeline.py --pipeline single-notebook --route dummy --compile-only
   ```

2. Go to RHOAI Dashboard → Data Science Pipelines
3. Click "Import Pipeline" and upload the YAML
4. Create a new run with your parameters

## Pipeline Options

### Single Notebook Pipeline

Tests a single notebook - useful for quick validation:

```bash
python submit_pipeline.py \
  --pipeline single-notebook \
  --notebook-path "examples/knowledge-tuning/02_Data_Processing/Data_Processing.ipynb" \
  --notebook-dir "examples/knowledge-tuning/02_Data_Processing" \
  --step-name "Data Processing Test" \
  --route $DSP_ROUTE \
  --wait
```

### Full E2E Pipeline

Runs all 6 notebooks in sequence:

```bash
python submit_pipeline.py \
  --pipeline full-e2e \
  --route $DSP_ROUTE \
  --wait \
  --timeout 180
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `student_model` | SmolLM2-135M | Student model for testing |
| `teacher_model` | SmolLM2-135M | Teacher model |
| `git_url` | GitHub repo | Repository to clone |
| `git_branch` | main | Branch to test |
| `notebook_path` | Data Processing | Notebook file path |
| `notebook_dir` | Data Processing | Notebook directory |

## Monitoring

### RHOAI Dashboard

1. Go to RHOAI Dashboard
2. Navigate to Data Science Pipelines → Runs
3. Click on your run to see:
   - Pipeline graph
   - Step status
   - Logs for each step
   - Artifacts

### CLI

```bash
# List runs (requires kfp client setup)
python -c "
from kfp import Client
client = Client(host='$DSP_ROUTE', existing_token='$OPENSHIFT_TOKEN')
for run in client.list_runs().runs[:5]:
    print(f'{run.display_name}: {run.state}')
"
```

## Troubleshooting

### "Connection refused" error

Ensure the DSP route is correct:

```bash
oc get route -n <namespace> | grep ds-pipeline
```

### "Unauthorized" error

Token may have expired. Generate a new one:

```bash
oc whoami -t
```

### Pipeline stuck in "Pending"

Check if there are available resources:

```bash
oc get pods -n <namespace> | grep -E "(Pending|Running)"
```

## Comparison with Other Approaches

| Feature | KFP | Tekton | K8s Job |
|---------|-----|--------|---------|
| Native RHOAI UI | ✅ Yes | ❌ No | ❌ No |
| Visual pipeline graph | ✅ Yes | ✅ Yes | ❌ No |
| Artifact tracking | ✅ Yes | ❌ No | ❌ No |
| Step-level retry | ✅ Yes | ✅ Yes | ❌ No |
| ML-focused | ✅ Yes | ❌ No | ❌ No |
| Setup complexity | Medium | High | Low |
