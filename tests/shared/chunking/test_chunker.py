import pytest
from shared.chunking.chunker import Chunker


def test_chunk_filters_types(sample_parsed_data):
    chunker = Chunker()
    result = chunker.chunk(sample_parsed_data)
    types = [c["metadata"]["type"] for c in result]
    assert "section" not in types
    assert set(types) == {"paragraph", "subparagraph", "definition"}


def test_chunk_preserves_metadata(sample_parsed_data):
    chunker = Chunker()
    result = chunker.chunk(sample_parsed_data)
    def_chunk = next(c for c in result if c["metadata"]["type"] == "definition")
    assert def_chunk["metadata"]["term"] == "Термин"
    assert def_chunk["metadata"]["page"] == 5
    para_chunk = next(c for c in result if c["metadata"]["type"] == "paragraph")
    assert para_chunk["metadata"]["section"] == "I"
    assert para_chunk["metadata"]["item"] == "1"


def test_chunk_empty_input():
    chunker = Chunker()
    assert chunker.chunk([]) == []


def test_chunk_text_field(sample_parsed_data):
    chunker = Chunker()
    result = chunker.chunk(sample_parsed_data)
    texts = [c["text"] for c in result]
    assert "Текст первого пункта" in texts
    assert "Термин – это определение" in texts
