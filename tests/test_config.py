"""Test configuration and constants."""

import os
from pathlib import Path

# Test timeouts (in seconds)
TIMEOUT_UNIT = 30
TIMEOUT_INTEGRATION = 120
TIMEOUT_NOTEBOOK = 300
TIMEOUT_E2E = 600
TIMEOUT_SLOW = 1800

# Feature flags
RUN_GPU_TESTS = os.getenv("RUN_GPU_TESTS", "false").lower() == "true"
RUN_SLOW_TESTS = os.getenv("RUN_SLOW_TESTS", "false").lower() == "true"
RUN_E2E_TESTS = os.getenv("RUN_E2E_TESTS", "true").lower() == "true"
RUN_RHOAI_TESTS = os.getenv("RUN_RHOAI_TESTS", "false").lower() == "true"

# Resource requirements
MIN_MEMORY_GB = 8
RECOMMENDED_MEMORY_GB = 16
GPU_MEMORY_GB = 16

# Platform compatibility
SUPPORTED_PYTHON_VERSIONS = ["3.11", "3.12"]
SUPPORTED_PLATFORMS = ["linux", "darwin"]  # macOS for development

# Example paths
EXAMPLES_ROOT = Path(__file__).parent.parent / "examples"
LLMCOMPRESSOR_DIR = EXAMPLES_ROOT / "llmcompressor"
FINE_TUNING_DIR = EXAMPLES_ROOT / "fine-tuning"
KNOWLEDGE_TUNING_DIR = EXAMPLES_ROOT / "knowledge-tuning"
KFP_PIPELINE_DIR = EXAMPLES_ROOT / "domain_customization_kfp_pipeline"

# Test data limits (for keeping tests fast)
MAX_TEST_SAMPLES = 10
MAX_TEST_TOKENS = 512
MAX_TEST_EPOCHS = 1

# Model testing
TINY_MODEL_NAME = "hf-internal-testing/tiny-random-gpt2"  # ~500KB model for testing
TINY_TOKENIZER_NAME = "hf-internal-testing/tiny-random-gpt2"

# Notebook validation settings
NOTEBOOK_KERNEL_TIMEOUT = 300  # 5 minutes
NOTEBOOK_STARTUP_TIMEOUT = 60  # 1 minute
ALLOW_NOTEBOOK_ERRORS = False  # Fail on any notebook errors

# KFP settings
KFP_COMPILE_ONLY = True  # Only compile pipelines, don't execute
KFP_VALIDATE_SCHEMA = True

# Coverage settings
MIN_COVERAGE_PERCENT = 70
MIN_COVERAGE_UTILS = 80  # Higher requirement for utility modules

# Test markers mapping
TEST_CATEGORIES = {
    "unit": {"timeout": TIMEOUT_UNIT, "parallel": True},
    "integration": {"timeout": TIMEOUT_INTEGRATION, "parallel": True},
    "notebook": {"timeout": TIMEOUT_NOTEBOOK, "parallel": False},
    "e2e": {"timeout": TIMEOUT_E2E, "parallel": False},
}

# Notebook manifest
NOTEBOOK_CONFIGS = {
    "llmcompressor/workbench_example.ipynb": {
        "requires_gpu": False,
        "timeout": 300,
        "env_vars": [],
        "skip_reason": None,
    },
    "fine-tuning/osft/osft-example.ipynb": {
        "requires_gpu": True,
        "timeout": 1800,
        "env_vars": ["MODEL_NAME", "DATASET_PATH"],
        "skip_reason": "Requires GPU and distributed setup",
    },
    "fine-tuning/training-hub/sft/sft.ipynb": {
        "requires_gpu": True,
        "timeout": 1800,
        "env_vars": ["MODEL_NAME", "DATASET_PATH"],
        "skip_reason": "Requires GPU and Kubeflow Training operator",
    },
    "knowledge-tuning/01_Base_Model_Evaluation/Base_Model_Evaluation.ipynb": {
        "requires_gpu": False,
        "timeout": 600,
        "env_vars": ["MODEL_NAME"],
        "skip_reason": None,
    },
    "knowledge-tuning/02_Data_Processing/Data_Processing.ipynb": {
        "requires_gpu": False,
        "timeout": 600,
        "env_vars": ["DATA_URL"],
        "skip_reason": None,
    },
    "knowledge-tuning/03_Knowledge_Generation/Knowledge_Generation.ipynb": {
        "requires_gpu": False,
        "timeout": 1200,
        "env_vars": ["TEACHER_MODEL", "DATASET_PATH"],
        "skip_reason": None,
    },
    "knowledge-tuning/04_Knowledge_Mixing/Knowledge_Mixing.ipynb": {
        "requires_gpu": False,
        "timeout": 600,
        "env_vars": ["DATASET_PATH"],
        "skip_reason": None,
    },
    "knowledge-tuning/05_Model_Training/Model_Training.ipynb": {
        "requires_gpu": True,
        "timeout": 1800,
        "env_vars": ["MODEL_NAME", "DATASET_PATH"],
        "skip_reason": "Requires GPU for training",
    },
    "knowledge-tuning/06_Evaluation/Evaluation.ipynb": {
        "requires_gpu": False,
        "timeout": 600,
        "env_vars": ["MODEL_PATH"],
        "skip_reason": None,
    },
}


def should_skip_test(marker: str) -> tuple[bool, str]:
    """
    Determine if a test should be skipped based on markers and environment.

    Args:
        marker: Test marker (gpu, slow, rhoai, etc.)

    Returns:
        Tuple of (should_skip, reason)
    """
    if marker == "gpu" and not RUN_GPU_TESTS:
        return True, "GPU tests disabled (set RUN_GPU_TESTS=true to enable)"

    if marker == "slow" and not RUN_SLOW_TESTS:
        return True, "Slow tests disabled (set RUN_SLOW_TESTS=true to enable)"

    if marker == "e2e" and not RUN_E2E_TESTS:
        return True, "E2E tests disabled (set RUN_E2E_TESTS=false to disable)"

    if marker == "rhoai" and not RUN_RHOAI_TESTS:
        return True, "RHOAI tests disabled (set RUN_RHOAI_TESTS=true to enable)"

    return False, ""


def get_notebook_config(notebook_path: str) -> dict:
    """
    Get configuration for a specific notebook.

    Args:
        notebook_path: Relative path to notebook from examples dir

    Returns:
        Configuration dict for the notebook
    """
    return NOTEBOOK_CONFIGS.get(
        notebook_path,
        {
            "requires_gpu": False,
            "timeout": TIMEOUT_NOTEBOOK,
            "env_vars": [],
            "skip_reason": None,
        },
    )
