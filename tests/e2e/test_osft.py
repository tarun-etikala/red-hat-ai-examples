"""End-to-end tests for OSFT fine-tuning example."""

import pytest


@pytest.mark.e2e
@pytest.mark.gpu
@pytest.mark.rhoai
class TestOSFTExample:
    """Tests for OSFT fine-tuning example."""

    def test_osft_directory_exists(self, examples_dir):
        """Test that OSFT directory exists."""
        osft_dir = examples_dir / "fine-tuning" / "osft"
        assert osft_dir.exists()
        assert osft_dir.is_dir()

    def test_osft_notebook_exists(self, examples_dir):
        """Test that OSFT notebook exists."""
        notebook = examples_dir / "fine-tuning" / "osft" / "osft-example.ipynb"
        assert notebook.exists()

    def test_osft_readme_exists(self, examples_dir):
        """Test that OSFT README exists."""
        readme = examples_dir / "fine-tuning" / "osft" / "README.md"
        assert readme.exists()

    def test_osft_documentation_present(self, examples_dir):
        """Test that OSFT has documentation images."""
        docs_dir = examples_dir / "fine-tuning" / "osft" / "docs"
        if docs_dir.exists():
            image_files = list(docs_dir.glob("*.png"))
            assert len(image_files) > 0, "No documentation images found"

    def test_osft_readme_content(self, examples_dir):
        """Test OSFT README has meaningful content."""
        readme = examples_dir / "fine-tuning" / "osft" / "README.md"
        content = readme.read_text()

        assert len(content) > 200
        assert any(
            keyword in content.lower()
            for keyword in ["osft", "orthogonal", "fine-tuning", "continual"]
        )

    @pytest.mark.skip(reason="Requires GPU and distributed training setup")
    def test_osft_execution(self):
        """Test OSFT notebook execution (skipped - requires GPU)."""
        pass
