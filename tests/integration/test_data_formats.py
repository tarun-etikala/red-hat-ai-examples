"""Integration tests for data format validation and handling."""

import json
from pathlib import Path

import pytest


@pytest.mark.integration
class TestJSONLFormat:
    """Tests for JSONL (JSON Lines) format handling."""

    def test_read_jsonl_file(self, sample_jsonl_file):
        """Test reading JSONL file."""
        lines = sample_jsonl_file.read_text().strip().split("\n")
        assert len(lines) == 3

        for line in lines:
            data = json.loads(line)
            assert "messages" in data
            assert isinstance(data["messages"], list)

    def test_jsonl_message_structure(self, sample_jsonl_file):
        """Test JSONL message structure."""
        lines = sample_jsonl_file.read_text().strip().split("\n")

        for line in lines:
            data = json.loads(line)
            messages = data["messages"]

            # Each message should have role and content
            for msg in messages:
                assert "role" in msg
                assert "content" in msg
                assert msg["role"] in ["user", "assistant", "system"]

    def test_write_jsonl_format(self, temp_dir):
        """Test writing JSONL format."""
        output_file = temp_dir / "output.jsonl"

        test_data = [
            {"messages": [{"role": "user", "content": "Hello"}]},
            {"messages": [{"role": "assistant", "content": "Hi there"}]},
        ]

        with open(output_file, "w") as f:
            for item in test_data:
                f.write(json.dumps(item) + "\n")

        # Verify written data
        assert output_file.exists()
        lines = output_file.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_jsonl_with_metadata(self, temp_dir):
        """Test JSONL with metadata field."""
        jsonl_file = temp_dir / "with_metadata.jsonl"

        data = {
            "messages": [
                {"role": "user", "content": "Test"},
                {"role": "assistant", "content": "Response"},
            ],
            "metadata": json.dumps({
                "sdg_document": "doc1",
                "dataset": "test_dataset",
                "raw_document": "raw1",
            }),
        }

        jsonl_file.write_text(json.dumps(data) + "\n")

        # Read and validate
        loaded = json.loads(jsonl_file.read_text().strip())
        assert "metadata" in loaded
        metadata = json.loads(loaded["metadata"])
        assert metadata["dataset"] == "test_dataset"

    def test_jsonl_with_unmask_field(self, temp_dir):
        """Test JSONL with unmask field for pre-training."""
        jsonl_file = temp_dir / "with_unmask.jsonl"

        data = {
            "messages": [{"role": "user", "content": "Q"}],
            "metadata": "{}",
            "unmask": True,
        }

        jsonl_file.write_text(json.dumps(data) + "\n")

        loaded = json.loads(jsonl_file.read_text().strip())
        assert "unmask" in loaded
        assert loaded["unmask"] is True


@pytest.mark.integration
class TestNotebookFormat:
    """Tests for Jupyter Notebook format validation."""

    def test_notebook_json_structure(self, minimal_notebook, temp_dir):
        """Test notebook JSON structure."""
        nb_file = temp_dir / "test.ipynb"
        nb_file.write_text(json.dumps(minimal_notebook))

        # Read and validate structure
        nb_data = json.loads(nb_file.read_text())
        assert "cells" in nb_data
        assert "metadata" in nb_data
        assert "nbformat" in nb_data
        assert nb_data["nbformat"] == 4

    def test_notebook_cell_types(self, minimal_notebook):
        """Test notebook cell types."""
        cells = minimal_notebook["cells"]

        for cell in cells:
            assert "cell_type" in cell
            assert cell["cell_type"] in ["code", "markdown", "raw"]

    def test_notebook_with_outputs(self, notebook_with_outputs, temp_dir):
        """Test notebook with cell outputs."""
        nb_file = temp_dir / "with_outputs.ipynb"
        nb_file.write_text(json.dumps(notebook_with_outputs))

        nb_data = json.loads(nb_file.read_text())
        code_cells = [c for c in nb_data["cells"] if c["cell_type"] == "code"]

        assert len(code_cells) > 0
        assert "outputs" in code_cells[0]
        assert len(code_cells[0]["outputs"]) > 0


@pytest.mark.integration
class TestEnvFileFormat:
    """Tests for .env file format."""

    def test_read_env_file(self, sample_env_file):
        """Test reading .env file."""
        content = sample_env_file.read_text()
        assert "MODEL_NAME" in content
        assert "DATASET_PATH" in content

    def test_parse_env_file(self, sample_env_file):
        """Test parsing .env file into dict."""
        env_vars = {}
        for line in sample_env_file.read_text().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key] = value

        assert "MODEL_NAME" in env_vars
        assert env_vars["MODEL_NAME"] == "test-model"

    def test_dotenv_loading(self, sample_env_file):
        """Test loading .env file with python-dotenv."""
        try:
            from dotenv import dotenv_values

            env_vars = dotenv_values(sample_env_file)
            assert "MODEL_NAME" in env_vars
            assert env_vars["MODEL_NAME"] == "test-model"
        except ImportError:
            pytest.skip("python-dotenv not installed")


@pytest.mark.integration
class TestYAMLFormat:
    """Tests for YAML format handling."""

    def test_read_yaml_config(self, project_root):
        """Test reading YAML configuration."""
        pytest.importorskip("yaml")
        import yaml

        manifest_path = (
            project_root / "tests" / "notebooks" / "notebooks_manifest.yaml"
        )
        with open(manifest_path) as f:
            data = yaml.safe_load(f)

        assert "notebooks" in data
        assert isinstance(data["notebooks"], list)

    def test_yaml_notebook_config(self, project_root):
        """Test YAML notebook configuration structure."""
        pytest.importorskip("yaml")
        import yaml

        manifest_path = (
            project_root / "tests" / "notebooks" / "notebooks_manifest.yaml"
        )
        with open(manifest_path) as f:
            data = yaml.safe_load(f)

        for notebook in data["notebooks"]:
            assert "path" in notebook
            assert "name" in notebook
            assert "requires_gpu" in notebook
            assert isinstance(notebook["requires_gpu"], bool)


@pytest.mark.integration
class TestMessageFormats:
    """Tests for chat message formats."""

    def test_basic_message_structure(self):
        """Test basic message structure."""
        message = {"role": "user", "content": "Hello", "thinking": None}

        assert "role" in message
        assert "content" in message
        assert message["role"] in ["user", "assistant", "system"]

    def test_message_with_reasoning(self):
        """Test message with reasoning/thinking field."""
        message = {
            "role": "assistant",
            "content": "Answer here",
            "thinking": "Reasoning here",
        }

        assert message["thinking"] is not None
        assert isinstance(message["thinking"], str)

    def test_message_serialization(self):
        """Test message serialization to JSON."""
        messages = [
            {"role": "user", "content": "Question?", "thinking": None},
            {"role": "assistant", "content": "Answer", "thinking": "Reason"},
        ]

        json_str = json.dumps(messages)
        loaded = json.loads(json_str)

        assert len(loaded) == 2
        assert loaded[0]["role"] == "user"
        assert loaded[1]["thinking"] == "Reason"


@pytest.mark.integration
class TestDatasetFormats:
    """Tests for dataset formats (HuggingFace datasets)."""

    def test_dataset_dict_format(self):
        """Test dataset dict format."""
        try:
            pytest.importorskip("datasets")
            from datasets import Dataset

            data_dict = {
                "question": ["Q1", "Q2"],
                "response": ["A1", "A2"],
            }

            dataset = Dataset.from_dict(data_dict)
            assert len(dataset) == 2
            assert "question" in dataset.column_names
        except ImportError:
            pytest.skip("datasets not installed")

    def test_jsonl_to_dataset(self, sample_jsonl_file):
        """Test converting JSONL to dataset."""
        try:
            pytest.importorskip("datasets")
            from datasets import load_dataset

            dataset = load_dataset("json", data_files=str(sample_jsonl_file))
            assert "train" in dataset
            assert len(dataset["train"]) == 3
        except ImportError:
            pytest.skip("datasets not installed")


@pytest.mark.integration
class TestPolarsDataFrameFormat:
    """Tests for Polars DataFrame format."""

    def test_polars_from_dict(self):
        """Test creating Polars DataFrame from dict."""
        try:
            pytest.importorskip("polars")
            import polars as pl

            data = {
                "question": ["Q1", "Q2"],
                "response": ["A1", "A2"],
                "document": ["D1", "D2"],
            }

            df = pl.DataFrame(data)
            assert len(df) == 2
            assert df.columns == ["question", "response", "document"]
        except ImportError:
            pytest.skip("polars not installed")

    def test_polars_to_jsonl(self, temp_dir):
        """Test exporting Polars DataFrame to JSONL."""
        try:
            pytest.importorskip("polars")
            import polars as pl

            data = {
                "messages": [
                    [{"role": "user", "content": "Q1"}],
                    [{"role": "user", "content": "Q2"}],
                ]
            }

            df = pl.DataFrame(data)
            output_file = temp_dir / "polars_output.jsonl"

            # Write to JSONL (line by line)
            with open(output_file, "w") as f:
                for row in df.iter_rows(named=True):
                    f.write(json.dumps(row) + "\n")

            assert output_file.exists()
            lines = output_file.read_text().strip().split("\n")
            assert len(lines) == 2
        except ImportError:
            pytest.skip("polars not installed")


@pytest.mark.integration
class TestModelConfigFormats:
    """Tests for model configuration formats."""

    def test_model_config_json(self, mock_model_config, temp_dir):
        """Test model config JSON format."""
        config_file = temp_dir / "model_config.json"
        config_file.write_text(json.dumps(mock_model_config, indent=2))

        loaded = json.loads(config_file.read_text())
        assert loaded["model_name"] == "test-model"
        assert "hidden_size" in loaded

    def test_training_config_json(self, mock_training_config, temp_dir):
        """Test training config JSON format."""
        config_file = temp_dir / "training_config.json"
        config_file.write_text(json.dumps(mock_training_config, indent=2))

        loaded = json.loads(config_file.read_text())
        assert "num_train_epochs" in loaded
        assert "learning_rate" in loaded


@pytest.mark.integration
class TestEdgeCases:
    """Tests for edge cases in data formats."""

    def test_empty_jsonl_file(self, temp_dir):
        """Test handling empty JSONL file."""
        empty_file = temp_dir / "empty.jsonl"
        empty_file.write_text("")

        content = empty_file.read_text().strip()
        assert content == ""

    def test_jsonl_with_special_characters(self, temp_dir):
        """Test JSONL with special characters."""
        jsonl_file = temp_dir / "special_chars.jsonl"

        data = {
            "messages": [
                {"role": "user", "content": "Quote: \"Hello\""},
                {"role": "assistant", "content": "Newline:\nHere"},
            ]
        }

        jsonl_file.write_text(json.dumps(data) + "\n")

        loaded = json.loads(jsonl_file.read_text().strip())
        assert '"Hello"' in loaded["messages"][0]["content"]
        assert "\n" in loaded["messages"][1]["content"]

    def test_jsonl_with_unicode(self, temp_dir):
        """Test JSONL with Unicode characters."""
        jsonl_file = temp_dir / "unicode.jsonl"

        data = {"messages": [{"role": "user", "content": "Hello 世界 🌍"}]}

        jsonl_file.write_text(json.dumps(data, ensure_ascii=False) + "\n")

        loaded = json.loads(jsonl_file.read_text().strip())
        assert "世界" in loaded["messages"][0]["content"]
        assert "🌍" in loaded["messages"][0]["content"]

    def test_large_jsonl_entry(self, temp_dir):
        """Test JSONL with large content."""
        jsonl_file = temp_dir / "large.jsonl"

        large_content = "A" * 10000
        data = {"messages": [{"role": "user", "content": large_content}]}

        jsonl_file.write_text(json.dumps(data) + "\n")

        loaded = json.loads(jsonl_file.read_text().strip())
        assert len(loaded["messages"][0]["content"]) == 10000
