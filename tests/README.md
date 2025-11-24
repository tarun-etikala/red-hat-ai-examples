# Tests for Red Hat AI Examples

This directory contains a comprehensive test suite for validating the Red Hat AI Examples repository.

## Test Structure

```
tests/
├── unit/                    # Unit tests for utility functions
├── integration/             # Integration tests for dependencies and data formats
├── notebooks/               # Notebook validation tests
├── e2e/                     # End-to-end tests for complete workflows
├── fixtures/                # Test data and fixtures
├── conftest.py             # Shared pytest fixtures
└── test_config.py          # Test configuration
```

## Test Categories

### Unit Tests (`tests/unit/`)

Fast, isolated tests for utility modules:

- **test_knowledge_utils.py**: Tests for knowledge tuning utilities
- **test_flash_attn_installer.py**: Tests for flash attention installer

**Run**: `pytest tests/unit -v`

### Integration Tests (`tests/integration/`)

Tests for dependency installation and data format handling:

- **test_dependencies.py**: Dependency availability and compatibility
- **test_data_formats.py**: JSONL, notebook, and YAML format validation

**Run**: `pytest tests/integration -v`

### Notebook Validation Tests (`tests/notebooks/`)

Validates all Jupyter notebooks in the repository:

- **test_notebook_validation.py**: Structure, format, and content validation
- **notebooks_manifest.yaml**: Registry of all notebooks with metadata

**Run**: `pytest tests/notebooks -v -m "not slow"`

### End-to-End Tests (`tests/e2e/`)

Complete workflow validation for each example:

- **test_llmcompressor.py**: LLMCompressor pipeline tests
- **test_kfp_pipeline.py**: Domain customization KFP pipeline tests
- **test_knowledge_tuning.py**: Knowledge tuning workflow tests
- **test_osft.py**: OSFT fine-tuning tests
- **test_training_hub_sft.py**: Training Hub SFT tests

**Run**: `pytest tests/e2e -v -m "not gpu and not rhoai"`

## Quick Start

### 1. Install Test Dependencies

```bash
# From repository root
pip install -e ".[test]"
```

### 2. Run All Tests

```bash
# Run everything (fast tests only)
pytest tests/ -v -m "not slow and not gpu and not rhoai"

# Run with coverage
pytest tests/ --cov=examples --cov-report=html
```

### 3. Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Notebook validation (no execution)
pytest tests/notebooks -v -m "not slow"

# E2E tests (no GPU/RHOAI required)
pytest tests/e2e -v -m "not gpu and not rhoai"
```

## Test Markers

Tests are organized using pytest markers:

| Marker | Description |
|--------|-------------|
| `unit` | Fast unit tests |
| `integration` | Integration tests |
| `notebook` | Notebook validation tests |
| `e2e` | End-to-end tests |
| `gpu` | Requires GPU |
| `slow` | Takes >60 seconds |
| `rhoai` | Requires Red Hat OpenShift AI |
| `kfp` | Requires Kubeflow Pipelines |
| `requires_model` | Requires model downloads |
| `requires_data` | Requires dataset downloads |

### Running Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run tests that don't require GPU
pytest -m "not gpu"

# Run fast notebook validation tests
pytest -m "notebook and not slow"
```

## Configuration

### Environment Variables

Control test execution with environment variables:

```bash
# Enable GPU tests
export RUN_GPU_TESTS=true

# Enable slow tests
export RUN_SLOW_TESTS=true

# Enable RHOAI-specific tests
export RUN_RHOAI_TESTS=true

# Disable E2E tests
export RUN_E2E_TESTS=false
```

### Test Timeouts

Default timeouts per category (in `test_config.py`):

- Unit tests: 30 seconds
- Integration tests: 120 seconds
- Notebook tests: 300 seconds
- E2E tests: 600 seconds

## CI/CD Integration

Tests run automatically in GitHub Actions:

### Code Quality Workflow (`.github/workflows/code-quality.yml`)

- Runs on every push and PR
- Executes: linting, formatting, secret scanning, and basic tests

### Comprehensive Tests Workflow (`.github/workflows/tests.yml`)

- Runs on push, PR, and weekly schedule
- Executes: all test categories across multiple Python versions
- Generates coverage reports

## Test Development Guidelines

### Adding New Tests

1. **Unit Tests**: Add to appropriate file in `tests/unit/`
2. **Integration Tests**: Add to `tests/integration/`
3. **Notebook Tests**: Update `notebooks_manifest.yaml` if adding new notebooks
4. **E2E Tests**: Add to appropriate example test file in `tests/e2e/`

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Writing Good Tests

```python
import pytest

@pytest.mark.unit
def test_function_name():
    """Clear description of what is being tested."""
    # Arrange
    input_data = create_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

### Using Fixtures

```python
def test_with_fixture(temp_dir, sample_jsonl_file):
    """Use shared fixtures from conftest.py."""
    output_file = temp_dir / "output.jsonl"
    process_jsonl(sample_jsonl_file, output_file)
    assert output_file.exists()
```

## Troubleshooting

### Common Issues

**Issue**: `ImportError: No module named 'polars'`
**Solution**: Install optional dependencies: `pip install polars`

**Issue**: Tests fail with "GPU not available"
**Solution**: Skip GPU tests: `pytest -m "not gpu"`

**Issue**: Notebook validation fails
**Solution**: Check `notebooks_manifest.yaml` for correct paths

**Issue**: Test discovery finds no tests
**Solution**: Ensure you're in the repository root and tests have `test_` prefix

### Debug Mode

Run tests with verbose output and stop on first failure:

```bash
pytest tests/ -vv -x --tb=short
```

### Show Print Statements

```bash
pytest tests/ -v -s
```

## Coverage Reports

Generate HTML coverage report:

```bash
pytest tests/ --cov=examples --cov-report=html
open htmlcov/index.html
```

Target coverage:
- Overall: >70%
- Utility modules: >80%

## Contributing

When adding new examples to the repository:

1. Add notebook to `notebooks_manifest.yaml`
2. Create E2E test in appropriate `tests/e2e/test_*.py` file
3. Add any utility modules to unit tests
4. Update this README if adding new test categories

## Support

For questions or issues:

1. Check this README
2. Review test output for detailed error messages
3. Check CI logs in GitHub Actions
4. Open an issue with test failure details
