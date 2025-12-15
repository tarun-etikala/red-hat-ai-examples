# Running E2E Tests on RHOAI Cluster

This directory contains resources for running E2E tests directly on a Red Hat OpenShift AI (RHOAI) cluster.

## Overview

There are **3 approaches** to run E2E tests on RHOAI:

| Approach | Best For | Setup Complexity | GitHub Integration |
|----------|----------|------------------|-------------------|
| **1. OpenShift CronJob** | Scheduled testing | Low | None (native) |
| **2. OpenShift Pipelines** | CI/CD integration | Medium | Webhook triggers |
| **3. GitHub Self-Hosted Runner** | Full GitHub Actions | Medium | Full integration |

---

## Approach 1: OpenShift CronJob (Recommended for Scheduled Tests)

Run E2E tests on a schedule using native Kubernetes CronJobs.

### Setup

```bash
# 1. Create the namespace and resources
oc apply -f scheduled-e2e-job.yaml

# 2. Verify CronJob is created
oc get cronjobs -n e2e-tests

# 3. Check scheduled runs
oc get jobs -n e2e-tests
```

### Configuration

Edit the ConfigMap in `scheduled-e2e-job.yaml`:

```yaml
data:
  GIT_REPO_URL: "https://github.com/your-org/your-repo.git"
  GIT_BRANCH: "main"
  TEST_PROFILE: "minimal"  # minimal, standard, extended
  SKIP_STEPS: ""           # e.g., "1,5,6" to skip GPU-heavy steps
  STUDENT_MODEL_NAME: "HuggingFaceTB/SmolLM2-135M-Instruct"  # pragma: allowlist secret
```

### Run Manually

```bash
# Trigger an immediate run
oc create -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  generateName: e2e-manual-
  namespace: e2e-tests
spec:
  template:
    spec:
      # ... (uses template from scheduled-e2e-job.yaml)
EOF

# Or use the Job template
oc create -f scheduled-e2e-job.yaml  # Contains manual Job template
```

### View Results

```bash
# Get job status
oc get jobs -n e2e-tests

# View logs
oc logs -f job/e2e-manual-xxxxx -n e2e-tests

# Access results PVC
oc exec -it <pod-name> -n e2e-tests -- ls /results/
```

---

## Approach 2: OpenShift Pipelines (Tekton)

Use OpenShift's native CI/CD with Tekton Pipelines.

### Prerequisites

```bash
# Install OpenShift Pipelines Operator (if not installed)
# Via OpenShift Console: Operators → OperatorHub → "OpenShift Pipelines"
```

### Setup

```bash
# 1. Create namespace
oc new-project e2e-tests

# 2. Apply Pipeline resources
oc apply -f openshift-pipeline.yaml

# 3. Verify
oc get pipelines -n e2e-tests
oc get tasks -n e2e-tests
```

### Run Pipeline

```bash
# Start a PipelineRun
oc create -f - <<EOF
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  generateName: e2e-run-
  namespace: e2e-tests
spec:
  pipelineRef:
    name: e2e-knowledge-tuning-pipeline
  params:
    - name: test-profile
      value: "minimal"
    - name: skip-steps
      value: ""
  workspaces:
    - name: shared-workspace
      persistentVolumeClaim:
        claimName: e2e-workspace-pvc
EOF

# Watch progress
tkn pipelinerun logs -f -n e2e-tests
```

### GitHub Webhook Integration

```bash
# 1. Create EventListener for GitHub webhooks
oc apply -f - <<EOF
apiVersion: triggers.tekton.dev/v1beta1
kind: EventListener
metadata:
  name: github-e2e-trigger
  namespace: e2e-tests
spec:
  triggers:
    - name: github-push
      interceptors:
        - ref:
            name: github
          params:
            - name: eventTypes
              value: ["push", "pull_request"]
      bindings:
        - ref: github-binding
      template:
        ref: e2e-trigger-template
EOF

# 2. Get the webhook URL
oc get route github-e2e-trigger -n e2e-tests
```

---

## Approach 3: GitHub Self-Hosted Runner on RHOAI

Install a GitHub Actions runner inside your RHOAI workbench.

### Prerequisites

- RHOAI workbench with terminal access
- GitHub Personal Access Token with `repo` scope
- Repository admin access

### Setup

```bash
# 1. Open terminal in your RHOAI workbench

# 2. Set environment variables
export GITHUB_TOKEN="ghp_your_personal_access_token"
export GITHUB_REPO="red-hat-data-services/red-hat-ai-examples"

# 3. Run setup script
chmod +x setup-github-runner.sh
./setup-github-runner.sh

# 4. Start the runner
cd ~/actions-runner
./run.sh

# Or run in background
nohup ./run.sh > runner.log 2>&1 &
```

### Verify Runner

1. Go to: `https://github.com/<your-org>/<your-repo>/settings/actions/runners`
2. You should see your runner with labels: `self-hosted, rhoai, gpu, linux`

### Trigger Workflows

The runner will pick up jobs from `.github/workflows/e2e-tests.yml` when:

- `runner: self-hosted-rhoai` is selected
- Labels match: `self-hosted`, `rhoai`

```bash
# Trigger via GitHub CLI
gh workflow run e2e-tests.yml \
  -f profile=minimal \
  -f runner=self-hosted-rhoai \
  -f run_full_pipeline=true
```

---

## Quick Reference

### Check GPU Availability

```bash
# In RHOAI workbench or pod
nvidia-smi
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPUs: {torch.cuda.device_count()}')"
```

### Run E2E Tests Manually (in workbench)

```bash
cd ~/red-hat-ai-examples/tests/e2e/knowledge_tuning
python run_e2e.py --profile minimal --dry-run  # Verify config
python run_e2e.py --profile minimal            # Run tests
```

### View Logs

```bash
# CronJob/Job logs
oc logs -f job/<job-name> -n e2e-tests

# Pipeline logs
tkn pipelinerun logs -f <run-name> -n e2e-tests

# GitHub runner logs
tail -f ~/actions-runner/runner.log
```

---

## Troubleshooting

### GPU Not Available

```bash
# Check GPU nodes
oc get nodes -l nvidia.com/gpu.present=true

# Check if GPU is allocated
oc describe pod <pod-name> -n e2e-tests | grep -A5 "Limits:"
```

### Job Timeout

Increase `activeDeadlineSeconds` in the Job spec:

```yaml
spec:
  activeDeadlineSeconds: 28800  # 8 hours
```

### PVC Issues

```bash
# Check PVC status
oc get pvc -n e2e-tests

# Ensure storage class supports RWO
oc get storageclass
```

### Permission Issues

```bash
# Grant service account permissions
oc adm policy add-scc-to-user anyuid -z default -n e2e-tests
```

---

## Files in This Directory

| File | Description |
|------|-------------|
| `setup-github-runner.sh` | Script to install GitHub Actions runner on RHOAI |
| `openshift-pipeline.yaml` | Tekton Pipeline definition for E2E tests |
| `scheduled-e2e-job.yaml` | CronJob for scheduled E2E testing |
| `README.md` | This documentation |
