"""
KFP Components for E2E Testing
==============================
Reusable components for running notebooks in RHOAI Data Science Pipelines.
"""

from kfp import dsl
from kfp.dsl import Artifact, Output


@dsl.component(
    base_image="quay.io/modh/runtime-images:runtime-cuda-tensorflow-ubi9-python-3.11-2024b-20241111",
    packages_to_install=["papermill", "nbformat", "nbclient", "ipykernel", "numpy<2.0"],
)
def run_notebook(
    notebook_path: str,
    notebook_dir: str,
    step_name: str,
    student_model: str,
    teacher_model: str,
    output_notebook: Output[Artifact],
    execution_log: Output[Artifact],
) -> str:
    """
    Execute a Jupyter notebook using Papermill.

    Args:
        notebook_path: Path to the notebook file (relative to repo root)
        notebook_dir: Directory containing the notebook
        step_name: Human-readable step name for logging
        student_model: Student model name for environment
        teacher_model: Teacher model name for environment
        output_notebook: Output artifact for executed notebook
        execution_log: Output artifact for execution log

    Returns:
        Status string: "success" or "failure"
    """
    import os
    import subprocess
    import sys
    import time

    print("=" * 60)
    print(f"🚀 Running: {step_name}")
    print("=" * 60)
    print(f"Notebook: {notebook_path}")
    print(f"Directory: {notebook_dir}")
    print(f"Student Model: {student_model}")
    print(f"Teacher Model: {teacher_model}")
    print()

    # Set environment variables
    os.environ["STUDENT_MODEL_NAME"] = student_model
    os.environ["TEACHER_MODEL_NAME"] = teacher_model
    os.environ["E2E_TEST_MODE"] = "true"
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

    # Clone repository if not present
    repo_dir = "/tmp/repo"
    if not os.path.exists(repo_dir):
        print("📥 Cloning repository...")
        git_url = os.environ.get(
            "GIT_URL",
            "https://github.com/red-hat-data-services/red-hat-ai-examples.git",
        )
        git_branch = os.environ.get("GIT_BRANCH", "main")
        subprocess.run(
            ["git", "clone", "--depth", "1", "-b", git_branch, git_url, repo_dir],
            check=True,
        )
        print("✅ Repository cloned")

    full_notebook_path = os.path.join(repo_dir, notebook_path)
    full_notebook_dir = os.path.join(repo_dir, notebook_dir)

    # Install notebook-specific dependencies
    pyproject_path = os.path.join(full_notebook_dir, "pyproject.toml")
    if os.path.exists(pyproject_path):
        print("📦 Installing notebook dependencies...")
        try:
            import tomllib

            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            deps = data.get("project", {}).get("dependencies", [])
            # Filter out numpy (already pinned)
            deps = [d for d in deps if not d.lower().startswith("numpy")]
            if deps:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q"] + deps,
                    check=False,
                )
                print(f"✅ Installed: {len(deps)} dependencies")
        except Exception as e:
            print(f"⚠️ Could not install dependencies: {e}")

    # Install Jupyter kernel
    subprocess.run(
        [sys.executable, "-m", "ipykernel", "install", "--user", "--name", "python3"],
        check=False,
        capture_output=True,
    )

    # Run notebook with papermill
    import papermill as pm

    start_time = time.time()
    log_content = []

    try:
        print("🔄 Executing notebook...")
        log_content.append(f"Starting execution: {step_name}")
        log_content.append(f"Notebook: {notebook_path}")

        pm.execute_notebook(
            full_notebook_path,
            output_notebook.path,
            cwd=full_notebook_dir,
            kernel_name="python3",
            progress_bar=True,
        )

        duration = time.time() - start_time
        log_content.append(f"Duration: {duration:.1f}s")
        log_content.append("Status: SUCCESS")

        print(f"✅ {step_name} completed in {duration:.1f}s")

        # Write log
        with open(execution_log.path, "w") as f:
            f.write("\n".join(log_content))

        return "success"

    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        log_content.append(f"Duration: {duration:.1f}s")
        log_content.append("Status: FAILURE")
        log_content.append(f"Error: {error_msg}")

        print(f"❌ {step_name} failed after {duration:.1f}s")
        print(f"Error: {error_msg}")

        # Write log
        with open(execution_log.path, "w") as f:
            f.write("\n".join(log_content))

        # Still save the output notebook if it exists
        if not os.path.exists(output_notebook.path):
            with open(output_notebook.path, "w") as f:
                f.write("{}")

        raise


@dsl.component(
    base_image="python:3.11-slim",
)
def report_results(
    step_results: list,
    report: Output[Artifact],
) -> str:
    """
    Generate a summary report of all step results.

    Args:
        step_results: List of result strings from each step
        report: Output artifact for the report

    Returns:
        Overall status: "success" or "failure"
    """
    import json

    print("=" * 60)
    print("📊 E2E Test Report")
    print("=" * 60)

    passed = sum(1 for r in step_results if r == "success")
    failed = len(step_results) - passed

    report_data = {
        "total_steps": len(step_results),
        "passed": passed,
        "failed": failed,
        "results": step_results,
        "overall_status": "success" if failed == 0 else "failure",
    }

    print(f"Total Steps: {len(step_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Overall: {report_data['overall_status'].upper()}")

    with open(report.path, "w") as f:
        json.dump(report_data, f, indent=2)

    return report_data["overall_status"]
