"""Unit tests for knowledge_utils.py module."""

import json
from unittest.mock import MagicMock

import polars as pl
import pytest

# Import the module to test
import sys
from pathlib import Path

knowledge_mixing_utils = (
    Path(__file__).parent.parent.parent
    / "examples"
    / "knowledge-tuning"
    / "04_Knowledge_Mixing"
    / "utils"
)
sys.path.insert(0, str(knowledge_mixing_utils))

from knowledge_utils import (
    _clean_response_text,
    _create_messages_with_reasoning,
    _create_messages_with_reasoning_no_document,
    _create_messages_without_reasoning,
    _create_messages_without_reasoning_no_document,
    count_len_in_tokens,
    generate_knowledge_qa_dataset,
    get_avg_summaries_per_raw_doc,
    sample_doc_qa,
)


@pytest.fixture
def sample_qa_dataframe():
    """Create a sample Q&A dataframe for testing."""
    return pl.DataFrame({
        "question": ["What is AI?", "What is ML?", "What is DL?"],
        "response": ["Artificial Intelligence", "Machine Learning", "Deep Learning"],
        "document": ["doc1", "doc1", "doc2"],
        "raw_document": ["raw1", "raw1", "raw2"],
        "document_outline": ["AI outline", "ML outline", "DL outline"],
    })


@pytest.fixture
def sample_qa_dataframe_with_reasoning():
    """Create a sample Q&A dataframe with reasoning column."""
    return pl.DataFrame({
        "question": ["What is AI?", "What is ML?"],
        "response": ["Artificial Intelligence", "Machine Learning"],
        "document": ["doc1", "doc2"],
        "raw_document": ["raw1", "raw1"],
        "document_outline": ["AI outline", "ML outline"],
        "reasoning": ["AI is about machines", "ML is a subset of AI"],
    })


@pytest.fixture
def sample_dirty_responses():
    """Create a dataframe with dirty response text."""
    return pl.DataFrame({
        "response": [
            "Answer here [END]",
            "[ANSWER] Response text [END]",
            "  Clean response  ",
        ]
    })


class TestGetAvgSummariesPerRawDoc:
    """Tests for get_avg_summaries_per_raw_doc function."""

    def test_basic_calculation(self):
        """Test average calculation with simple data."""
        df = pl.DataFrame({
            "document": ["d1", "d2", "d3", "d4"],
            "raw_document": ["r1", "r1", "r2", "r2"],
        })
        avg = get_avg_summaries_per_raw_doc(df)
        assert avg == 2.0

    def test_uneven_distribution(self):
        """Test average with uneven distribution."""
        df = pl.DataFrame({
            "document": ["d1", "d2", "d3", "d4", "d5"],
            "raw_document": ["r1", "r1", "r1", "r2", "r2"],
        })
        avg = get_avg_summaries_per_raw_doc(df)
        assert avg == 2.5

    def test_single_raw_document(self):
        """Test with single raw document."""
        df = pl.DataFrame({
            "document": ["d1", "d2", "d3"],
            "raw_document": ["r1", "r1", "r1"],
        })
        avg = get_avg_summaries_per_raw_doc(df)
        assert avg == 3.0

    def test_duplicate_documents(self):
        """Test that duplicate documents are counted only once."""
        df = pl.DataFrame({
            "document": ["d1", "d1", "d2", "d2"],
            "raw_document": ["r1", "r1", "r1", "r1"],
        })
        avg = get_avg_summaries_per_raw_doc(df)
        assert avg == 2.0  # Only 2 unique documents


class TestSampleDocQA:
    """Tests for sample_doc_qa function."""

    def test_basic_sampling(self, sample_qa_dataframe):
        """Test basic sampling functionality."""
        result = sample_doc_qa(sample_qa_dataframe, n_docs_per_raw=2, qa_per_doc=2)
        assert isinstance(result, pl.DataFrame)
        assert "question" in result.columns
        assert "response" in result.columns

    def test_missing_columns(self):
        """Test that missing required columns raise error."""
        df = pl.DataFrame({"question": ["Q1"], "response": ["A1"]})
        with pytest.raises(ValueError, match="Missing required columns"):
            sample_doc_qa(df)

    def test_qa_per_doc_limit(self, sample_qa_dataframe):
        """Test that qa_per_doc limit is respected."""
        # Add more Q&A pairs to same document
        extended_df = pl.concat([
            sample_qa_dataframe,
            pl.DataFrame({
                "question": ["Q4", "Q5", "Q6"],
                "response": ["A4", "A5", "A6"],
                "document": ["doc1", "doc1", "doc1"],
                "raw_document": ["raw1", "raw1", "raw1"],
                "document_outline": ["O1", "O1", "O1"],
            }),
        ])

        result = sample_doc_qa(extended_df, n_docs_per_raw=1, qa_per_doc=2)
        # Each document should have at most 2 Q&A pairs
        doc_counts = result.group_by("document").agg(pl.count().alias("count"))
        assert all(doc_counts["count"] <= 2)

    def test_n_docs_per_raw_limit(self):
        """Test that n_docs_per_raw sampling works."""
        df = pl.DataFrame({
            "question": [f"Q{i}" for i in range(10)],
            "response": [f"A{i}" for i in range(10)],
            "document": [f"doc{i}" for i in range(10)],
            "raw_document": ["raw1"] * 10,
            "document_outline": ["outline"] * 10,
        })

        result = sample_doc_qa(df, n_docs_per_raw=3, qa_per_doc=1)
        unique_docs = result["document"].n_unique()
        assert unique_docs <= 3

    def test_with_reasoning_column(self, sample_qa_dataframe_with_reasoning):
        """Test sampling with reasoning column present."""
        result = sample_doc_qa(
            sample_qa_dataframe_with_reasoning, n_docs_per_raw=2, qa_per_doc=1
        )
        assert "reasoning" in result.columns


class TestCleanResponseText:
    """Tests for _clean_response_text function."""

    def test_remove_end_marker(self, sample_dirty_responses):
        """Test that [END] marker is removed."""
        cleaned = _clean_response_text(sample_dirty_responses)
        assert "[END]" not in cleaned["response"][0]
        assert "[END]" not in cleaned["response"][1]

    def test_remove_answer_marker(self, sample_dirty_responses):
        """Test that [ANSWER] marker is removed."""
        cleaned = _clean_response_text(sample_dirty_responses)
        assert "[ANSWER]" not in cleaned["response"][1]

    def test_strip_whitespace(self, sample_dirty_responses):
        """Test that whitespace is stripped."""
        cleaned = _clean_response_text(sample_dirty_responses)
        assert cleaned["response"][2] == "Clean response"

    def test_combined_cleaning(self):
        """Test multiple cleaning operations."""
        df = pl.DataFrame({"response": ["  [ANSWER] Text here [END]  "]})
        cleaned = _clean_response_text(df)
        assert cleaned["response"][0] == "Text here"


class TestCreateMessagesWithReasoning:
    """Tests for message creation functions with reasoning."""

    def test_create_messages_with_reasoning(self):
        """Test message creation with reasoning and document."""
        record = {
            "document_outline": "Test Outline",
            "document": "Test Document",
            "question": "What is this?",
            "response": "This is a test",
            "reasoning": "Because it's a test",
        }
        messages = _create_messages_with_reasoning(record)

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["thinking"] is None
        assert "Test Outline" in messages[0]["content"]
        assert "Test Document" in messages[0]["content"]
        assert "What is this?" in messages[0]["content"]

        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "This is a test"
        assert messages[1]["thinking"] == "Because it's a test"

    def test_create_messages_with_reasoning_no_document(self):
        """Test message creation with reasoning but no document."""
        record = {
            "document_outline": "Test Outline",
            "question": "What is this?",
            "response": "This is a test",
            "reasoning": "Because it's a test",
        }
        messages = _create_messages_with_reasoning_no_document(record)

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert "In Test Outline" in messages[0]["content"]
        assert messages[1]["thinking"] == "Because it's a test"


class TestCreateMessagesWithoutReasoning:
    """Tests for message creation functions without reasoning."""

    def test_create_messages_without_reasoning(self):
        """Test message creation without reasoning."""
        record = {
            "document_outline": "Test Outline",
            "document": "Test Document",
            "question": "What is this?",
            "response": "This is a test",
        }
        messages = _create_messages_without_reasoning(record)

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["thinking"] == ""

    def test_create_messages_without_reasoning_no_document(self):
        """Test message creation without reasoning or document."""
        record = {
            "document_outline": "Test Outline",
            "question": "What is this?",
            "response": "This is a test",
        }
        messages = _create_messages_without_reasoning_no_document(record)

        assert len(messages) == 2
        assert "In Test Outline" in messages[0]["content"]
        assert messages[1]["thinking"] == ""


class TestGenerateKnowledgeQADataset:
    """Tests for generate_knowledge_qa_dataset function."""

    def test_basic_generation(self, sample_qa_dataframe):
        """Test basic dataset generation."""
        result = generate_knowledge_qa_dataset(sample_qa_dataframe)

        assert "messages" in result.columns
        assert "metadata" in result.columns
        assert "unmask" in result.columns
        assert len(result) == len(sample_qa_dataframe)

    def test_missing_required_columns(self):
        """Test that missing columns raise error."""
        df = pl.DataFrame({"question": ["Q1"], "response": ["A1"]})
        with pytest.raises(ValueError, match="Missing required columns"):
            generate_knowledge_qa_dataset(df)

    def test_metadata_structure(self, sample_qa_dataframe):
        """Test metadata JSON structure."""
        result = generate_knowledge_qa_dataset(sample_qa_dataframe)
        metadata = json.loads(result["metadata"][0])

        assert "sdg_document" in metadata
        assert "dataset" in metadata
        assert "raw_document" in metadata
        assert metadata["dataset"] == "document_knowledge_qa"

    def test_messages_structure(self, sample_qa_dataframe):
        """Test messages structure."""
        result = generate_knowledge_qa_dataset(sample_qa_dataframe)
        messages = result["messages"][0]

        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"

    def test_with_reasoning(self, sample_qa_dataframe_with_reasoning):
        """Test dataset generation with reasoning."""
        result = generate_knowledge_qa_dataset(sample_qa_dataframe_with_reasoning)
        messages = result["messages"][0]

        assert messages[1]["thinking"] is not None

    def test_pre_training_flag(self, sample_qa_dataframe):
        """Test pre_training flag sets unmask correctly."""
        result_pre = generate_knowledge_qa_dataset(
            sample_qa_dataframe, pre_training=True
        )
        result_no_pre = generate_knowledge_qa_dataset(
            sample_qa_dataframe, pre_training=False
        )

        assert all(result_pre["unmask"])
        assert not any(result_no_pre["unmask"])

    def test_keep_columns(self, sample_qa_dataframe):
        """Test that keep_columns preserves specified columns."""
        df_with_extra = sample_qa_dataframe.with_columns(
            pl.lit("extra_value").alias("extra_col")
        )
        result = generate_knowledge_qa_dataset(
            df_with_extra, keep_columns=["extra_col"]
        )

        assert "extra_col" in result.columns
        assert all(result["extra_col"] == "extra_value")

    def test_keep_document_in_context(self, sample_qa_dataframe):
        """Test keep_document_in_context flag."""
        result = generate_knowledge_qa_dataset(
            sample_qa_dataframe, keep_document_in_context=True
        )
        messages = result["messages"][0]

        # Document should be in user message
        assert sample_qa_dataframe["document"][0] in messages[0]["content"]


class TestCountLenInTokens:
    """Tests for count_len_in_tokens function."""

    def test_basic_token_counting(self):
        """Test basic token counting functionality."""
        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.return_value = "templated text"
        mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]

        df = pl.DataFrame({
            "messages": [
                [{"role": "user", "content": "Hello"}],
                [{"role": "assistant", "content": "Hi"}],
            ]
        })

        result = count_len_in_tokens(df, mock_tokenizer, column_name="messages")

        assert "token_length" in result.columns
        assert len(result) == 2
        assert all(result["token_length"] == 5)

    def test_missing_column(self):
        """Test error when column doesn't exist."""
        mock_tokenizer = MagicMock()
        df = pl.DataFrame({"other_col": [1, 2, 3]})

        with pytest.raises(ValueError, match="Column 'messages' not found"):
            count_len_in_tokens(df, mock_tokenizer)

    def test_custom_column_name(self):
        """Test with custom column name."""
        mock_tokenizer = MagicMock()
        mock_tokenizer.apply_chat_template.return_value = "text"
        mock_tokenizer.encode.return_value = [1, 2]

        df = pl.DataFrame({
            "custom_messages": [
                [{"role": "user", "content": "Test"}]
            ]
        })

        result = count_len_in_tokens(df, mock_tokenizer, column_name="custom_messages")
        assert "token_length" in result.columns
        assert result["token_length"][0] == 2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test functions with empty dataframe."""
        empty_df = pl.DataFrame({
            "question": [],
            "response": [],
            "document": [],
            "raw_document": [],
            "document_outline": [],
        })

        # Should not raise error
        result = generate_knowledge_qa_dataset(empty_df)
        assert len(result) == 0

    def test_special_characters_in_text(self):
        """Test handling of special characters."""
        df = pl.DataFrame({
            "question": ["What's the {answer}?"],
            "response": ["It's <complicated> & \"tricky\""],
            "document": ["doc1"],
            "raw_document": ["raw1"],
            "document_outline": ["outline"],
        })

        result = generate_knowledge_qa_dataset(df)
        assert len(result) == 1

    def test_very_long_text(self):
        """Test with very long text strings."""
        long_text = "A" * 10000
        df = pl.DataFrame({
            "question": [long_text],
            "response": [long_text],
            "document": ["doc1"],
            "raw_document": ["raw1"],
            "document_outline": ["outline"],
        })

        result = generate_knowledge_qa_dataset(df)
        assert len(result) == 1
