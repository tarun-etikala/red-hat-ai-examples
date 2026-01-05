#!/usr/bin/env python3
"""
Submit KFP Pipeline to RHOAI
============================
Compiles and submits a KFP pipeline to RHOAI Data Science Pipelines.

Usage:
    python submit_pipeline.py --pipeline single-notebook --route https://ds-pipeline-dspa.apps.xxx
    python submit_pipeline.py --pipeline full-e2e --route https://ds-pipeline-dspa.apps.xxx
"""

import argparse
import os
import sys
import time

# Check for required packages
try:
    from kfp import Client, compiler
    from kfp.dsl import component, pipeline
except ImportError:
    print("❌ KFP not installed. Install with: pip install kfp")
    sys.exit(1)


def get_kfp_client(route: str, token: str) -> Client:
    """Create a KFP client connected to RHOAI Data Science Pipelines."""
    # RHOAI DSP uses bearer token authentication
    return Client(
        host=route,
        existing_token=token,
        ssl_ca_cert=None,  # Skip SSL verification for now
    )


def compile_single_notebook_pipeline(output_path: str) -> str:
    """Compile the single-notebook test pipeline."""

    @component(
        base_image="quay.io/modh/runtime-images:runtime-cuda-tensorflow-ubi9-python-3.11-2024b-20241111",
        packages_to_install=[
            "papermill",
            "nbformat",
            "nbclient",
            "ipykernel",
            "numpy<2.0",
            "gitpython",
        ],
    )
    def run_notebook_component(
        notebook_path: str,
        notebook_dir: str,
        step_name: str,
        student_model: str,
        teacher_model: str,
        git_url: str,
        git_branch: str,
    ) -> str:
        """Execute a single notebook using Papermill."""
        import os
        import subprocess
        import sys
        import time

        print("=" * 60)
        print(f"🚀 {step_name}")
        print("=" * 60)

        # Set environment
        os.environ["STUDENT_MODEL_NAME"] = student_model
        os.environ["TEACHER_MODEL_NAME"] = teacher_model
        os.environ["E2E_TEST_MODE"] = "true"
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

        # Clone repository
        repo_dir = "/tmp/repo"
        print(f"📥 Cloning {git_url} (branch: {git_branch})...")
        subprocess.run(
            ["git", "clone", "--depth", "1", "-b", git_branch, git_url, repo_dir],
            check=True,
        )

        full_notebook_path = os.path.join(repo_dir, notebook_path)
        full_notebook_dir = os.path.join(repo_dir, notebook_dir)

        # Install dependencies from pyproject.toml
        pyproject = os.path.join(full_notebook_dir, "pyproject.toml")
        if os.path.exists(pyproject):
            print("📦 Installing dependencies...")
            try:
                import tomllib

                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                deps = data.get("project", {}).get("dependencies", [])
                deps = [d for d in deps if not d.lower().startswith("numpy")]
                if deps:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-q"] + deps[:20],
                        check=False,
                    )
            except Exception as e:
                print(f"⚠️ Dependency install issue: {e}")

        # Install kernel
        subprocess.run(
            [
                sys.executable,
                "-m",
                "ipykernel",
                "install",
                "--user",
                "--name",
                "python3",
            ],
            capture_output=True,
        )

        # Execute notebook
        import papermill as pm

        output_nb = f"/tmp/output_{step_name.replace(' ', '_')}.ipynb"
        start = time.time()

        try:
            print(f"🔄 Executing: {notebook_path}")
            pm.execute_notebook(
                full_notebook_path,
                output_nb,
                cwd=full_notebook_dir,
                kernel_name="python3",
                progress_bar=True,
            )
            duration = time.time() - start
            print(f"✅ Completed in {duration:.1f}s")
            return "success"
        except Exception as e:
            duration = time.time() - start
            print(f"❌ Failed after {duration:.1f}s: {e}")
            return f"failure: {e}"

    @pipeline(
        name="single-notebook-e2e-test",
        description="Run a single notebook for E2E testing",
    )
    def single_notebook_pipeline(
        notebook_path: str = "examples/knowledge-tuning/02_Data_Processing/Data_Processing.ipynb",
        notebook_dir: str = "examples/knowledge-tuning/02_Data_Processing",
        step_name: str = "Data Processing",
        student_model: str = "HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
        teacher_model: str = "HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
        git_url: str = "https://github.com/red-hat-data-services/red-hat-ai-examples.git",
        git_branch: str = "main",
    ):
        task = run_notebook_component(
            notebook_path=notebook_path,
            notebook_dir=notebook_dir,
            step_name=step_name,
            student_model=student_model,
            teacher_model=teacher_model,
            git_url=git_url,
            git_branch=git_branch,
        )
        task.set_cpu_limit("4")
        task.set_memory_limit("16G")

    compiler.Compiler().compile(
        pipeline_func=single_notebook_pipeline,
        package_path=output_path,
    )
    return output_path


def compile_full_e2e_pipeline(output_path: str) -> str:
    """Compile the full E2E pipeline with all 6 notebooks."""

    @component(
        base_image="quay.io/modh/runtime-images:runtime-cuda-tensorflow-ubi9-python-3.11-2024b-20241111",
        packages_to_install=[
            "papermill",
            "nbformat",
            "nbclient",
            "ipykernel",
            "numpy<2.0",
        ],
    )
    def run_step(
        step_num: int,
        step_name: str,
        notebook_path: str,
        notebook_dir: str,
        student_model: str,
        teacher_model: str,
        git_url: str,
        git_branch: str,
    ) -> str:
        """Execute a notebook step."""
        import os
        import subprocess
        import sys
        import time

        print(f"{'=' * 60}")
        print(f"📓 Step {step_num}: {step_name}")
        print(f"{'=' * 60}")

        os.environ["STUDENT_MODEL_NAME"] = student_model
        os.environ["TEACHER_MODEL_NAME"] = teacher_model
        os.environ["E2E_TEST_MODE"] = "true"

        repo_dir = "/tmp/repo"
        if not os.path.exists(repo_dir):
            subprocess.run(
                ["git", "clone", "--depth", "1", "-b", git_branch, git_url, repo_dir],
                check=True,
            )

        full_path = os.path.join(repo_dir, notebook_path)
        full_dir = os.path.join(repo_dir, notebook_dir)

        # Install deps
        pyproject = os.path.join(full_dir, "pyproject.toml")
        if os.path.exists(pyproject):
            try:
                import tomllib

                with open(pyproject, "rb") as f:
                    deps = tomllib.load(f).get("project", {}).get("dependencies", [])
                deps = [d for d in deps if not d.lower().startswith("numpy")]
                if deps:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-q"] + deps[:20],
                        check=False,
                    )
            except Exception:
                pass

        subprocess.run(
            [
                sys.executable,
                "-m",
                "ipykernel",
                "install",
                "--user",
                "--name",
                "python3",
            ],
            capture_output=True,
        )

        import papermill as pm

        start = time.time()
        try:
            pm.execute_notebook(
                full_path,
                f"/tmp/step_{step_num}_output.ipynb",
                cwd=full_dir,
                kernel_name="python3",
            )
            print(f"✅ Step {step_num} completed in {time.time() - start:.1f}s")
            return "success"
        except Exception as e:
            print(f"❌ Step {step_num} failed: {e}")
            raise

    @pipeline(
        name="knowledge-tuning-e2e-full",
        description="Full E2E test of knowledge-tuning workflow",
    )
    def full_e2e_pipeline(
        student_model: str = "HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
        teacher_model: str = "HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
        git_url: str = "https://github.com/red-hat-data-services/red-hat-ai-examples.git",
        git_branch: str = "main",
    ):
        notebooks = [
            (
                1,
                "Base Model Evaluation",
                "01_Base_Model_Evaluation",
                "Base_Model_Evaluation.ipynb",
            ),
            (2, "Data Processing", "02_Data_Processing", "Data_Processing.ipynb"),
            (
                3,
                "Knowledge Generation",
                "03_Knowledge_Generation",
                "Knowledge_Generation.ipynb",
            ),
            (4, "Knowledge Mixing", "04_Knowledge_Mixing", "Knowledge_Mixing.ipynb"),
            (5, "Model Training", "05_Model_Training", "Model_Training.ipynb"),
            (6, "Evaluation", "06_Evaluation", "Evaluation.ipynb"),
        ]

        prev = None
        for step_num, name, folder, nb_file in notebooks:
            task = run_step(
                step_num=step_num,
                step_name=name,
                notebook_path=f"examples/knowledge-tuning/{folder}/{nb_file}",
                notebook_dir=f"examples/knowledge-tuning/{folder}",
                student_model=student_model,
                teacher_model=teacher_model,
                git_url=git_url,
                git_branch=git_branch,
            )
            task.set_display_name(f"Step {step_num}: {name}")
            task.set_cpu_limit("4")
            task.set_memory_limit("16G")

            if prev:
                task.after(prev)
            prev = task

    compiler.Compiler().compile(
        pipeline_func=full_e2e_pipeline,
        package_path=output_path,
    )
    return output_path


def submit_pipeline(
    client: Client,
    pipeline_path: str,
    run_name: str,
    params: dict,
    experiment_name: str = "e2e-tests",
) -> str:
    """Submit a compiled pipeline to RHOAI."""
    print(f"📤 Submitting pipeline: {run_name}")

    # Get or create experiment
    try:
        client.get_experiment(experiment_name=experiment_name)
    except Exception:
        client.create_experiment(name=experiment_name)

    # Submit run
    run = client.create_run_from_pipeline_package(
        pipeline_file=pipeline_path,
        run_name=run_name,
        experiment_name=experiment_name,
        arguments=params,
    )

    print(f"✅ Run submitted: {run.run_id}")
    return run.run_id


def wait_for_run(client: Client, run_id: str, timeout_minutes: int = 120) -> str:
    """Wait for a pipeline run to complete."""
    print(f"⏳ Waiting for run {run_id} to complete...")

    start = time.time()
    timeout = timeout_minutes * 60

    while time.time() - start < timeout:
        run = client.get_run(run_id)
        status = run.state

        if status in ["SUCCEEDED"]:
            print("✅ Run completed successfully!")
            return "success"
        elif status in ["FAILED", "ERROR", "SKIPPED"]:
            print(f"❌ Run failed with status: {status}")
            return "failure"

        elapsed = int(time.time() - start)
        print(f"   Status: {status} (elapsed: {elapsed}s)")
        time.sleep(30)

    print(f"❌ Timeout after {timeout_minutes} minutes")
    return "timeout"


def main():
    parser = argparse.ArgumentParser(description="Submit KFP pipeline to RHOAI")
    parser.add_argument(
        "--pipeline",
        choices=["single-notebook", "full-e2e"],
        default="single-notebook",
        help="Pipeline to run",
    )
    parser.add_argument(
        "--route",
        required=True,
        help="RHOAI Data Science Pipelines route URL",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("OPENSHIFT_TOKEN"),
        help="OpenShift token (or set OPENSHIFT_TOKEN env var)",
    )
    parser.add_argument(
        "--compile-only",
        action="store_true",
        help="Only compile, don't submit",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for run to complete",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in minutes when waiting",
    )
    # Pipeline parameters
    parser.add_argument("--notebook-path", help="Notebook path (single-notebook only)")
    parser.add_argument(
        "--notebook-dir", help="Notebook directory (single-notebook only)"
    )
    parser.add_argument("--step-name", default="E2E Test", help="Step name")
    parser.add_argument(
        "--student-model",
        default="HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
        help="Student model",
    )
    parser.add_argument(
        "--teacher-model",
        default="HuggingFaceTB/SmolLM2-135M-Instruct",  # pragma: allowlist secret
        help="Teacher model",
    )
    parser.add_argument(
        "--git-url",
        default="https://github.com/red-hat-data-services/red-hat-ai-examples.git",
        help="Git repository URL",
    )
    parser.add_argument("--git-branch", default="main", help="Git branch")

    args = parser.parse_args()

    # Compile pipeline
    output_path = f"/tmp/{args.pipeline}_pipeline.yaml"
    print(f"🔧 Compiling {args.pipeline} pipeline...")

    if args.pipeline == "single-notebook":
        compile_single_notebook_pipeline(output_path)
    else:
        compile_full_e2e_pipeline(output_path)

    print(f"✅ Compiled: {output_path}")

    if args.compile_only:
        print(f"📄 Pipeline YAML saved to: {output_path}")
        return

    # Submit to RHOAI
    if not args.token:
        print("❌ No token provided. Set --token or OPENSHIFT_TOKEN env var")
        sys.exit(1)

    client = get_kfp_client(args.route, args.token)

    # Build parameters
    run_name = f"e2e-{args.pipeline}-{int(time.time())}"
    params = {
        "student_model": args.student_model,
        "teacher_model": args.teacher_model,
        "git_url": args.git_url,
        "git_branch": args.git_branch,
    }

    if args.pipeline == "single-notebook":
        params["notebook_path"] = (
            args.notebook_path
            or "examples/knowledge-tuning/02_Data_Processing/Data_Processing.ipynb"
        )
        params["notebook_dir"] = (
            args.notebook_dir or "examples/knowledge-tuning/02_Data_Processing"
        )
        params["step_name"] = args.step_name

    run_id = submit_pipeline(client, output_path, run_name, params)

    if args.wait:
        status = wait_for_run(client, run_id, args.timeout)
        sys.exit(0 if status == "success" else 1)


if __name__ == "__main__":
    main()
