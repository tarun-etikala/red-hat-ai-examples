"""
KFP Pipeline: Knowledge-Tuning E2E Tests
========================================
Runs the complete knowledge-tuning workflow as a KFP pipeline on RHOAI.
"""

from kfp import dsl
from kfp.dsl import pipeline

# Notebook configurations
NOTEBOOKS = [
    {
        "step": 1,
        "name": "Base Model Evaluation",
        "path": "examples/knowledge-tuning/01_Base_Model_Evaluation/Base_Model_Evaluation.ipynb",
        "dir": "examples/knowledge-tuning/01_Base_Model_Evaluation",
    },
    {
        "step": 2,
        "name": "Data Processing",
        "path": "examples/knowledge-tuning/02_Data_Processing/Data_Processing.ipynb",
        "dir": "examples/knowledge-tuning/02_Data_Processing",
    },
    {
        "step": 3,
        "name": "Knowledge Generation",
        "path": "examples/knowledge-tuning/03_Knowledge_Generation/Knowledge_Generation.ipynb",
        "dir": "examples/knowledge-tuning/03_Knowledge_Generation",
    },
    {
        "step": 4,
        "name": "Knowledge Mixing",
        "path": "examples/knowledge-tuning/04_Knowledge_Mixing/Knowledge_Mixing.ipynb",
        "dir": "examples/knowledge-tuning/04_Knowledge_Mixing",
    },
    {
        "step": 5,
        "name": "Model Training",
        "path": "examples/knowledge-tuning/05_Model_Training/Model_Training.ipynb",
        "dir": "examples/knowledge-tuning/05_Model_Training",
    },
    {
        "step": 6,
        "name": "Evaluation",
        "path": "examples/knowledge-tuning/06_Evaluation/Evaluation.ipynb",
        "dir": "examples/knowledge-tuning/06_Evaluation",
    },
]


@pipeline(
    name="knowledge-tuning-e2e-test",
    description="E2E test pipeline for knowledge-tuning workflow",
)
def knowledge_tuning_e2e_pipeline(
    student_model: str = "HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
    teacher_model: str = "HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
    git_url: str = "https://github.com/red-hat-data-services/red-hat-ai-examples.git",
    git_branch: str = "main",
    skip_steps: str = "",
):
    """
    Run all 6 knowledge-tuning notebooks in sequence.

    Args:
        student_model: Student model for fine-tuning
        teacher_model: Teacher model for knowledge generation
        git_url: Git repository URL
        git_branch: Git branch to test
        skip_steps: Comma-separated step numbers to skip (e.g., "1,5,6")
    """
    from tests.e2e.knowledge_tuning.kfp.components import report_results, run_notebook

    # Parse skip_steps
    results = []
    previous_task = None

    for nb in NOTEBOOKS:
        step_num = str(nb["step"])

        # Create the notebook task
        with dsl.If(
            dsl.PipelineTask.from_pipeline_param(skip_steps).not_contains(step_num),
            name=f"check-skip-step-{step_num}",
        ):
            task = run_notebook(
                notebook_path=nb["path"],
                notebook_dir=nb["dir"],
                step_name=f"Step {nb['step']}: {nb['name']}",
                student_model=student_model,
                teacher_model=teacher_model,
            )

            # Set task name and resources
            task.set_display_name(f"Step {nb['step']}: {nb['name']}")
            task.set_cpu_limit("4")
            task.set_memory_limit("16Gi")

            # Add GPU for steps that need it
            if nb["step"] in [1, 3, 5, 6]:
                task.add_node_selector_constraint(
                    "nvidia.com/gpu.present", "true"
                ).set_accelerator_type("nvidia.com/gpu").set_accelerator_limit(1)

            # Set environment variables
            task.set_env_variable("GIT_URL", git_url)
            task.set_env_variable("GIT_BRANCH", git_branch)

            # Chain tasks sequentially
            if previous_task:
                task.after(previous_task)

            previous_task = task
            results.append(task.output)

    # Generate final report
    report_task = report_results(step_results=results)
    report_task.set_display_name("Generate Report")
    if previous_task:
        report_task.after(previous_task)


# Simpler single-notebook pipeline for testing
@pipeline(
    name="single-notebook-test",
    description="Run a single notebook for testing",
)
def single_notebook_pipeline(
    notebook_path: str = "examples/knowledge-tuning/02_Data_Processing/Data_Processing.ipynb",
    notebook_dir: str = "examples/knowledge-tuning/02_Data_Processing",
    step_name: str = "Data Processing Test",
    student_model: str = "HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
    teacher_model: str = "HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
    git_url: str = "https://github.com/red-hat-data-services/red-hat-ai-examples.git",
    git_branch: str = "main",
):
    """
    Run a single notebook - useful for testing individual steps.

    Args:
        notebook_path: Path to notebook file
        notebook_dir: Directory containing the notebook
        step_name: Display name for the step
        student_model: Student model name
        teacher_model: Teacher model name
        git_url: Git repository URL
        git_branch: Git branch to test
    """
    from tests.e2e.knowledge_tuning.kfp.components import run_notebook

    task = run_notebook(
        notebook_path=notebook_path,
        notebook_dir=notebook_dir,
        step_name=step_name,
        student_model=student_model,
        teacher_model=teacher_model,
    )

    task.set_display_name(step_name)
    task.set_cpu_limit("4")
    task.set_memory_limit("16Gi")
    task.set_env_variable("GIT_URL", git_url)
    task.set_env_variable("GIT_BRANCH", git_branch)


if __name__ == "__main__":
    # Compile pipelines when run directly
    from kfp import compiler

    print("Compiling pipelines...")

    compiler.Compiler().compile(
        pipeline_func=knowledge_tuning_e2e_pipeline,
        package_path="knowledge_tuning_e2e_pipeline.yaml",
    )
    print("✅ Compiled: knowledge_tuning_e2e_pipeline.yaml")

    compiler.Compiler().compile(
        pipeline_func=single_notebook_pipeline,
        package_path="single_notebook_pipeline.yaml",
    )
    print("✅ Compiled: single_notebook_pipeline.yaml")
