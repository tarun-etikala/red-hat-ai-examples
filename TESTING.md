# Testing Infrastructure for Red Hat AI Examples

This document provides an overview of the testing infrastructure implemented for the Red Hat AI Examples repository.

## Overview

A comprehensive testing framework has been established to validate:
- ✅ All 9 Jupyter notebooks (structure, format, content)
- ✅ Python utility modules (knowledge_utils.py, flash_attn_installer.py)
- ✅ Data formats (JSONL, notebooks, YAML, .env files)
- ✅ Dependencies and compatibility
- ✅ End-to-end workflows for all 4 example categories

## Test Statistics

- **Total Test Files**: 14
- **Test Categories**: 4 (unit, integration, notebook, e2e)
- **Notebooks Covered**: 9/9 (100%)
- **Examples Covered**: 4/4 (100%)
- **Python Utility Modules Tested**: 2/2 (100%)

## Quick Start

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all fast tests
pytest tests/ -v -m "not slow and not gpu and not rhoai"

# Run with coverage
pytest tests/ --cov=examples --cov-report=html
```

## Test Suite Breakdown

### 1. Unit Tests (tests/unit/)

**Purpose**: Test utility functions in isolation

**Files**:
- `test_knowledge_utils.py` - 13 test classes, 40+ test methods
  - Tests data sampling, message creation, metadata generation
  - Tests JSONL dataset generation
  - Tests token counting functionality

- `test_flash_attn_installer.py` - 4 test classes, 20+ test methods
  - Tests URL construction for flash-attention wheels
  - Tests platform/CUDA detection
  - Tests download functionality (mocked)

**Run**: `pytest tests/unit -v`

**Expected Time**: < 30 seconds

---

### 2. Integration Tests (tests/integration/)

**Purpose**: Test dependencies and data format handling

**Files**:
- `test_dependencies.py` - 8 test classes
  - Tests Python version compatibility
  - Tests ML/AI library availability (PyTorch, Transformers, Datasets)
  - Tests data libraries (Polars, KFP)
  - Tests notebook dependencies (Papermill, Jupyter)
  - Tests module imports

- `test_data_formats.py` - 7 test classes
  - Tests JSONL reading/writing
  - Tests notebook JSON structure
  - Tests .env file parsing
  - Tests YAML configuration
  - Tests message formats
  - Tests Polars DataFrame operations

**Run**: `pytest tests/integration -v`

**Expected Time**: < 2 minutes

---

### 3. Notebook Validation Tests (tests/notebooks/)

**Purpose**: Validate structure and content of all Jupyter notebooks

**Files**:
- `test_notebook_validation.py` - 4 test classes
  - **TestNotebookStructure**: Format validation (nbformat schema, cells, metadata)
  - **TestNotebookContent**: Content validation (no hardcoded secrets, env var usage)
  - **TestNotebookDocumentation**: Documentation checks (markdown, titles)
  - **TestNotebookExecution**: Execution tests (marked as slow)
  - **TestNotebookConfiguration**: Manifest consistency

- `notebooks_manifest.yaml` - Registry of all 9 notebooks
  - Metadata: GPU requirements, timeouts, env vars
  - Tags for categorization
  - Skip flags for platform-specific notebooks

**Notebooks Tested**:
1. llmcompressor/workbench_example.ipynb
2. fine-tuning/osft/osft-example.ipynb
3. fine-tuning/training-hub/sft/sft.ipynb
4. knowledge-tuning/01_Base_Model_Evaluation/Base_Model_Evaluation.ipynb
5. knowledge-tuning/02_Data_Processing/Data_Processing.ipynb
6. knowledge-tuning/03_Knowledge_Generation/Knowledge_Generation.ipynb
7. knowledge-tuning/04_Knowledge_Mixing/Knowledge_Mixing.ipynb
8. knowledge-tuning/05_Model_Training/Model_Training.ipynb
9. knowledge-tuning/06_Evaluation/Evaluation.ipynb

**Run**: `pytest tests/notebooks -v -m "not slow"`

**Expected Time**: < 1 minute (structure tests), < 30 minutes (with execution)

---

### 4. End-to-End Tests (tests/e2e/)

**Purpose**: Validate complete workflows for each example

**Files**:
- `test_llmcompressor.py` - Tests for LLMCompressor example
  - Pipeline component validation
  - KFP compilation tests
  - Notebook structure
  - Requirements validation

- `test_kfp_pipeline.py` - Tests for domain customization pipeline
  - Python script validation
  - YAML compilation validation
  - Environment configuration
  - Component structure

- `test_knowledge_tuning.py` - Tests for knowledge tuning workflow
  - 7-step workflow validation
  - Utility module availability
  - Dependencies per step
  - Sequential flow verification

- `test_osft.py` - Tests for OSFT fine-tuning
  - Directory structure
  - Notebook existence
  - Documentation validation

- `test_training_hub_sft.py` - Tests for Training Hub SFT
  - Directory structure
  - Notebook existence
  - Documentation validation

**Run**: `pytest tests/e2e -v -m "not gpu and not rhoai"`

**Expected Time**: < 1 minute (validation), < 1 hour (with execution)

---

## Test Infrastructure Files

### Core Configuration

- **pytest.ini**: Pytest configuration, markers, coverage settings
- **pyproject.toml**: Project metadata, test dependencies
- **tests/conftest.py**: Shared fixtures (temp directories, sample data, GPU detection)
- **tests/test_config.py**: Test timeouts, feature flags, notebook configs

### CI/CD Integration

- **.github/workflows/code-quality.yml**: Updated to include test execution
- **.github/workflows/tests.yml**: Comprehensive test matrix (new)
  - Multiple Python versions (3.11, 3.12)
  - Parallel test execution
  - Coverage reporting
  - Test result artifacts

---

## Test Markers

Tests can be selectively run using pytest markers:

```bash
# Run only unit tests
pytest -m unit

# Run tests without GPU requirement
pytest -m "not gpu"

# Run fast tests only
pytest -m "not slow"

# Run notebook tests
pytest -m notebook

# Run E2E tests
pytest -m e2e
```

**Available Markers**:
- `unit` - Unit tests (fast)
- `integration` - Integration tests
- `notebook` - Notebook validation
- `e2e` - End-to-end tests
- `gpu` - Requires GPU
- `slow` - Takes >60 seconds
- `rhoai` - Requires Red Hat OpenShift AI
- `kfp` - Requires Kubeflow Pipelines
- `requires_model` - Requires model downloads
- `requires_data` - Requires dataset downloads

---

## Environment Variables

Control test execution:

```bash
# Enable GPU tests
export RUN_GPU_TESTS=true

# Enable slow tests (notebook execution, etc.)
export RUN_SLOW_TESTS=true

# Enable RHOAI-specific tests
export RUN_RHOAI_TESTS=true

# Disable E2E tests
export RUN_E2E_TESTS=false
```

---

## Coverage Goals

- **Overall**: >70% code coverage
- **Utility modules**: >80% code coverage
- **Critical paths**: 100% coverage

Generate coverage report:

```bash
pytest tests/ --cov=examples --cov-report=html
open htmlcov/index.html
```

---

## CI/CD Workflows

### On Every Push/PR

**code-quality.yml** runs:
1. Linting (Ruff)
2. Formatting (Ruff)
3. Markdown linting
4. Secret scanning (Gitleaks, Talisman)
5. **Unit tests** ✨ NEW
6. **Integration tests** ✨ NEW
7. **Notebook validation** ✨ NEW

### Comprehensive Testing

**tests.yml** runs:
1. Unit tests (Python 3.11, 3.12)
2. Integration tests
3. Notebook validation
4. E2E tests
5. Coverage reporting
6. Test result artifacts

**Triggers**:
- Push to main
- Pull requests
- Weekly schedule (Sundays 2 AM UTC)
- Manual dispatch

---

## Test Dependencies

Core testing libraries (installed via `pip install -e ".[test]"`):

- `pytest>=8.0.0` - Test framework
- `pytest-timeout>=2.2.0` - Timeout management
- `pytest-xdist>=3.5.0` - Parallel execution
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Mocking support
- `papermill>=2.5.0` - Notebook execution
- `nbformat>=5.9.0` - Notebook validation
- `nbconvert>=7.14.0` - Notebook conversion
- `jupyter>=1.0.0` - Jupyter kernel
- `kfp>=2.0.0` - KFP validation
- `pyyaml>=6.0` - YAML parsing
- `python-dotenv>=1.0.0` - Environment handling

---

## Future Enhancements

Potential additions:

1. **Model Testing**: Add tests with tiny models for inference validation
2. **Dataset Testing**: Add tests with small sample datasets
3. **Performance Testing**: Add benchmark tests for critical operations
4. **GPU Testing**: Add GPU-specific test suite
5. **RHOAI Integration Testing**: Add platform-specific tests
6. **Notebook Execution Tests**: Full execution tests for all notebooks
7. **Security Testing**: Expand secret detection and vulnerability scanning

---

## Maintenance

### Adding New Examples

When adding new examples:

1. Add notebook to `tests/notebooks/notebooks_manifest.yaml`
2. Create E2E test file in `tests/e2e/`
3. Add utility tests if example includes Python modules
4. Update this document

### Updating Tests

When modifying examples:

1. Update relevant test assertions
2. Update notebook manifest if configs change
3. Run full test suite to verify: `pytest tests/ -v`

---

## Support

- **Documentation**: See `tests/README.md` for detailed test documentation
- **Issues**: Report test failures with full output
- **CI Logs**: Check GitHub Actions for detailed test results

---

## Summary

The testing infrastructure provides:

✅ **Comprehensive Coverage**: All notebooks, utilities, and workflows tested
✅ **Multiple Test Levels**: Unit, integration, notebook, and E2E tests
✅ **CI/CD Integration**: Automated testing on every commit
✅ **Flexible Execution**: Selective test runs with markers
✅ **Clear Documentation**: Extensive docs for developers
✅ **Maintainability**: Well-organized structure for easy updates

**Total Lines of Test Code**: ~3,000+
**Total Test Files**: 14
**Total CI/CD Workflows**: 2
