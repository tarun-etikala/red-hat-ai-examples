#!/bin/bash
# =============================================================================
# Trigger E2E Tekton Pipeline on RHOAI
# =============================================================================
# Usage: ./trigger-pipeline.sh [--profile <minimal|standard|extended>] [--branch <branch>]
# =============================================================================

set -e

# Default values
PROFILE="minimal"
GIT_BRANCH="main"
GIT_URL="https://github.com/red-hat-data-services/red-hat-ai-examples.git"
SKIP_STEPS=""
NAMESPACE="e2e-tests"
MODE="single-pod"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)
      PROFILE="$2"
      shift 2
      ;;
    --branch)
      GIT_BRANCH="$2"
      shift 2
      ;;
    --skip)
      SKIP_STEPS="$2"
      shift 2
      ;;
    --namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --profile <minimal|standard|extended>  Test profile (default: minimal)"
      echo "  --mode <single-pod|multi-pod>          Execution mode (default: single-pod)"
      echo "  --branch <branch>                      Git branch to test (default: main)"
      echo "  --skip <steps>                         Steps to skip, comma-separated (e.g., '1,5,6')"
      echo "  --namespace <ns>                       Kubernetes namespace (default: e2e-tests)"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Select model based on profile
case $PROFILE in
  minimal)
    MODEL="HuggingFaceTB/SmolLM2-135M-Instruct"  # pragma: allowlist secret
    ;;
  standard)
    MODEL="HuggingFaceTB/SmolLM2-360M-Instruct"  # pragma: allowlist secret
    ;;
  extended)
    MODEL="Qwen/Qwen2.5-0.5B-Instruct"  # pragma: allowlist secret
    ;;
  *)
    echo "❌ Invalid profile: $PROFILE"
    exit 1
    ;;
esac

# Set pipeline name based on mode
if [ "$MODE" == "single-pod" ]; then
  PIPELINE_NAME="e2e-knowledge-tuning-single-pod"
else
  PIPELINE_NAME="e2e-knowledge-tuning"
fi

# Generate unique run name
RUN_NAME="e2e-manual-$(date +%Y%m%d-%H%M%S)"

echo "🚀 Triggering E2E Tekton Pipeline"
echo "=================================="
echo "   Name:    $RUN_NAME"
echo "   Mode:    $MODE"
echo "   Profile: $PROFILE"
echo "   Model:   $MODEL"
echo "   Branch:  $GIT_BRANCH"
echo "   Skip:    ${SKIP_STEPS:-None}"
echo ""

# Check if logged into OpenShift
if ! oc whoami > /dev/null 2>&1; then
  echo "❌ Not logged into OpenShift. Please run 'oc login' first."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if namespace exists (admin setup required)
if ! oc get namespace "$NAMESPACE" > /dev/null 2>&1; then
  echo "❌ Namespace '$NAMESPACE' does not exist!"
  echo ""
  echo "A cluster administrator must first run:"
  echo "  oc apply -f $SCRIPT_DIR/setup-admin.yaml"
  echo ""
  echo "Then generate a token if needed:"
  echo "  oc create token github-actions -n $NAMESPACE --duration=8760h"
  exit 1
fi

# Apply Tekton resources
echo "📦 Applying Tekton resources..."

# Apply PVCs only for multi-pod mode
if [ "$MODE" == "multi-pod" ]; then
  oc apply -f "$SCRIPT_DIR/resources.yaml" || true
fi

if [ "$MODE" == "single-pod" ]; then
  oc apply -f "$SCRIPT_DIR/task-e2e-single-pod.yaml"
  oc apply -f "$SCRIPT_DIR/pipeline-single-pod.yaml"
else
  oc apply -f "$SCRIPT_DIR/task-notebook-runner.yaml"
  oc apply -f "$SCRIPT_DIR/pipeline-e2e.yaml"
fi
echo "✅ Resources applied"

# Create PipelineRun
if [ "$MODE" == "single-pod" ]; then
  # Single-pod mode (no workspaces needed)
  cat <<EOF | oc apply -f -
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  name: ${RUN_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: e2e-tests
    trigger: manual
    mode: single-pod
spec:
  pipelineRef:
    name: ${PIPELINE_NAME}
  serviceAccountName: e2e-pipeline-sa
  params:
    - name: git-url
      value: "${GIT_URL}"
    - name: git-revision
      value: "${GIT_BRANCH}"
    - name: test-profile
      value: "${PROFILE}"
    - name: student-model
      value: "${MODEL}"
    - name: teacher-model
      value: "${MODEL}"
    - name: skip-steps
      value: "${SKIP_STEPS}"
  podTemplate:
    tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
    nodeSelector:
      nvidia.com/gpu.present: "true"
EOF
else
  # Multi-pod mode (uses PVC workspaces)
  cat <<EOF | oc apply -f -
apiVersion: tekton.dev/v1beta1
kind: PipelineRun
metadata:
  name: ${RUN_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: e2e-tests
    trigger: manual
    mode: multi-pod
spec:
  pipelineRef:
    name: ${PIPELINE_NAME}
  serviceAccountName: e2e-pipeline-sa
  params:
    - name: git-url
      value: "${GIT_URL}"
    - name: git-revision
      value: "${GIT_BRANCH}"
    - name: test-profile
      value: "${PROFILE}"
    - name: student-model
      value: "${MODEL}"
    - name: teacher-model
      value: "${MODEL}"
    - name: skip-steps
      value: "${SKIP_STEPS}"
  workspaces:
    - name: shared-data
      persistentVolumeClaim:
        claimName: e2e-shared-data
    - name: output-notebooks
      persistentVolumeClaim:
        claimName: e2e-output-notebooks
  podTemplate:
    tolerations:
      - key: "nvidia.com/gpu"
        operator: "Exists"
        effect: "NoSchedule"
    nodeSelector:
      nvidia.com/gpu.present: "true"
EOF
fi

echo ""
echo "✅ PipelineRun created: $RUN_NAME"
echo ""
echo "📊 Monitor with:"
echo "   tkn pipelinerun logs $RUN_NAME -f -n $NAMESPACE"
echo ""
echo "🔍 Or check status:"
echo "   oc get pipelinerun $RUN_NAME -n $NAMESPACE"
