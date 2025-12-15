#!/bin/bash
# =============================================================================
# Setup GitHub Actions Self-Hosted Runner on RHOAI Workbench
# =============================================================================
# This script installs and configures a GitHub Actions runner inside your
# RHOAI workbench, allowing GitHub Actions workflows to execute on RHOAI.
#
# Prerequisites:
# - Running RHOAI workbench with terminal access
# - GitHub Personal Access Token with 'repo' scope
# - Repository admin access to configure runners
#
# Usage:
#   export GITHUB_TOKEN="your_personal_access_token"
#   export GITHUB_REPO="owner/repo-name"
#   ./setup-github-runner.sh
# =============================================================================

set -e

# Configuration
RUNNER_VERSION="2.321.0"
RUNNER_NAME="${RUNNER_NAME:-rhoai-e2e-runner}"
RUNNER_LABELS="${RUNNER_LABELS:-self-hosted,rhoai,gpu,linux}"
RUNNER_WORK_DIR="${RUNNER_WORK_DIR:-_work}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}RHOAI GitHub Actions Runner Setup${NC}"
echo -e "${GREEN}============================================${NC}"

# Check required environment variables
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ Error: GITHUB_TOKEN environment variable is required${NC}"
    echo "   Export your GitHub Personal Access Token:"
    echo "   export GITHUB_TOKEN='ghp_xxxxxxxxxxxx'"
    exit 1
fi

if [ -z "$GITHUB_REPO" ]; then
    echo -e "${RED}❌ Error: GITHUB_REPO environment variable is required${NC}"
    echo "   Export your repository (owner/repo format):"
    echo "   export GITHUB_REPO='red-hat-data-services/red-hat-ai-examples'"
    exit 1
fi

# Create runner directory
RUNNER_DIR="$HOME/actions-runner"
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

echo -e "${YELLOW}📦 Downloading GitHub Actions Runner v${RUNNER_VERSION}...${NC}"

# Download runner (Linux x64)
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

echo -e "${YELLOW}🔑 Getting registration token...${NC}"

# Get registration token from GitHub API
REG_TOKEN=$(curl -s -X POST \
    -H "Authorization: token ${GITHUB_TOKEN}" \
    -H "Accept: application/vnd.github.v3+json" \
    "https://api.github.com/repos/${GITHUB_REPO}/actions/runners/registration-token" \
    | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

if [ -z "$REG_TOKEN" ] || [ "$REG_TOKEN" == "null" ]; then
    echo -e "${RED}❌ Failed to get registration token. Check your GITHUB_TOKEN permissions.${NC}"
    exit 1
fi

echo -e "${YELLOW}⚙️ Configuring runner...${NC}"

# Configure the runner
./config.sh \
    --url "https://github.com/${GITHUB_REPO}" \
    --token "${REG_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --labels "${RUNNER_LABELS}" \
    --work "${RUNNER_WORK_DIR}" \
    --unattended \
    --replace

echo -e "${GREEN}✅ Runner configured successfully!${NC}"
echo ""
echo -e "${YELLOW}To start the runner:${NC}"
echo "   cd $RUNNER_DIR && ./run.sh"
echo ""
echo -e "${YELLOW}To run in background:${NC}"
echo "   cd $RUNNER_DIR && nohup ./run.sh &"
echo ""
echo -e "${YELLOW}Runner labels: ${RUNNER_LABELS}${NC}"
echo ""
echo -e "${GREEN}The runner will appear in:${NC}"
echo "   https://github.com/${GITHUB_REPO}/settings/actions/runners"
