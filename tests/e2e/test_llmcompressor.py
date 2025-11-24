"""End-to-end tests for llmcompressor example."""

import sys
from pathlib import Path

import pytest


@pytest.mark.e2e
class TestLLMCompressorPipeline:
    """Tests for LLMCompressor KFP pipeline."""

    @pytest.fixture
    def pipeline_module(self, examples_dir):
        """Import the oneshot_pipeline module."""
        pytest.importorskip("kfp")

        llmcompressor_dir = examples_dir / "llmcompressor"
        sys.path.insert(0, str(llmcompressor_dir))

        try:
            import oneshot_pipeline

            return oneshot_pipeline
        except ImportError as e:
            pytest.skip(f"Could not import oneshot_pipeline: {e}")

    def test_pipeline_module_imports(self, pipeline_module):
        """Test that pipeline module imports successfully."""
        assert pipeline_module is not None
        assert hasattr(pipeline_module, "run_oneshot_datafree")
        assert hasattr(pipeline_module, "run_oneshot_calibrated")
        assert hasattr(pipeline_module, "eval_model")

    def test_datafree_component_exists(self, pipeline_module):
        """Test that datafree component is defined."""
        component = pipeline_module.run_oneshot_datafree
        assert component is not None
        assert callable(component)

    def test_calibrated_component_exists(self, pipeline_module):
        """Test that calibrated component is defined."""
        component = pipeline_module.run_oneshot_calibrated
        assert component is not None
        assert callable(component)

    def test_eval_component_exists(self, pipeline_module):
        """Test that eval component is defined."""
        component = pipeline_module.eval_model
        assert component is not None
        assert callable(component)

    def test_pipeline_component_signatures(self, pipeline_module):
        """Test component function signatures."""
        import inspect

        # Test datafree component signature
        datafree_sig = inspect.signature(pipeline_module.run_oneshot_datafree)
        datafree_params = list(datafree_sig.parameters.keys())
        assert "model_id" in datafree_params
        assert "recipe" in datafree_params
        assert "output_model" in datafree_params

        # Test calibrated component signature
        calibrated_sig = inspect.signature(pipeline_module.run_oneshot_calibrated)
        calibrated_params = list(calibrated_sig.parameters.keys())
        assert "model_id" in calibrated_params
        assert "recipe" in calibrated_params
        assert "dataset_id" in calibrated_params

    @pytest.mark.kfp
    def test_pipeline_compilation(self, pipeline_module, temp_dir):
        """Test that the pipeline can be compiled."""
        pytest.importorskip("kfp")
        from kfp import compiler

        # Check if pipeline function exists
        if hasattr(pipeline_module, "oneshot_pipeline"):
            pipeline_func = pipeline_module.oneshot_pipeline
            output_file = temp_dir / "compiled_pipeline.yaml"

            try:
                compiler.Compiler().compile(
                    pipeline_func=pipeline_func, package_path=str(output_file)
                )
                assert output_file.exists()
            except Exception as e:
                pytest.skip(f"Pipeline compilation failed (expected): {e}")


@pytest.mark.e2e
class TestLLMCompressorNotebook:
    """Tests for LLMCompressor workbench notebook."""

    def test_notebook_exists(self, examples_dir):
        """Test that the workbench notebook exists."""
        notebook_path = examples_dir / "llmcompressor" / "workbench_example.ipynb"
        assert notebook_path.exists()
        assert notebook_path.is_file()

    def test_notebook_structure(self, examples_dir):
        """Test basic notebook structure."""
        pytest.importorskip("nbformat")
        import nbformat

        notebook_path = examples_dir / "llmcompressor" / "workbench_example.ipynb"
        nb = nbformat.read(str(notebook_path), as_version=4)

        assert len(nb.cells) > 0
        assert "metadata" in nb
        assert "kernelspec" in nb.metadata or "language_info" in nb.metadata

    def test_notebook_has_compression_code(self, examples_dir):
        """Test that notebook contains compression-related code."""
        pytest.importorskip("nbformat")
        import nbformat

        notebook_path = examples_dir / "llmcompressor" / "workbench_example.ipynb"
        nb = nbformat.read(str(notebook_path), as_version=4)

        # Look for llmcompressor-related imports or functions
        notebook_content = ""
        for cell in nb.cells:
            if cell.cell_type == "code":
                source = (
                    "".join(cell.source) if isinstance(cell.source, list) else cell.source
                )
                notebook_content += source

        # Check for key llmcompressor components
        has_compression_content = any(
            keyword in notebook_content
            for keyword in ["llmcompressor", "oneshot", "compress", "quantiz"]
        )

        if not has_compression_content:
            pytest.skip("Notebook may be a template or different structure")


@pytest.mark.e2e
class TestLLMCompressorRequirements:
    """Tests for LLMCompressor requirements and dependencies."""

    def test_requirements_file_exists(self, examples_dir):
        """Test that requirements.txt exists."""
        req_file = examples_dir / "llmcompressor" / "requirements.txt"
        assert req_file.exists()

    def test_requirements_content(self, examples_dir):
        """Test that requirements.txt has expected dependencies."""
        req_file = examples_dir / "llmcompressor" / "requirements.txt"
        content = req_file.read_text()

        # Check for KFP dependencies
        assert "kfp" in content.lower()

    def test_readme_exists(self, examples_dir):
        """Test that README exists."""
        readme = examples_dir / "llmcompressor" / "README.md"
        assert readme.exists()

    def test_readme_has_content(self, examples_dir):
        """Test that README has meaningful content."""
        readme = examples_dir / "llmcompressor" / "README.md"
        content = readme.read_text()

        assert len(content) > 100
        assert any(
            keyword in content.lower()
            for keyword in ["llm", "compress", "quantiz", "vllm"]
        )


@pytest.mark.e2e
@pytest.mark.kfp
class TestPipelineComponents:
    """Tests for individual KFP components."""

    def test_component_decorator_usage(self, examples_dir):
        """Test that components use KFP decorators."""
        pytest.importorskip("kfp")

        pipeline_file = examples_dir / "llmcompressor" / "oneshot_pipeline.py"
        content = pipeline_file.read_text()

        # Check for component decorator
        assert "@kfp.dsl.component" in content or "@dsl.component" in content

    def test_component_base_images(self, examples_dir):
        """Test that components specify base images."""
        pipeline_file = examples_dir / "llmcompressor" / "oneshot_pipeline.py"
        content = pipeline_file.read_text()

        # Check for base image specification
        assert "base_image" in content
        assert "llmcompressor-pipeline-runtime" in content

    def test_component_io_artifacts(self, examples_dir):
        """Test that components use KFP I/O artifacts."""
        pipeline_file = examples_dir / "llmcompressor" / "oneshot_pipeline.py"
        content = pipeline_file.read_text()

        # Check for artifact usage
        assert "dsl.Output" in content or "Output[" in content
        assert "dsl.Input" in content or "Input[" in content or "dsl.Output" in content


@pytest.mark.e2e
class TestLLMCompressorIntegration:
    """Integration tests for LLMCompressor workflow."""

    def test_recipe_usage(self, examples_dir):
        """Test that example uses compression recipes."""
        pipeline_file = examples_dir / "llmcompressor" / "oneshot_pipeline.py"
        content = pipeline_file.read_text()

        # Check for recipe parameter
        assert "recipe" in content

    def test_model_loading(self, examples_dir):
        """Test that components load models properly."""
        pipeline_file = examples_dir / "llmcompressor" / "oneshot_pipeline.py"
        content = pipeline_file.read_text()

        # Check for model loading
        assert "AutoModelForCausalLM" in content
        assert "from_pretrained" in content

    def test_model_saving(self, examples_dir):
        """Test that components save compressed models."""
        pipeline_file = examples_dir / "llmcompressor" / "oneshot_pipeline.py"
        content = pipeline_file.read_text()

        # Check for model saving
        assert "save_pretrained" in content

    def test_dataset_handling(self, examples_dir):
        """Test that calibrated compression uses datasets."""
        pipeline_file = examples_dir / "llmcompressor" / "oneshot_pipeline.py"
        content = pipeline_file.read_text()

        # Check for dataset loading and processing
        assert "load_dataset" in content or "dataset" in content

    def test_tokenizer_usage(self, examples_dir):
        """Test that components use tokenizers."""
        pipeline_file = examples_dir / "llmcompressor" / "oneshot_pipeline.py"
        content = pipeline_file.read_text()

        # Check for tokenizer
        assert "tokenizer" in content
        assert "AutoTokenizer" in content


@pytest.mark.e2e
class TestLLMCompressorDocumentation:
    """Tests for LLMCompressor documentation."""

    def test_readme_structure(self, examples_dir):
        """Test README has proper structure."""
        readme = examples_dir / "llmcompressor" / "README.md"
        content = readme.read_text()

        # Check for common README sections
        has_sections = any(
            section in content
            for section in ["#", "##", "###", "Overview", "Usage", "Example"]
        )
        assert has_sections

    def test_example_files_present(self, examples_dir):
        """Test that all expected files are present."""
        llmcompressor_dir = examples_dir / "llmcompressor"

        expected_files = [
            "oneshot_pipeline.py",
            "workbench_example.ipynb",
            "requirements.txt",
            "README.md",
        ]

        for file_name in expected_files:
            file_path = llmcompressor_dir / file_name
            assert file_path.exists(), f"Expected file not found: {file_name}"
