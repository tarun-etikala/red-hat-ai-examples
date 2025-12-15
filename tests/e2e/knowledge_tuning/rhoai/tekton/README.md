# Tekton-based E2E Testing for Knowledge-Tuning

This directory contains Tekton Pipeline resources for running E2E tests on RHOAI with Tekton Dashboard visibility and built-in retry capabilities.

## Two Execution Modes

### Single-Pod Mode (Default, Recommended)

All 6 notebooks run in a **single Pod** with step-by-step visibility:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Single Pod (Tekton Task)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   │
│  │ Step 1 │─▶│ Step 2 │─▶│ Step 3 │─▶│ Step 4 │─▶│ Step 5 │─▶│ Step 6 │   │
│  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘   │
│                                                                              │
│  ✅ Fast startup (single Pod)          ✅ Tekton Dashboard visibility        │
│  ✅ Simple debugging (one log stream)  ✅ Built-in retry at Task level       │
│  ✅ Shared GPU/filesystem              ✅ No PVC required                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Multi-Pod Mode (Optional)

Each notebook runs in a **separate Pod** for step isolation:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐       │
│  │  Pod 1  │──▶│  Pod 2  │──▶│  Pod 3  │──▶│  Pod 4  │──▶│  Pod 5  │──▶ 6  │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘       │
│        ↓           ↓             ↓             ↓             ↓              │
│   ═══════════════ Shared PVC for data/outputs ═══════════════════          │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Mode Comparison

| Feature | Single-Pod | Multi-Pod |
|---------|------------|-----------|
| Startup time | ✅ Fast | ❌ Slower (Pod per step) |
| Debugging | ✅ Simple | ❌ Multiple logs |
| Step retry | ✅ Task level | ✅ Per-step |
| Dashboard visibility | ✅ Yes | ✅ Yes |
| Step isolation | ❌ Shared | ✅ Isolated |
| PVC required | ❌ No | ✅ Yes |

## Files

| File | Description |
|------|-------------|
| `resources.yaml` | Namespace, PVCs, ServiceAccount |
| `task-e2e-single-pod.yaml` | Single-pod Task (all steps in one Pod) |
| `pipeline-single-pod.yaml` | Pipeline wrapper for single-pod mode |
| `task-notebook-runner.yaml` | Multi-pod Task (one notebook per call) |
| `pipeline-e2e.yaml` | Multi-pod Pipeline (6 TaskRuns) |

## Prerequisites

1. **OpenShift Pipelines Operator** installed on RHOAI cluster
2. **GPU nodes** available with label `nvidia.com/gpu.present=true`
3. **GitHub Secrets** configured:
   - `OPENSHIFT_SERVER`: API server URL
   - `OPENSHIFT_TOKEN`: Service account token

## Quick Start

### Option 1: Via GitHub Actions

```bash
# Single-pod mode (default, recommended)
gh workflow run e2e-tekton.yml \
  -f profile=minimal \
  -f mode=single-pod

# Multi-pod mode (step isolation)
gh workflow run e2e-tekton.yml \
  -f profile=minimal \
  -f mode=multi-pod
```

### Option 2: Using trigger script

```bash
# Single-pod mode (default)
./trigger-pipeline.sh --profile minimal

# Multi-pod mode
./trigger-pipeline.sh --profile minimal --mode multi-pod

# With options
./trigger-pipeline.sh --profile standard --branch feature-branch --skip "1,6"
```

### Option 3: Manual Setup on RHOAI

```bash
# 1. Apply resources (single-pod mode)
oc apply -f resources.yaml
oc apply -f task-e2e-single-pod.yaml
oc apply -f pipeline-single-pod.yaml

# 2. Start a PipelineRun
cat <<EOF | oc apply -f -
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  generateName: e2e-manual-
  namespace: e2e-tests
spec:
  pipelineRef:
    name: e2e-knowledge-tuning-single-pod
  serviceAccountName: e2e-pipeline-sa
  params:
    - name: test-profile
      value: "minimal"
  podTemplate:
    tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
    nodeSelector:
      nvidia.com/gpu.present: "true"
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
