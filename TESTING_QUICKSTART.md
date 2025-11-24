# Testing Quick Start Guide

Get started with testing in 5 minutes!

## Step 1: Install Test Dependencies

```bash
# From repository root
pip install -e ".[test]"
```

This installs:
- pytest and plugins (timeout, coverage, xdist)
- notebook tools (papermill, nbformat, jupyter)
- KFP for pipeline tests
- Data libraries (yaml, dotenv)

## Step 2: Run Your First Tests

### Option A: Run Everything (Fast)

```bash
pytest tests/ -v -m "not slow and not gpu and not rhoai"
```

**Expected output**: ~100+ tests passing in < 5 minutes

### Option B: Run by Category

```bash
# Unit tests only (~30 seconds)
pytest tests/unit -v

# Integration tests (~2 minutes)
pytest tests/integration -v

# Notebook validation (~1 minute)
pytest tests/notebooks -v -m "not slow"

# E2E tests (~1 minute)
pytest tests/e2e -v -m "not gpu and not rhoai"
```

## Step 3: View Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=examples --cov-report=html

# Open in browser (macOS)
open htmlcov/index.html

# Open in browser (Linux)
xdg-open htmlcov/index.html
```

## Common Commands

### Run Specific Test File

```bash
pytest tests/unit/test_knowledge_utils.py -v
```

### Run Specific Test Class

```bash
pytest tests/unit/test_knowledge_utils.py::TestSampleDocQA -v
```

### Run Specific Test Method

```bash
pytest tests/unit/test_knowledge_utils.py::TestSampleDocQA::test_basic_sampling -v
```

### Stop on First Failure

```bash
pytest tests/ -x -v
```

### Show Print Statements

```bash
pytest tests/ -s -v
```

### Run in Parallel (faster)

```bash
pytest tests/ -n auto
```

## Understanding Test Output

### ✅ Passing Test

```
tests/unit/test_knowledge_utils.py::test_basic_sampling PASSED [100%]
```

### ❌ Failing Test

```
tests/unit/test_knowledge_utils.py::test_basic_sampling FAILED [100%]
FAILED - AssertionError: expected 3 got 2
```

### ⏭️ Skipped Test

```
tests/e2e/test_osft.py::test_osft_execution SKIPPED [100%]
SKIPPED - Requires GPU and distributed training setup
```

## Test Markers Cheat Sheet

| Command | Description |
|---------|-------------|
| `pytest -m unit` | Run only unit tests |
| `pytest -m integration` | Run only integration tests |
| `pytest -m notebook` | Run only notebook tests |
| `pytest -m e2e` | Run only E2E tests |
| `pytest -m "not slow"` | Skip slow tests |
| `pytest -m "not gpu"` | Skip GPU tests |
| `pytest -m "not rhoai"` | Skip RHOAI tests |

## Troubleshooting

### ImportError: No module named 'pytest'

```bash
pip install -e ".[test]"
```

### ImportError: No module named 'polars'

```bash
pip install polars
```

### Tests not found

Make sure you're in the repository root:

```bash
cd /path/to/red-hat-ai-examples
pytest tests/
```

### GPU tests failing

Skip GPU tests (they require NVIDIA GPU):

```bash
pytest tests/ -m "not gpu"
```

## What Gets Tested?

### ✅ All 9 Notebooks

- Structure validation (JSON format, cells, metadata)
- Content validation (no hardcoded secrets)
- Documentation (markdown, titles)

### ✅ Python Utilities

- `knowledge_utils.py` - Data sampling, message creation
- `flash_attn_installer.py` - Wheel detection and download

### ✅ Data Formats

- JSONL reading/writing
- Notebook JSON structure
- YAML configuration
- Environment files

### ✅ Dependencies

- Python version compatibility
- Library availability
- Module imports

### ✅ Complete Workflows

- LLMCompressor pipeline
- KFP domain customization
- Knowledge tuning (7 steps)
- OSFT fine-tuning
- Training Hub SFT

## Next Steps

1. **Read Full Documentation**: See `tests/README.md`
2. **View Test Details**: See `TESTING.md`
3. **Check CI Status**: View GitHub Actions workflows
4. **Add Your Own Tests**: Follow patterns in existing test files

## Quick Reference

```bash
# Install
pip install -e ".[test]"

# Run all fast tests
pytest tests/ -v -m "not slow and not gpu"

# Run with coverage
pytest tests/ --cov=examples

# Run unit tests only
pytest tests/unit -v

# Run and stop on first failure
pytest tests/ -x

# Run in parallel
pytest tests/ -n auto

# Generate HTML coverage report
pytest tests/ --cov=examples --cov-report=html
```

## Need Help?

- 📖 Full docs: `tests/README.md`
- 📊 Test overview: `TESTING.md`
- 🐛 Report issues: GitHub Issues
- 💬 Questions: Open a discussion

Happy Testing! 🧪
