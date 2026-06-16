# import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))


def test_pipeline_initializes_components():
    with patch("shared.pipeline.rag_pipeline.Embedder") as mock_emb, \
         patch("shared.pipeline.rag_pipeline.QdrantStore") as mock_vs, \
         patch("shared.pipeline.rag_pipeline.Generator") as mock_gen, \
         patch("shared.pipeline.rag_pipeline.Config") as mock_config:
        
        mock_config.FINAL_TOP_K = 5
        from shared.pipeline.rag_pipeline import RAGPipeline
        pipeline = RAGPipeline()
        mock_emb.assert_called_once()
        mock_vs.assert_called_once()
        mock_gen.assert_called_once()
        assert pipeline.embedder is not None
        assert pipeline.vector_store is not None
        assert pipeline.generator is not None


def test_ask_calls_search_and_generate(sample_chunks):
    with patch("shared.pipeline.rag_pipeline.Embedder"), \
         patch("shared.pipeline.rag_pipeline.QdrantStore") as mock_vs_cls, \
         patch("shared.pipeline.rag_pipeline.Generator") as mock_gen_cls, \
         patch("shared.pipeline.rag_pipeline.Config") as mock_config:
        
        mock_config.FINAL_TOP_K = 5
        mock_vs = MagicMock()
        mock_vs.search.return_value = sample_chunks
        mock_vs_cls.return_value = mock_vs
        mock_gen = MagicMock()
        mock_gen.generate.return_value = "Ответ от LLM"
        mock_gen_cls.return_value = mock_gen
        from shared.pipeline.rag_pipeline import RAGPipeline
        pipeline = RAGPipeline()
        answer, chunks = pipeline.ask("Тестовый вопрос?")
        mock_vs.search.assert_called_once_with("Тестовый вопрос?", top_k=5)
        mock_gen.generate.assert_called_once_with("Тестовый вопрос?", sample_chunks)
        assert answer == "Ответ от LLM"
        assert chunks == sample_chunks
