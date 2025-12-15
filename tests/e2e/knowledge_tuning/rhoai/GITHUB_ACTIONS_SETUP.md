# Setting Up GitHub Actions to Run E2E Tests on RHOAI

This guide explains how to configure GitHub Actions to automatically trigger E2E tests on your RHOAI cluster.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Workflow: e2e-rhoai.yml                                        │   │
│  │  • Triggers: Nightly (2 AM UTC) / Manual / PR with label       │   │
│  │  • Orchestrates test execution                                  │   │
│  └───────────────────────────┬─────────────────────────────────────┘   │
│                              │                                          │
│                              │ 1. oc login                             │
│                              │ 2. Create Job                           │
│                              │ 3. Stream logs                          │
│                              │ 4. Get results                          │
│                              ▼                                          │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   RHOAI Cluster     │
                    │  ┌───────────────┐  │
                    │  │ Kubernetes    │  │
                    │  │ Job with GPU  │  │
                    │  │               │  │
                    │  │ • Clone repo  │  │
                    │  │ • Install deps│  │
                    │  │ • Run tests   │  │
                    │  │ • Report back │  │
                    │  └───────────────┘  │
                    └─────────────────────┘
```

## Prerequisites

1. ✅ RHOAI cluster with GPU nodes
2. ✅ Service account with permissions to create Jobs
3. ✅ GitHub repository admin access

## Step 1: Create Service Account on RHOAI

```bash
# Connect to your RHOAI cluster
oc login <your-cluster-url>

# Create namespace for E2E tests
oc new-project e2e-tests

# Create service account
oc create serviceaccount github-actions -n e2e-tests

# Grant permissions to create jobs
oc adm policy add-role-to-user edit -z github-actions -n e2e-tests

# Allow the service account to use GPU nodes
oc adm policy add-scc-to-user anyuid -z github-actions -n e2e-tests
```

## Step 2: Get Authentication Token

```bash
# Create a long-lived token for the service account
oc create token github-actions -n e2e-tests --duration=8760h > token.txt

# Get the token value
cat token.txt

# Get the cluster URL
oc whoami --show-server
```

## Step 3: Configure GitHub Secrets

Go to your GitHub repository:
**Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `OPENSHIFT_SERVER` | `https://api.your-cluster.com:6443` | OpenShift API server URL |
| `OPENSHIFT_TOKEN` | `eyJhbGc...` | Service account token from Step 2 |

![GitHub Secrets Setup](https://docs.github.com/assets/images/help/repository/actions-secret-new.png)

## Step 4: Verify the Workflow

### Manual Test Run

1. Go to **Actions** tab in your repository
2. Select **"E2E Tests on RHOAI"** workflow
3. Click **"Run workflow"**
4. Set parameters:
   - Profile: `minimal`
   - Skip steps: (leave empty for full test, or `1,5,6` for quick test)
   - Git branch: `main`
5. Click **"Run workflow"**

### Check Results

1. Click on the running workflow
2. View real-time logs from RHOAI
3. Download artifacts after completion

## Step 5: Enable Nightly Runs

The workflow is already configured to run nightly at 2 AM UTC:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Every day at 2 AM UTC
```

To change the schedule, edit `.github/workflows/e2e-rhoai.yml`.

## Step 6: Enable PR Testing (Optional)

To run E2E tests on PRs:

1. Add the `e2e-test` label to a PR
2. The workflow will automatically trigger

```yaml
on:
  pull_request:
    branches: [main]
    paths:
      - 'examples/knowledge-tuning/**'
    types: [labeled]  # Triggers when 'e2e-test' label is added
```

## Workflow Parameters

| Parameter | Default | Options | Description |
|-----------|---------|---------|-------------|
| `profile` | `minimal` | minimal/standard/extended | Test profile |
| `skip_steps` | `` | e.g., `1,5,6` | Steps to skip |
| `git_branch` | `main` | any branch | Branch to test |
| `timeout_minutes` | `120` | 30-240 | Job timeout |

## Trigger via GitHub CLI

```bash
# Run with defaults
gh workflow run e2e-rhoai.yml

# Run with custom parameters
gh workflow run e2e-rhoai.yml \
  -f profile=standard \
  -f skip_steps="" \
  -f git_branch=feature-branch \
  -f timeout_minutes=180

# Quick test (skip GPU-heavy steps)
gh workflow run e2e-rhoai.yml \
  -f profile=minimal \
  -f skip_steps="1,5,6"
```

## Monitoring & Troubleshooting

### View Job on RHOAI

```bash
# List E2E jobs
oc get jobs -n e2e-tests -l app=e2e-tests

# Get job logs
oc logs -f job/<job-name> -n e2e-tests

# Describe job for events
oc describe job <job-name> -n e2e-tests
```

### Common Issues

#### 1. Authentication Failed

```text
Error: Unable to connect to the server
```

**Solution:** Regenerate the token and update `OPENSHIFT_TOKEN` secret:

```bash
oc create token github-actions -n e2e-tests --duration=8760h
```

#### 2. No GPU Available

```text
Error: 0/10 nodes are available: Insufficient nvidia.com/gpu
```

**Solution:**

- Check GPU node availability: `oc get nodes -l nvidia.com/gpu.present=true`
- Use `skip_steps: "1,5,6"` to skip GPU-heavy steps

#### 3. Job Timeout

```text
Error: Job exceeded activeDeadlineSeconds
```

**Solution:** Increase `timeout_minutes` parameter or use `minimal` profile

#### 4. Permission Denied

```text
Error: cannot create resource "jobs"
```

**Solution:** Grant edit role to service account:

```bash
oc adm policy add-role-to-user edit -z github-actions -n e2e-tests
```

## Security Considerations

1. **Token Rotation:** Rotate the service account token periodically
2. **Least Privilege:** The service account only has access to `e2e-tests` namespace
3. **Network Policies:** Consider adding network policies to restrict pod communication
4. **Resource Quotas:** Set resource quotas to prevent runaway jobs

```bash
# Create resource quota
oc create quota e2e-quota -n e2e-tests \
  --hard=requests.nvidia.com/gpu=2 \
  --hard=limits.memory=64Gi \
  --hard=pods=5
```

## Cost Optimization

- Use `minimal` profile for regular nightly tests
- Use `standard` or `extended` only for release testing
- Set appropriate timeouts to avoid runaway jobs
- Jobs are auto-deleted after 24 hours (`ttlSecondsAfterFinished: 86400`)
