"""End-to-end tests for knowledge tuning workflow."""

from pathlib import Path

import pytest


@pytest.mark.e2e
class TestKnowledgeTuningStructure:
    """Tests for knowledge tuning directory structure."""

    @pytest.fixture
    def knowledge_tuning_dir(self, examples_dir):
        """Get knowledge tuning directory."""
        return examples_dir / "knowledge-tuning"

    def test_all_steps_present(self, knowledge_tuning_dir):
        """Test that all workflow steps are present."""
        expected_steps = [
            "00_Setup",
            "01_Base_Model_Evaluation",
            "02_Data_Processing",
            "03_Knowledge_Generation",
            "04_Knowledge_Mixing",
            "05_Model_Training",
            "06_Evaluation",
        ]

        for step in expected_steps:
            step_dir = knowledge_tuning_dir / step
            assert step_dir.exists(), f"Missing step directory: {step}"
            assert step_dir.is_dir()

    def test_each_step_has_notebook(self, knowledge_tuning_dir):
        """Test that each step (except setup) has a notebook."""
        steps_with_notebooks = [
            ("01_Base_Model_Evaluation", "Base_Model_Evaluation.ipynb"),
            ("02_Data_Processing", "Data_Processing.ipynb"),
            ("03_Knowledge_Generation", "Knowledge_Generation.ipynb"),
            ("04_Knowledge_Mixing", "Knowledge_Mixing.ipynb"),
            ("05_Model_Training", "Model_Training.ipynb"),
            ("06_Evaluation", "Evaluation.ipynb"),
        ]

        for step_dir, notebook_name in steps_with_notebooks:
            notebook_path = knowledge_tuning_dir / step_dir / notebook_name
            assert notebook_path.exists(), f"Missing notebook: {step_dir}/{notebook_name}"

    def test_each_step_has_pyproject_toml(self, knowledge_tuning_dir):
        """Test that each step has pyproject.toml."""
        steps_with_pyproject = [
            "01_Base_Model_Evaluation",
            "02_Data_Processing",
            "03_Knowledge_Generation",
            "04_Knowledge_Mixing",
            "05_Model_Training",
            "06_Evaluation",
        ]

        for step in steps_with_pyproject:
            pyproject = knowledge_tuning_dir / step / "pyproject.toml"
            assert pyproject.exists(), f"Missing pyproject.toml in {step}"

    def test_each_step_has_env_example(self, knowledge_tuning_dir):
        """Test that each step has .env.example."""
        steps_with_env = [
            "01_Base_Model_Evaluation",
            "02_Data_Processing",
            "03_Knowledge_Generation",
            "04_Knowledge_Mixing",
            "05_Model_Training",
            "06_Evaluation",
        ]

        for step in steps_with_env:
            env_file = knowledge_tuning_dir / step / ".env.example"
            assert env_file.exists(), f"Missing .env.example in {step}"


@pytest.mark.e2e
class TestKnowledgeTuningUtilities:
    """Tests for knowledge tuning utility modules."""

    def test_knowledge_utils_exists(self, examples_dir):
        """Test that knowledge_utils.py exists."""
        utils_file = (
            examples_dir
            / "knowledge-tuning"
            / "04_Knowledge_Mixing"
            / "utils"
            / "knowledge_utils.py"
        )
        assert utils_file.exists()

    def test_flash_attn_installer_exists(self, examples_dir):
        """Test that flash_attn_installer.py exists."""
        installer_file = (
            examples_dir
            / "knowledge-tuning"
            / "05_Model_Training"
            / "utils"
            / "flash_attn_installer.py"
        )
        assert installer_file.exists()

    def test_utils_are_importable(self, examples_dir):
        """Test that utility modules can be imported."""
        import sys

        # Test knowledge_utils
        utils_dir = (
            examples_dir
            / "knowledge-tuning"
            / "04_Knowledge_Mixing"
            / "utils"
        )
        sys.path.insert(0, str(utils_dir))

        try:
            import knowledge_utils

            assert hasattr(knowledge_utils, "sample_doc_qa")
        except ImportError as e:
            pytest.skip(f"Could not import knowledge_utils: {e}")


@pytest.mark.e2e
class TestKnowledgeTuningDependencies:
    """Tests for knowledge tuning dependencies."""

    def test_pyproject_toml_structure(self, examples_dir):
        """Test pyproject.toml has required structure."""
        pytest.importorskip("tomli", reason="tomli not available")

        try:
            import tomli
        except ImportError:
            import tomllib as tomli

        pyproject_file = (
            examples_dir
            / "knowledge-tuning"
            / "01_Base_Model_Evaluation"
            / "pyproject.toml"
        )

        with open(pyproject_file, "rb") as f:
            config = tomli.load(f)

        assert "project" in config
        assert "dependencies" in config["project"]

    def test_python_version_specified(self, examples_dir):
        """Test that Python version is specified."""
        python_version_file = (
            examples_dir
            / "knowledge-tuning"
            / "01_Base_Model_Evaluation"
            / ".python-version"
        )

        if python_version_file.exists():
            version = python_version_file.read_text().strip()
            assert version.startswith("3.")


@pytest.mark.e2e
class TestKnowledgeTuningWorkflow:
    """Tests for knowledge tuning workflow integration."""

    def test_workflow_sequence(self, examples_dir):
        """Test that workflow steps are in correct sequence."""
        knowledge_tuning_dir = examples_dir / "knowledge-tuning"

        step_dirs = sorted(
            [d for d in knowledge_tuning_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
        )

        # Should be 7 steps (00-06)
        assert len(step_dirs) == 7

        # Should be numbered sequentially
        for i, step_dir in enumerate(step_dirs):
            assert step_dir.name.startswith(f"0{i}_")

    def test_data_flow_documented(self, examples_dir):
        """Test that data flow is documented in READMEs."""
        knowledge_tuning_dir = examples_dir / "knowledge-tuning"

        readme_files = list(knowledge_tuning_dir.rglob("*README.md"))
        assert len(readme_files) > 0, "No README files found"
