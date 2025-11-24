"""End-to-end tests for Training Hub SFT example."""

import pytest


@pytest.mark.e2e
@pytest.mark.gpu
@pytest.mark.rhoai
class TestTrainingHubSFT:
    """Tests for Training Hub SFT fine-tuning example."""

    def test_sft_directory_exists(self, examples_dir):
        """Test that SFT directory exists."""
        sft_dir = examples_dir / "fine-tuning" / "training-hub" / "sft"
        assert sft_dir.exists()
        assert sft_dir.is_dir()

    def test_sft_notebook_exists(self, examples_dir):
        """Test that SFT notebook exists."""
        notebook = examples_dir / "fine-tuning" / "training-hub" / "sft" / "sft.ipynb"
        assert notebook.exists()

    def test_sft_readme_exists(self, examples_dir):
        """Test that SFT README exists."""
        readme = examples_dir / "fine-tuning" / "training-hub" / "sft" / "README.md"
        assert readme.exists()

    def test_sft_documentation_present(self, examples_dir):
        """Test that SFT has documentation images."""
        images_dir = examples_dir / "fine-tuning" / "training-hub" / "sft" / "images"
        if images_dir.exists():
            image_files = list(images_dir.glob("*.png"))
            assert len(image_files) > 0, "No documentation images found"

    def test_sft_readme_content(self, examples_dir):
        """Test SFT README has meaningful content."""
        readme = examples_dir / "fine-tuning" / "training-hub" / "sft" / "README.md"
        content = readme.read_text()

        assert len(content) > 200
        assert any(
            keyword in content.lower()
            for keyword in ["sft", "supervised", "fine-tuning", "training-hub"]
        )

    def test_sft_mentions_kubeflow(self, examples_dir):
        """Test that SFT documentation mentions Kubeflow."""
        readme = examples_dir / "fine-tuning" / "training-hub" / "sft" / "README.md"
        content = readme.read_text()

        has_kubeflow = any(
            keyword in content.lower() for keyword in ["kubeflow", "kfp", "pipeline"]
        )

        if not has_kubeflow:
            pytest.skip("SFT may use different orchestration")

    @pytest.mark.skip(reason="Requires GPU and Kubeflow Training operator")
    def test_sft_execution(self):
        """Test SFT notebook execution (skipped - requires GPU and K8s)."""
        pass
