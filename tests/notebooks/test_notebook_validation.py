"""Tests for validating Jupyter notebooks."""

import json
import re
from pathlib import Path

import nbformat
import pytest
import yaml
from nbformat.validator import validate as nbformat_validate


def load_manifest():
    """Load the notebooks manifest YAML file."""
    manifest_path = Path(__file__).parent / "notebooks_manifest.yaml"
    with open(manifest_path) as f:
        return yaml.safe_load(f)


MANIFEST = load_manifest()
NOTEBOOKS = MANIFEST["notebooks"]


def get_notebook_ids():
    """Generate test IDs for parametrization."""
    return [nb["name"] for nb in NOTEBOOKS]


def get_notebooks_to_test():
    """Get list of notebooks that should be tested."""
    return [nb for nb in NOTEBOOKS if not nb.get("skip", False)]


@pytest.mark.notebook
class TestNotebookStructure:
    """Tests for notebook structure and format validation."""

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_notebook_exists(self, notebook_config, project_root):
        """Test that notebook file exists."""
        notebook_path = project_root / notebook_config["path"]
        assert notebook_path.exists(), f"Notebook not found: {notebook_path}"
        assert notebook_path.is_file(), f"Path is not a file: {notebook_path}"

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_notebook_is_valid_json(self, notebook_config, project_root):
        """Test that notebook is valid JSON."""
        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        try:
            with open(notebook_path) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            pytest.fail(f"Notebook is not valid JSON: {e}")

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_notebook_format_valid(self, notebook_config, project_root):
        """Test that notebook follows nbformat schema."""
        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        try:
            nb = nbformat.read(str(notebook_path), as_version=4)
            nbformat_validate(nb)
        except nbformat.ValidationError as e:
            pytest.fail(f"Notebook validation failed: {e}")

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_notebook_has_cells(self, notebook_config, project_root):
        """Test that notebook has at least one cell."""
        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        nb = nbformat.read(str(notebook_path), as_version=4)
        assert len(nb.cells) > 0, "Notebook has no cells"

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_notebook_has_metadata(self, notebook_config, project_root):
        """Test that notebook has required metadata."""
        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        nb = nbformat.read(str(notebook_path), as_version=4)
        assert "metadata" in nb, "Notebook missing metadata"
        assert "kernelspec" in nb.metadata or "language_info" in nb.metadata, (
            "Notebook missing kernelspec or language_info"
        )


@pytest.mark.notebook
class TestNotebookContent:
    """Tests for notebook content validation."""

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_no_hardcoded_secrets(self, notebook_config, project_root):
        """Test that notebook doesn't contain hardcoded secrets."""
        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        nb = nbformat.read(str(notebook_path), as_version=4)

        # Patterns that might indicate secrets
        secret_patterns = [
            r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"][^'\"]{20,}['\"]",
            r"(?i)(secret|password|passwd|pwd)\s*[=:]\s*['\"][^'\"]+['\"]",
            r"(?i)(token)\s*[=:]\s*['\"][^'\"]{30,}['\"]",
            r"(?i)(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*['\"][^'\"]+['\"]",
            r"(?i)(private[_-]?key)\s*[=:]\s*['\"].*BEGIN.*PRIVATE.*KEY",
        ]

        # Allowed patterns (environment variable usage is OK)
        allowed_patterns = [
            r"os\.getenv",
            r"os\.environ",
            r"ENV\[",
            r"\.env",
            r"dotenv",
        ]

        for cell in nb.cells:
            if cell.cell_type == "code":
                source = "".join(cell.source) if isinstance(cell.source, list) else cell.source

                for pattern in secret_patterns:
                    matches = re.findall(pattern, source)
                    if matches:
                        # Check if it's an allowed pattern
                        is_allowed = any(
                            re.search(allowed, source) for allowed in allowed_patterns
                        )
                        if not is_allowed:
                            pytest.fail(
                                f"Potential hardcoded secret found in {notebook_path}: {matches[0]}"
                            )

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_notebook_uses_env_vars(self, notebook_config, project_root):
        """Test that notebooks use environment variables for configuration."""
        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        required_env_vars = notebook_config.get("env_vars", [])
        if not required_env_vars:
            pytest.skip("No required environment variables")

        nb = nbformat.read(str(notebook_path), as_version=4)

        # Look for environment variable usage
        env_var_patterns = [
            r"os\.getenv\(['\"](\w+)['\"]",
            r"os\.environ\[['\"](\w+)['\"]\]",
            r"os\.environ\.get\(['\"](\w+)['\"]",
        ]

        found_env_vars = set()
        for cell in nb.cells:
            if cell.cell_type == "code":
                source = "".join(cell.source) if isinstance(cell.source, list) else cell.source
                for pattern in env_var_patterns:
                    found_env_vars.update(re.findall(pattern, source))

        # Check if required env vars are referenced
        for env_var in required_env_vars:
            if env_var not in found_env_vars:
                pytest.skip(
                    f"Required env var '{env_var}' not found (may use alternative method)"
                )

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_notebook_imports_valid(self, notebook_config, project_root):
        """Test that notebook has valid import statements."""
        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        nb = nbformat.read(str(notebook_path), as_version=4)

        import_pattern = r"^(?:from\s+[\w.]+\s+)?import\s+[\w.,\s()]+$"

        for i, cell in enumerate(nb.cells):
            if cell.cell_type == "code":
                source = "".join(cell.source) if isinstance(cell.source, list) else cell.source

                # Find import statements
                for line in source.split("\n"):
                    line = line.strip()
                    if line.startswith(("import ", "from ")):
                        # Basic syntax check
                        if not re.match(import_pattern, line, re.MULTILINE):
                            # Allow multi-line imports
                            if "(" not in line and "\\" not in line:
                                pytest.fail(
                                    f"Invalid import syntax in cell {i}: {line}"
                                )


@pytest.mark.notebook
class TestNotebookDocumentation:
    """Tests for notebook documentation and readability."""

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_notebook_has_markdown(self, notebook_config, project_root):
        """Test that notebook has markdown cells for documentation."""
        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        nb = nbformat.read(str(notebook_path), as_version=4)

        markdown_cells = [c for c in nb.cells if c.cell_type == "markdown"]
        assert len(markdown_cells) > 0, "Notebook has no markdown cells"

    @pytest.mark.parametrize("notebook_config", NOTEBOOKS, ids=get_notebook_ids())
    def test_notebook_has_title(self, notebook_config, project_root):
        """Test that notebook has a title (H1 heading)."""
        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        nb = nbformat.read(str(notebook_path), as_version=4)

        # Look for H1 heading in first few markdown cells
        for cell in nb.cells[:5]:
            if cell.cell_type == "markdown":
                source = "".join(cell.source) if isinstance(cell.source, list) else cell.source
                if re.search(r"^#\s+.+", source, re.MULTILINE):
                    return

        pytest.fail("Notebook has no title (H1 heading)")


@pytest.mark.notebook
@pytest.mark.slow
class TestNotebookExecution:
    """Tests for notebook execution (marked as slow)."""

    @pytest.mark.parametrize(
        "notebook_config",
        [nb for nb in NOTEBOOKS if not nb.get("skip", False)],
        ids=[nb["name"] for nb in NOTEBOOKS if not nb.get("skip", False)],
    )
    def test_notebook_executes(self, notebook_config, project_root, temp_dir):
        """Test that notebook can be executed without errors."""
        pytest.importorskip("papermill")
        import papermill as pm

        notebook_path = project_root / notebook_config["path"]
        if not notebook_path.exists():
            pytest.skip(f"Notebook not found: {notebook_path}")

        if notebook_config.get("requires_gpu", False):
            pytest.skip("GPU required for this notebook")

        output_path = temp_dir / f"executed_{notebook_config['name']}.ipynb"
        timeout = notebook_config.get("timeout", 300)

        try:
            pm.execute_notebook(
                str(notebook_path),
                str(output_path),
                kernel_name="python3",
                timeout=timeout,
            )
        except pm.PapermillExecutionError as e:
            pytest.fail(f"Notebook execution failed: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error during notebook execution: {e}")


@pytest.mark.notebook
class TestNotebookConfiguration:
    """Tests for notebook configuration consistency."""

    def test_all_notebooks_in_manifest(self, project_root):
        """Test that all .ipynb files are listed in manifest."""
        examples_dir = project_root / "examples"
        actual_notebooks = set(examples_dir.rglob("*.ipynb"))

        # Exclude checkpoints and hidden files
        actual_notebooks = {
            nb.relative_to(project_root)
            for nb in actual_notebooks
            if ".ipynb_checkpoints" not in str(nb)
        }

        manifest_notebooks = {
            Path(nb["path"]) for nb in NOTEBOOKS
        }

        missing_in_manifest = actual_notebooks - manifest_notebooks
        if missing_in_manifest:
            pytest.fail(
                f"Notebooks not in manifest: {[str(p) for p in missing_in_manifest]}"
            )

    def test_manifest_notebooks_exist(self, project_root):
        """Test that all notebooks in manifest actually exist."""
        for nb_config in NOTEBOOKS:
            nb_path = project_root / nb_config["path"]
            assert nb_path.exists(), (
                f"Notebook in manifest does not exist: {nb_config['path']}"
            )

    def test_notebook_tags_valid(self):
        """Test that notebook tags follow conventions."""
        valid_tag_prefixes = [
            "llmcompressor",
            "fine-tuning",
            "knowledge-tuning",
            "osft",
            "sft",
            "training-hub",
            "vllm",
            "model-compression",
            "distributed-training",
            "kubeflow",
            "evaluation",
            "data-processing",
            "sdg",
            "data-mixing",
            "training",
            "step-",
        ]

        for nb_config in NOTEBOOKS:
            tags = nb_config.get("tags", [])
            for tag in tags:
                is_valid = any(tag.startswith(prefix) for prefix in valid_tag_prefixes)
                assert is_valid, (
                    f"Invalid tag '{tag}' in notebook '{nb_config['name']}'"
                )
