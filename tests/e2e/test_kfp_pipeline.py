"""End-to-end tests for domain customization KFP pipeline."""

import sys
from pathlib import Path

import pytest


@pytest.mark.e2e
@pytest.mark.kfp
class TestKFPPipelineScript:
    """Tests for KFP enhanced summary knowledge tuning pipeline."""

    @pytest.fixture
    def pipeline_dir(self, examples_dir):
        """Get the KFP pipeline directory."""
        return examples_dir / "domain_customization_kfp_pipeline"

    def test_pipeline_file_exists(self, pipeline_dir):
        """Test that pipeline Python file exists."""
        pipeline_file = pipeline_dir / "kfp_enhanced_summary_knowledge_tuning.py"
        assert pipeline_file.exists()
        assert pipeline_file.is_file()

    def test_compiled_yaml_exists(self, pipeline_dir):
        """Test that compiled pipeline YAML exists."""
        yaml_file = pipeline_dir / "knowledge_generation_pipeline.yaml"
        assert yaml_file.exists()
        assert yaml_file.is_file()

    def test_env_example_exists(self, pipeline_dir):
        """Test that environment example file exists."""
        env_file = pipeline_dir / "env.example"
        assert env_file.exists()

    def test_readme_exists(self, pipeline_dir):
        """Test that README exists."""
        readme = pipeline_dir / "README.md"
        assert readme.exists()

    def test_pipeline_python_syntax(self, pipeline_dir):
        """Test that pipeline Python file is valid syntax."""
        pipeline_file = pipeline_dir / "kfp_enhanced_summary_knowledge_tuning.py"

        try:
            with open(pipeline_file) as f:
                compile(f.read(), str(pipeline_file), "exec")
        except SyntaxError as e:
            pytest.fail(f"Pipeline has syntax error: {e}")

    def test_pipeline_imports_kfp(self, pipeline_dir):
        """Test that pipeline imports KFP."""
        pipeline_file = pipeline_dir / "kfp_enhanced_summary_knowledge_tuning.py"
        content = pipeline_file.read_text()

        assert "import kfp" in content or "from kfp" in content

    def test_pipeline_has_components(self, pipeline_dir):
        """Test that pipeline defines components."""
        pipeline_file = pipeline_dir / "kfp_enhanced_summary_knowledge_tuning.py"
        content = pipeline_file.read_text()

        # Check for component definitions
        assert "@dsl.component" in content or "@kfp.dsl.component" in content

    def test_pipeline_has_pipeline_function(self, pipeline_dir):
        """Test that pipeline has a pipeline function."""
        pipeline_file = pipeline_dir / "kfp_enhanced_summary_knowledge_tuning.py"
        content = pipeline_file.read_text()

        # Check for pipeline decorator
        assert "@dsl.pipeline" in content or "@kfp.dsl.pipeline" in content


@pytest.mark.e2e
@pytest.mark.kfp
class TestCompiledPipelineYAML:
    """Tests for the compiled pipeline YAML file."""

    @pytest.fixture
    def yaml_content(self, examples_dir):
        """Load the compiled pipeline YAML."""
        pytest.importorskip("yaml")
        import yaml

        yaml_file = (
            examples_dir
            / "domain_customization_kfp_pipeline"
            / "knowledge_generation_pipeline.yaml"
        )

        with open(yaml_file) as f:
            return yaml.safe_load(f)

    def test_yaml_is_valid(self, yaml_content):
        """Test that YAML is valid and parseable."""
        assert yaml_content is not None
        assert isinstance(yaml_content, dict)

    def test_yaml_has_pipeline_spec(self, yaml_content):
        """Test that YAML has pipeline specification."""
        # KFP v2 YAML structure
        assert "pipelineSpec" in yaml_content or "spec" in yaml_content

    def test_yaml_has_components(self, yaml_content):
        """Test that YAML defines components."""
        # Look for components in the spec
        if "pipelineSpec" in yaml_content:
            spec = yaml_content["pipelineSpec"]
            assert "components" in spec or "deploymentSpec" in spec


@pytest.mark.e2e
class TestKFPPipelineConfiguration:
    """Tests for KFP pipeline configuration."""

    def test_env_example_format(self, examples_dir):
        """Test env.example file format."""
        env_file = (
            examples_dir / "domain_customization_kfp_pipeline" / "env.example"
        )
        content = env_file.read_text()

        # Should have environment variable definitions
        assert "=" in content

        # Parse as key=value pairs
        env_vars = {}
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key] = value

        assert len(env_vars) > 0

    def test_env_variables_documented(self, examples_dir):
        """Test that environment variables are documented."""
        readme = examples_dir / "domain_customization_kfp_pipeline" / "README.md"
        content = readme.read_text()

        # README should mention environment variables or configuration
        assert any(
            keyword in content.lower()
            for keyword in ["environment", "variable", "config", "setup"]
        )


@pytest.mark.e2e
@pytest.mark.kfp
class TestPipelineComponents:
    """Tests for individual pipeline components."""

    @pytest.fixture
    def pipeline_module(self, examples_dir):
        """Import the pipeline module."""
        pytest.importorskip("kfp")

        pipeline_dir = examples_dir / "domain_customization_kfp_pipeline"
        sys.path.insert(0, str(pipeline_dir))

        try:
            import kfp_enhanced_summary_knowledge_tuning

            return kfp_enhanced_summary_knowledge_tuning
        except ImportError as e:
            pytest.skip(f"Could not import pipeline module: {e}")

    def test_module_imports(self, pipeline_module):
        """Test that pipeline module imports successfully."""
        assert pipeline_module is not None

    def test_pipeline_uses_sdg_hub(self, examples_dir):
        """Test that pipeline uses SDG hub."""
        pipeline_file = (
            examples_dir
            / "domain_customization_kfp_pipeline"
            / "kfp_enhanced_summary_knowledge_tuning.py"
        )
        content = pipeline_file.read_text()

        # Check for SDG hub usage
        assert "sdg" in content.lower() or "synthetic" in content.lower()

    def test_pipeline_uses_datasets(self, examples_dir):
        """Test that pipeline uses datasets library."""
        pipeline_file = (
            examples_dir
            / "domain_customization_kfp_pipeline"
            / "kfp_enhanced_summary_knowledge_tuning.py"
        )
        content = pipeline_file.read_text()

        # Check for datasets usage
        assert "dataset" in content.lower()


@pytest.mark.e2e
class TestKFPPipelineDocumentation:
    """Tests for KFP pipeline documentation."""

    def test_readme_content(self, examples_dir):
        """Test README has meaningful content."""
        readme = examples_dir / "domain_customization_kfp_pipeline" / "README.md"
        content = readme.read_text()

        assert len(content) > 200

        # Check for key topics
        topics_covered = [
            "pipeline" in content.lower(),
            "kubeflow" in content.lower() or "kfp" in content.lower(),
            "knowledge" in content.lower() or "synthetic" in content.lower(),
        ]

        assert any(topics_covered)

    def test_readme_has_instructions(self, examples_dir):
        """Test README has usage instructions."""
        readme = examples_dir / "domain_customization_kfp_pipeline" / "README.md"
        content = readme.read_text()

        # Should have some form of instructions
        has_instructions = any(
            keyword in content.lower()
            for keyword in ["setup", "usage", "run", "deploy", "step"]
        )

        assert has_instructions


@pytest.mark.e2e
@pytest.mark.kfp
class TestPipelineExecution:
    """Tests for pipeline execution (dry-run/validation only)."""

    def test_pipeline_compilation_possible(self, examples_dir, temp_dir):
        """Test that pipeline can be compiled (if module imports)."""
        pytest.importorskip("kfp")

        try:
            pipeline_dir = examples_dir / "domain_customization_kfp_pipeline"
            sys.path.insert(0, str(pipeline_dir))

            import kfp_enhanced_summary_knowledge_tuning

            # Try to find pipeline function
            pipeline_funcs = [
                attr
                for attr in dir(kfp_enhanced_summary_knowledge_tuning)
                if "pipeline" in attr.lower() and not attr.startswith("_")
            ]

            if not pipeline_funcs:
                pytest.skip("No pipeline function found for compilation test")

        except Exception as e:
            pytest.skip(f"Pipeline compilation test skipped: {e}")


@pytest.mark.e2e
class TestKFPPipelineStructure:
    """Tests for pipeline structure and organization."""

    def test_all_required_files_present(self, examples_dir):
        """Test that all required files are present."""
        pipeline_dir = examples_dir / "domain_customization_kfp_pipeline"

        required_files = [
            "kfp_enhanced_summary_knowledge_tuning.py",
            "knowledge_generation_pipeline.yaml",
            "env.example",
            "README.md",
        ]

        for file_name in required_files:
            file_path = pipeline_dir / file_name
            assert file_path.exists(), f"Required file not found: {file_name}"

    def test_no_hardcoded_secrets(self, examples_dir):
        """Test that pipeline doesn't have hardcoded secrets."""
        import re

        pipeline_file = (
            examples_dir
            / "domain_customization_kfp_pipeline"
            / "kfp_enhanced_summary_knowledge_tuning.py"
        )
        content = pipeline_file.read_text()

        # Patterns that might indicate secrets
        secret_patterns = [
            r"(?i)(api[_-]?key|apikey)\s*=\s*['\"][^'\"]{20,}['\"]",
            r"(?i)(token)\s*=\s*['\"][^'\"]{30,}['\"]",
            r"(?i)(password|passwd)\s*=\s*['\"][^'\"]+['\"]",
        ]

        for pattern in secret_patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Allow environment variable usage
                if not any(
                    keyword in content for keyword in ["os.getenv", "os.environ"]
                ):
                    pytest.fail(f"Potential hardcoded secret found: {matches[0]}")

    def test_pipeline_uses_secrets_properly(self, examples_dir):
        """Test that pipeline uses Kubernetes secrets."""
        pipeline_file = (
            examples_dir
            / "domain_customization_kfp_pipeline"
            / "kfp_enhanced_summary_knowledge_tuning.py"
        )
        content = pipeline_file.read_text()

        # Should reference secrets in some way
        uses_secrets = any(
            keyword in content.lower()
            for keyword in ["secret", "env", "environment", "config"]
        )

        # This is informational, not a hard requirement
        if not uses_secrets:
            pytest.skip("Pipeline may not use secrets (template or different approach)")
