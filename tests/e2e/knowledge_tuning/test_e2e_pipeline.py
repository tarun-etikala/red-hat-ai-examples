"""
E2E Pipeline Tests for Knowledge-Tuning Workflow on RHOAI.

This module provides comprehensive E2E testing for the knowledge-tuning
workflow using Papermill to execute notebooks in sequence.

Test Modes:
-----------
1. Full Pipeline: Executes all 6 notebooks in sequence
2. Individual Steps: Tests each notebook independently
3. Partial Pipeline: Tests subsets of the workflow

Usage:
------
# Run with minimal profile (fastest)
pytest tests/e2e/knowledge_tuning/ -v --e2e-profile=minimal

# Run with standard profile
pytest tests/e2e/knowledge_tuning/ -v --e2e-profile=standard

# Skip specific steps
pytest tests/e2e/knowledge_tuning/ -v --skip-steps=1,6

# Keep outputs for debugging
pytest tests/e2e/knowledge_tuning/ -v --keep-outputs

# Use custom model
pytest tests/e2e/knowledge_tuning/ -v --student-model="Qwen/Qwen2.5-0.5B-Instruct"
"""

import json
from datetime import datetime

import pytest

from .config import KNOWLEDGE_TUNING_STEPS


class TestKnowledgeTuningE2EPipeline:
    """
    E2E tests for the complete knowledge-tuning workflow.

    This test class executes notebooks sequentially, validating:
    - Each notebook executes without errors
    - Expected output files/directories are created
    - The pipeline can run end-to-end
    """

    @pytest.mark.e2e
    @pytest.mark.rhoai
    @pytest.mark.slow
    def test_full_pipeline_execution(
        self,
        knowledge_tuning_path,
        e2e_workspace,
        notebook_executor,
        output_validator,
        workflow_steps,
        execution_results,
        e2e_config,
    ):
        """
        Execute the complete knowledge-tuning pipeline.

        This test runs all notebooks in sequence and validates
        that each step completes successfully.
        """
        print(f"\n{'=' * 60}")
        print("KNOWLEDGE-TUNING E2E PIPELINE TEST")
        print(f"{'=' * 60}")
        print(f"Profile: {e2e_config.student_model_name}")
        print(f"Workspace: {e2e_workspace}")
        print(f"Steps to execute: {len(workflow_steps)}")
        print(f"{'=' * 60}\n")

        failed_steps = []
        passed_steps = []

        for step in workflow_steps:
            print(f"\n{'─' * 50}")
            print(f"Executing: {step.display_name}")
            print(f"{'─' * 50}")

            notebook_path = knowledge_tuning_path / step.notebook_path
            output_notebook = (
                e2e_workspace
                / f"executed_{step.step_number:02d}_{step.name.replace(' ', '_')}.ipynb"
            )

            # Execute the notebook
            start_time = datetime.now()
            result = notebook_executor(
                notebook_path=notebook_path,
                output_path=output_notebook,
                timeout=step.timeout_override or e2e_config.notebook_timeout,
            )
            duration = (datetime.now() - start_time).total_seconds()

            # Store result for later validation
            execution_results[step.step_number] = {
                "step": step,
                "result": result,
                "duration": duration,
            }

            if result["success"]:
                print(f"✅ {step.display_name} completed in {duration:.1f}s")
                passed_steps.append(step)

                # Validate expected outputs
                if step.expected_outputs:
                    validation = output_validator.get_validation_report(
                        step.expected_outputs
                    )
                    if validation["all_passed"]:
                        print("   ✅ All expected outputs created")
                    else:
                        print(f"   ⚠️ Missing outputs: {validation['failed']}")
            else:
                print(f"❌ {step.display_name} FAILED after {duration:.1f}s")
                print(f"   Error: {result['error']}")
                if result.get("ename"):
                    print(f"   Exception: {result['ename']}: {result['evalue']}")
                failed_steps.append(step)

                # For debugging, don't stop on first failure
                # Continue to see which other steps might fail

        # Print summary
        print(f"\n{'=' * 60}")
        print("PIPELINE EXECUTION SUMMARY")
        print(f"{'=' * 60}")
        print(f"Total steps: {len(workflow_steps)}")
        print(f"Passed: {len(passed_steps)}")
        print(f"Failed: {len(failed_steps)}")

        if failed_steps:
            print("\nFailed steps:")
            for step in failed_steps:
                print(f"  - {step.display_name}")

        # Assert all steps passed
        assert len(failed_steps) == 0, (
            f"Pipeline failed: {len(failed_steps)} step(s) failed - "
            f"{[s.display_name for s in failed_steps]}"
        )


class TestIndividualNotebookExecution:
    """
    Tests for individual notebook execution.

    These tests can be run independently to verify specific notebooks
    without running the full pipeline.
    """

    @pytest.mark.e2e
    @pytest.mark.parametrize(
        "step_number",
        [1, 2, 3, 4, 5, 6],
        ids=[
            "step01_base_model_evaluation",
            "step02_data_processing",
            "step03_knowledge_generation",
            "step04_knowledge_mixing",
            "step05_model_training",
            "step06_evaluation",
        ],
    )
    def test_notebook_execution(
        self,
        step_number,
        knowledge_tuning_path,
        e2e_workspace,
        notebook_executor,
        output_validator,
        e2e_config,
        request,
    ):
        """
        Test individual notebook execution.

        Each notebook is tested independently. Note that some notebooks
        depend on outputs from previous steps, so they may fail if run
        in isolation without proper setup.
        """
        # Find the step configuration
        step = next(
            (s for s in KNOWLEDGE_TUNING_STEPS if s.step_number == step_number),
            None,
        )
        if step is None:
            pytest.skip(f"Step {step_number} not found in configuration")

        # Check if step should be skipped based on command line options
        skip_steps_str = request.config.getoption("--skip-steps")
        if skip_steps_str:
            skip_steps = {int(s.strip()) for s in skip_steps_str.split(",")}
            if step_number in skip_steps:
                pytest.skip(f"Step {step_number} skipped via --skip-steps")

        notebook_path = knowledge_tuning_path / step.notebook_path
        assert notebook_path.exists(), f"Notebook not found: {notebook_path}"

        output_notebook = (
            e2e_workspace
            / f"individual_{step.step_number:02d}_{step.name.replace(' ', '_')}.ipynb"
        )

        # Execute notebook
        result = notebook_executor(
            notebook_path=notebook_path,
            output_path=output_notebook,
            timeout=step.timeout_override or e2e_config.notebook_timeout,
        )

        # Validate execution success
        assert result["success"], (
            f"Notebook execution failed for {step.display_name}:\n"
            f"Error: {result['error']}\n"
            f"Cell: {result.get('cell_index')}\n"
            f"Exception: {result.get('ename')}: {result.get('evalue')}"
        )

        # Validate output notebook was created
        assert output_notebook.exists(), (
            f"Output notebook was not created: {output_notebook}"
        )


class TestNotebookOutputValidation:
    """
    Tests for validating notebook outputs after execution.

    These tests check that expected files and directories are created
    after notebook execution.
    """

    @pytest.mark.e2e
    def test_step02_creates_seed_data(self, knowledge_tuning_path, output_validator):
        """Verify Data Processing creates seed data file."""
        # This test assumes step 2 has been run
        expected_file = "output/step_02/seed_data.jsonl"

        if not output_validator.file_exists(expected_file):
            pytest.skip("Step 02 outputs not found - run full pipeline first")

        assert output_validator.file_has_content(expected_file), (
            f"Seed data file is empty: {expected_file}"
        )

    @pytest.mark.e2e
    def test_step03_creates_knowledge_data(
        self, knowledge_tuning_path, output_validator
    ):
        """Verify Knowledge Generation creates output directories."""
        expected_dirs = [
            "output/step_03/extractive_summary",
            "output/step_03/detailed_summary",
        ]

        for expected_dir in expected_dirs:
            if not output_validator.dir_exists(expected_dir):
                pytest.skip(
                    f"Step 03 outputs not found ({expected_dir}) - run full pipeline first"
                )

    @pytest.mark.e2e
    def test_step04_creates_training_data(
        self, knowledge_tuning_path, output_validator
    ):
        """Verify Knowledge Mixing creates training data."""
        expected_dir = "output/step_04"

        if not output_validator.dir_exists(expected_dir):
            pytest.skip("Step 04 outputs not found - run full pipeline first")

        # Check that training data files were created
        step_04_path = knowledge_tuning_path / expected_dir
        jsonl_files = list(step_04_path.glob("*.jsonl"))

        assert len(jsonl_files) > 0, f"No training data files found in {expected_dir}"

    @pytest.mark.e2e
    @pytest.mark.gpu
    def test_step05_creates_fine_tuned_model(
        self, knowledge_tuning_path, output_validator
    ):
        """Verify Model Training creates fine-tuned model."""
        expected_dir = "output/fine_tuned_model"

        if not output_validator.dir_exists(expected_dir):
            pytest.skip("Step 05 outputs not found - run full pipeline first")

        # Check for model files
        fine_tuned_path = knowledge_tuning_path / expected_dir
        # Look for model config or safetensors files
        model_files = list(fine_tuned_path.rglob("config.json")) + list(
            fine_tuned_path.rglob("*.safetensors")
        )

        assert len(model_files) > 0, f"No model files found in {expected_dir}"


class TestPipelineResilience:
    """
    Tests for pipeline resilience and error handling.
    """

    @pytest.mark.e2e
    def test_notebook_has_no_stored_errors(self, knowledge_tuning_path, workflow_steps):
        """Verify source notebooks don't contain execution errors."""
        import nbformat

        for step in workflow_steps:
            notebook_path = knowledge_tuning_path / step.notebook_path
            nb = nbformat.read(str(notebook_path), as_version=4)

            for i, cell in enumerate(nb.cells):
                if cell.cell_type == "code" and hasattr(cell, "outputs"):
                    for output in cell.outputs:
                        if output.get("output_type") == "error":
                            pytest.fail(
                                f"Notebook {step.notebook_path} has stored error "
                                f"in cell {i}: {output.get('ename')}"
                            )

    @pytest.mark.e2e
    def test_all_notebooks_are_readable(self, knowledge_tuning_path, workflow_steps):
        """Verify all workflow notebooks can be parsed."""
        import nbformat

        for step in workflow_steps:
            notebook_path = knowledge_tuning_path / step.notebook_path
            try:
                nb = nbformat.read(str(notebook_path), as_version=4)
                assert len(nb.cells) > 0, f"{step.notebook_path} has no cells"
            except Exception as e:
                pytest.fail(f"Failed to read {step.notebook_path}: {e}")


class TestE2EReporting:
    """
    Generate detailed reports for E2E test runs.
    """

    @pytest.mark.e2e
    def test_generate_execution_report(
        self, e2e_workspace, execution_results, e2e_config
    ):
        """Generate a JSON report of execution results."""
        if not execution_results:
            pytest.skip("No execution results available - run pipeline first")

        report = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "student_model": e2e_config.student_model_name,
                "teacher_model": e2e_config.teacher_model_name,
                "max_steps": e2e_config.max_steps,
                "max_samples": e2e_config.max_samples,
            },
            "steps": [],
            "summary": {
                "total": len(execution_results),
                "passed": 0,
                "failed": 0,
                "total_duration": 0,
            },
        }

        for step_num, data in sorted(execution_results.items()):
            step_report = {
                "step_number": step_num,
                "name": data["step"].name,
                "success": data["result"]["success"],
                "duration_seconds": data["duration"],
                "error": data["result"].get("error"),
            }
            report["steps"].append(step_report)
            report["summary"]["total_duration"] += data["duration"]

            if data["result"]["success"]:
                report["summary"]["passed"] += 1
            else:
                report["summary"]["failed"] += 1

        # Write report
        report_path = e2e_workspace / "e2e_execution_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📊 Execution report saved to: {report_path}")

        # Also print summary to stdout
        print(f"\n{'=' * 50}")
        print("E2E EXECUTION REPORT")
        print(f"{'=' * 50}")
        print(f"Total Steps: {report['summary']['total']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Total Duration: {report['summary']['total_duration']:.1f}s")
        print(f"{'=' * 50}")
