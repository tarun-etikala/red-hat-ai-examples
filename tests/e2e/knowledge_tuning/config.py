"""
Configuration for E2E testing of knowledge-tuning workflow.

This module defines test configurations for running the knowledge-tuning
workflow with small models and minimal data for faster CI/CD execution.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class E2ETestConfig:
    """Configuration for E2E notebook execution tests."""

    # =========================================================================
    # Model Configuration - Use small models for faster testing
    # =========================================================================

    # Student model - use a small model for testing
    # Options for small models (see HuggingFace for available models):
    # - SmolLM2 135M/360M (very fast)
    # - Qwen 0.5B (good quality)
    # - Phi 1.5B (slower but higher quality)
    student_model_name: str = (
        "HuggingFaceTB/SmolLM2-135M-Instruct"  # pragma: allowlist secret
    )

    # Teacher model for knowledge generation
    # For E2E testing, we can use the same small model or mock the API
    teacher_model_name: str = (
        "HuggingFaceTB/SmolLM2-360M-Instruct"  # pragma: allowlist secret
    )
    teacher_model_base_url: Optional[str] = None  # Set if using external API
    teacher_model_api_key: Optional[str] = None

    # =========================================================================
    # Training Configuration - Minimal for testing
    # =========================================================================

    # Reduced training parameters for E2E tests
    max_steps: int = 5  # Very few steps for testing
    per_device_train_batch_size: int = 1
    gradient_accumulation_steps: int = 1
    learning_rate: float = 2e-5
    warmup_steps: int = 1
    logging_steps: int = 1
    save_steps: int = 5
    max_seq_length: int = 256  # Reduced sequence length

    # =========================================================================
    # Data Configuration - Minimal sample data
    # =========================================================================

    # Use minimal data samples for testing
    max_samples: int = 5  # Only process a few samples
    test_chunk_size: int = 200  # Smaller chunks for testing

    # =========================================================================
    # Execution Configuration
    # =========================================================================

    # Notebook execution timeout (in seconds)
    notebook_timeout: int = 1800  # 30 minutes per notebook
    cell_timeout: int = 600  # 10 minutes per cell

    # Skip GPU-intensive cells in CI (set via environment)
    skip_gpu_cells: bool = False

    # =========================================================================
    # Path Configuration
    # =========================================================================

    # These are set dynamically based on workspace
    workspace_dir: Optional[Path] = None
    output_dir: Optional[Path] = None

    def get_env_vars(self) -> dict:
        """Get environment variables for notebook execution."""
        env_vars = {
            "STUDENT_MODEL_NAME": self.student_model_name,
            "TEACHER_MODEL_NAME": self.teacher_model_name,
            # Training overrides for minimal testing
            "E2E_TEST_MODE": "true",
            "MAX_STEPS": str(self.max_steps),
            "PER_DEVICE_TRAIN_BATCH_SIZE": str(self.per_device_train_batch_size),
            "GRADIENT_ACCUMULATION_STEPS": str(self.gradient_accumulation_steps),
            "LEARNING_RATE": str(self.learning_rate),
            "WARMUP_STEPS": str(self.warmup_steps),
            "MAX_SEQ_LENGTH": str(self.max_seq_length),
            "MAX_SAMPLES": str(self.max_samples),
        }

        if self.teacher_model_base_url:
            env_vars["TEACHER_MODEL_BASE_URL"] = self.teacher_model_base_url
        if self.teacher_model_api_key:
            env_vars["TEACHER_MODEL_API_KEY"] = self.teacher_model_api_key
        if self.workspace_dir:
            env_vars["WORKSPACE"] = str(self.workspace_dir)

        return env_vars


@dataclass
class NotebookStep:
    """Represents a single notebook step in the workflow."""

    step_number: int
    name: str
    notebook_path: str
    readme_path: str
    expected_outputs: list = field(default_factory=list)
    requires_gpu: bool = False
    skip_in_ci: bool = False
    timeout_override: Optional[int] = None

    @property
    def display_name(self) -> str:
        """Human-readable step name."""
        return f"Step {self.step_number:02d}: {self.name}"


# Define the knowledge-tuning workflow steps
KNOWLEDGE_TUNING_STEPS = [
    NotebookStep(
        step_number=1,
        name="Base Model Evaluation",
        notebook_path="01_Base_Model_Evaluation/Base_Model_Evaluation.ipynb",
        readme_path="01_Base_Model_Evaluation/01_Base_Model_Evaluation_README.md",
        expected_outputs=["output/base_model"],
        requires_gpu=True,
    ),
    NotebookStep(
        step_number=2,
        name="Data Processing",
        notebook_path="02_Data_Processing/Data_Processing.ipynb",
        readme_path="02_Data_Processing/02_Data_Processing_README.md",
        expected_outputs=[
            "output/step_02/docling_output",
            "output/step_02/seed_data.jsonl",
        ],
        requires_gpu=False,
    ),
    NotebookStep(
        step_number=3,
        name="Knowledge Generation",
        notebook_path="03_Knowledge_Generation/Knowledge_Generation.ipynb",
        readme_path="03_Knowledge_Generation/03_Knowledge_Generation_README.md",
        expected_outputs=[
            "output/step_03/extractive_summary",
            "output/step_03/detailed_summary",
        ],
        requires_gpu=True,
        timeout_override=3600,  # May take longer
    ),
    NotebookStep(
        step_number=4,
        name="Knowledge Mixing",
        notebook_path="04_Knowledge_Mixing/Knowledge_Mixing.ipynb",
        readme_path="04_Knowledge_Mixing/04_Knowledge_Mixing_README.md",
        expected_outputs=["output/step_04"],
        requires_gpu=False,
    ),
    NotebookStep(
        step_number=5,
        name="Model Training",
        notebook_path="05_Model_Training/Model_Training.ipynb",
        readme_path="05_Model_Training/05_Model_Training_README.md",
        expected_outputs=["output/fine_tuned_model"],
        requires_gpu=True,
        timeout_override=3600,  # Training may take longer
    ),
    NotebookStep(
        step_number=6,
        name="Evaluation",
        notebook_path="06_Evaluation/Evaluation.ipynb",
        readme_path="06_Evaluation/06_Evaluation_README.md",
        expected_outputs=[],  # Evaluation produces metrics, not files
        requires_gpu=True,
    ),
]


# Pre-configured test profiles
class TestProfiles:
    """Pre-configured test profiles for different scenarios."""

    @staticmethod
    def minimal() -> E2ETestConfig:
        """Minimal configuration for quick CI testing."""
        return E2ETestConfig(
            student_model_name="HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
            teacher_model_name="HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
            max_steps=2,
            max_samples=3,
            max_seq_length=128,
            notebook_timeout=900,  # 15 min
        )

    @staticmethod
    def standard() -> E2ETestConfig:
        """Standard configuration for regular E2E testing."""
        return E2ETestConfig(
            student_model_name="HuggingFaceTB/SmolLM2-360M-Instruct",  # pragma: allowlist secret
            teacher_model_name="HuggingFaceTB/SmolLM2-360M-Instruct",  # pragma: allowlist secret
            max_steps=5,
            max_samples=5,
            max_seq_length=256,
        )

    @staticmethod
    def extended() -> E2ETestConfig:
        """Extended configuration for thorough testing."""
        return E2ETestConfig(
            student_model_name="Qwen/Qwen2.5-0.5B-Instruct",
            teacher_model_name="Qwen/Qwen2.5-0.5B-Instruct",
            max_steps=10,
            max_samples=10,
            max_seq_length=512,
            notebook_timeout=3600,
        )
