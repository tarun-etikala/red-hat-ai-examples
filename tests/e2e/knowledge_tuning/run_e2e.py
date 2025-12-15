#!/usr/bin/env python3
"""
Standalone E2E test runner for knowledge-tuning workflow.

This script can be run directly on a RHOAI workbench to execute
the full E2E pipeline without pytest overhead.

Usage:
    python run_e2e.py                      # Run with defaults
    python run_e2e.py --profile minimal    # Use minimal profile
    python run_e2e.py --steps 1,2,3        # Run specific steps only
    python run_e2e.py --dry-run            # Show what would be executed
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def setup_paths():
    """Set up paths and ensure we can import our modules."""
    script_dir = Path(__file__).parent.resolve()
    repo_root = script_dir.parent.parent.parent

    # Add to path for imports
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(repo_root))

    return repo_root, script_dir


def check_dependencies():
    """Check that required dependencies are installed."""
    missing = []

    try:
        import papermill  # noqa: F401
    except ImportError:
        missing.append("papermill")

    try:
        import nbformat  # noqa: F401
    except ImportError:
        missing.append("nbformat")

    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
        sys.exit(1)

    print("✅ All dependencies available")


def run_notebook(notebook_path: Path, output_path: Path, env_vars: dict, timeout: int):
    """Execute a single notebook using papermill."""
    import papermill as pm

    try:
        pm.execute_notebook(
            str(notebook_path),
            str(output_path),
            parameters=env_vars,
            cwd=str(notebook_path.parent),
            kernel_name="python3",
            progress_bar=True,
        )
        return {"success": True, "error": None}
    except pm.PapermillExecutionError as e:
        return {
            "success": False,
            "error": str(e),
            "cell_index": getattr(e, "cell_index", None),
            "ename": getattr(e, "ename", None),
            "evalue": getattr(e, "evalue", None),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(
        description="Run E2E tests for knowledge-tuning workflow"
    )
    parser.add_argument(
        "--profile",
        choices=["minimal", "standard", "extended"],
        default="minimal",
        help="Test profile to use",
    )
    parser.add_argument(
        "--steps",
        type=str,
        default="",
        help="Comma-separated list of steps to run (e.g., '1,2,3'). Empty = all",
    )
    parser.add_argument(
        "--skip-steps",
        type=str,
        default="",
        help="Comma-separated list of steps to skip",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be executed without running",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for executed notebooks",
    )
    parser.add_argument(
        "--student-model",
        type=str,
        default=None,
        help="Override student model name",
    )
    parser.add_argument(
        "--teacher-model",
        type=str,
        default=None,
        help="Override teacher model name",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("KNOWLEDGE-TUNING E2E TEST RUNNER")
    print("=" * 60)

    # Setup
    repo_root, script_dir = setup_paths()
    check_dependencies()

    # Import config
    from config import KNOWLEDGE_TUNING_STEPS, TestProfiles

    # Get configuration
    profiles = {
        "minimal": TestProfiles.minimal,
        "standard": TestProfiles.standard,
        "extended": TestProfiles.extended,
    }
    config = profiles[args.profile]()

    # Apply overrides
    if args.student_model:
        config.student_model_name = args.student_model
    if args.teacher_model:
        config.teacher_model_name = args.teacher_model

    print("\n📋 Configuration:")
    print(f"   Profile: {args.profile}")
    print(f"   Student Model: {config.student_model_name}")
    print(f"   Teacher Model: {config.teacher_model_name}")
    print(f"   Max Steps: {config.max_steps}")
    print(f"   Max Samples: {config.max_samples}")

    # Determine which steps to run
    knowledge_tuning_path = repo_root / "examples" / "knowledge-tuning"

    if args.steps:
        run_steps = {int(s.strip()) for s in args.steps.split(",")}
    else:
        run_steps = {s.step_number for s in KNOWLEDGE_TUNING_STEPS}

    if args.skip_steps:
        skip_steps = {int(s.strip()) for s in args.skip_steps.split(",")}
        run_steps = run_steps - skip_steps

    steps_to_run = [s for s in KNOWLEDGE_TUNING_STEPS if s.step_number in run_steps]

    print(f"\n📝 Steps to execute: {[s.step_number for s in steps_to_run]}")

    # Output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = knowledge_tuning_path / "e2e_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Output directory: {output_dir}")

    if args.dry_run:
        print("\n🔍 DRY RUN - Would execute:")
        for step in steps_to_run:
            notebook_path = knowledge_tuning_path / step.notebook_path
            print(f"   [{step.step_number}] {step.name}")
            print(f"       {notebook_path}")
        print("\n✅ Dry run complete. Remove --dry-run to execute.")
        return

    # Set environment variables
    env_vars = config.get_env_vars()
    for key, value in env_vars.items():
        os.environ[key] = value

    # Execute notebooks
    results = []
    print(f"\n{'=' * 60}")
    print("EXECUTING PIPELINE")
    print(f"{'=' * 60}")

    for step in steps_to_run:
        print(f"\n{'─' * 50}")
        print(f"Step {step.step_number}: {step.name}")
        print(f"{'─' * 50}")

        notebook_path = knowledge_tuning_path / step.notebook_path
        output_notebook = (
            output_dir
            / f"executed_{step.step_number:02d}_{step.name.replace(' ', '_')}.ipynb"
        )

        start_time = datetime.now()
        result = run_notebook(
            notebook_path=notebook_path,
            output_path=output_notebook,
            env_vars=env_vars,
            timeout=step.timeout_override or config.notebook_timeout,
        )
        duration = (datetime.now() - start_time).total_seconds()

        result["step_number"] = step.step_number
        result["step_name"] = step.name
        result["duration"] = duration
        results.append(result)

        if result["success"]:
            print(f"✅ Completed in {duration:.1f}s")
        else:
            print(f"❌ Failed after {duration:.1f}s")
            print(f"   Error: {result['error']}")

    # Summary
    passed = sum(1 for r in results if r["success"])
    failed = len(results) - passed
    total_duration = sum(r["duration"] for r in results)

    print(f"\n{'=' * 60}")
    print("EXECUTION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total steps: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total duration: {total_duration:.1f}s")

    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "profile": args.profile,
        "config": {
            "student_model": config.student_model_name,
            "teacher_model": config.teacher_model_name,
        },
        "results": results,
        "summary": {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "duration": total_duration,
        },
    }

    report_path = output_dir / "e2e_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📊 Report saved: {report_path}")

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
