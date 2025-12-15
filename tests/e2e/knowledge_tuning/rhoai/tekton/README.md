# Tekton-based E2E Testing for Knowledge-Tuning

This directory contains Tekton Pipeline resources for running E2E tests on RHOAI with step isolation and built-in retry capabilities.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Tekton Pipeline                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│  │   Step 1    │   │   Step 2    │   │   Step 3    │   │   Step 4    │     │
│  │   (Pod 1)   │──▶│   (Pod 2)   │──▶│   (Pod 3)   │──▶│   (Pod 4)   │──▶  │
│  │             │   │             │   │             │   │             │     │
│  │ Base Model  │   │    Data     │   │ Knowledge   │   │ Knowledge   │     │
│  │ Evaluation  │   │ Processing  │   │ Generation  │   │   Mixing    │     │
│  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘     │
│                                                                              │
│  ┌─────────────┐   ┌─────────────┐                                          │
│  │   Step 5    │   │   Step 6    │    Shared PVC for data/outputs           │
│  │   (Pod 5)   │──▶│   (Pod 6)   │    ━━━━━━━━━━━━━━━━━━━━━━━━━━━           │
│  │             │   │             │                                          │
│  │   Model     │   │ Evaluation  │    Each Pod has:                         │
│  │  Training   │   │             │    • GPU access                          │
│  └─────────────┘   └─────────────┘    • Retry capability                    │
│                                       • Isolated dependencies               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Benefits over K8s Job Approach

| Feature | K8s Job | Tekton Pipeline |
|---------|---------|-----------------|
| Step isolation | ❌ Single container | ✅ Separate Pods |
| Retry per step | ❌ Manual | ✅ Built-in |
| Resource cleanup | ❌ Manual | ✅ Automatic |
| Progress visibility | ❌ Logs only | ✅ Tekton Dashboard |
| Parallel steps | ❌ No | ✅ Supported |
| Artifact passing | ❌ Manual | ✅ Workspaces |

## Files

| File | Description |
|------|-------------|
| `resources.yaml` | Namespace, PVCs, ServiceAccount |
| `task-notebook-runner.yaml` | Reusable Task for running notebooks |
| `pipeline-e2e.yaml` | Pipeline that chains all 6 steps |

## Prerequisites

1. **OpenShift Pipelines Operator** installed on RHOAI cluster
2. **GPU nodes** available with label `nvidia.com/gpu.present=true`
3. **GitHub Secrets** configured:
   - `OPENSHIFT_SERVER`: API server URL
   - `OPENSHIFT_TOKEN`: Service account token

## Quick Start

### Option 1: Via GitHub Actions

```bash
# Trigger via GitHub CLI
gh workflow run e2e-tekton.yml \
  -f profile=minimal \
  -f git_branch=main
```

### Option 2: Manual Setup on RHOAI

```bash
# 1. Apply resources
oc apply -f resources.yaml
oc apply -f task-notebook-runner.yaml
oc apply -f pipeline-e2e.yaml

# 2. Start a PipelineRun
cat <<EOF | oc apply -f -
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  generateName: e2e-manual-
  namespace: e2e-tests
spec:
  pipelineRef:
    name: e2e-knowledge-tuning
  serviceAccountName: e2e-pipeline-sa
  params:
    - name: test-profile
      value: "minimal"
  workspaces:
    - name: shared-data
      persistentVolumeClaim:
        claimName: e2e-shared-data
    - name: output-notebooks
      persistentVolumeClaim:
        claimName: e2e-output-notebooks
EOF

# 3. Watch progress
tkn pipelinerun logs -f -n e2e-tests
```

## Monitoring

### Tekton CLI

```bash
# List PipelineRuns
tkn pipelinerun list -n e2e-tests

# Watch logs
tkn pipelinerun logs <name> -f -n e2e-tests

# Describe run
tkn pipelinerun describe <name> -n e2e-tests
```

### OpenShift Console

1. Navigate to **Pipelines** → **PipelineRuns**
2. Select namespace: `e2e-tests`
3. Click on a PipelineRun to see task status

### Tekton Dashboard (if installed)

```bash
# Port-forward to dashboard
oc port-forward svc/tekton-dashboard 9097:9097 -n openshift-pipelines

# Open http://localhost:9097
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `git-url` | GitHub repo | Repository to clone |
| `git-revision` | `main` | Branch or tag |
| `test-profile` | `minimal` | Test profile |
| `student-model` | SmolLM2-135M | Model for testing |
| `teacher-model` | SmolLM2-135M | Teacher model |
| `skip-steps` | `""` | Steps to skip |

## Retry Configuration

Each task has built-in retry:

```yaml
tasks:
  - name: step-02-data-processing
    retries: 1  # Retry once on failure
    timeout: "30m"
```

To change retry count, edit `pipeline-e2e.yaml`.

## Troubleshooting

### Task stuck in Pending

```bash
# Check pod status
oc get pods -n e2e-tests -l tekton.dev/pipelineRun=<name>

# Check events
oc get events -n e2e-tests --sort-by='.lastTimestamp'
```

### GPU not allocated

```bash
# Check GPU node availability
oc get nodes -l nvidia.com/gpu.present=true

# Check pod tolerations
oc describe pod <pod-name> -n e2e-tests
```

### View task logs

```bash
# Get specific task logs
tkn taskrun logs <taskrun-name> -n e2e-tests
```

## Cleanup

```bash
# Delete old PipelineRuns (keep last 5)
tkn pipelinerun delete -n e2e-tests --keep 5

# Delete all resources
oc delete -f resources.yaml
oc delete -f task-notebook-runner.yaml
oc delete -f pipeline-e2e.yaml
```
