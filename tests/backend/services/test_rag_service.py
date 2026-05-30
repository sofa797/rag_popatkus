import pytest
from unittest.mock import MagicMock
from backend.app.services.rag_service import RAGService


@pytest.fixture
def fresh_rag_service():
    return RAGService()


def test_ask_calls_pipeline(fresh_rag_service, mocker):
    mock_pipeline = mocker.patch("backend.app.services.rag_service.RAGPipeline")
    mock_instance = MagicMock()
    mock_pipeline.return_value = mock_instance
    mock_instance.vector_store.search.return_value = [
        {"text": "Тест", "metadata": {"page": 1}}
    ]
    mock_instance.ask.return_value = ("Ответ", [{"text": "Тест", "metadata": {"page": 1}}])
    answer, sources = fresh_rag_service.ask("Тестовый вопрос?")
    mock_pipeline.assert_called_once()
    mock_instance.vector_store.search.assert_called_once_with("Тестовый вопрос?", top_k=5)
    mock_instance.ask.assert_called_once_with("Тестовый вопрос?")
    assert isinstance(answer, str)
    assert isinstance(sources, list)


def test_pipeline_cached(fresh_rag_service, mocker):
    mock_pipeline = mocker.patch("backend.app.services.rag_service.RAGPipeline")
    mock_instance = MagicMock()
    mock_pipeline.return_value = mock_instance
    pipeline1 = fresh_rag_service._get_pipeline()
    pipeline2 = fresh_rag_service._get_pipeline()
    assert pipeline1 is pipeline2
    mock_pipeline.assert_called_once()


def test_ask_handles_empty_results(fresh_rag_service, mocker):
    mock_pipeline = mocker.patch("backend.app.services.rag_service.RAGPipeline")
    mock_instance = MagicMock()
    mock_pipeline.return_value = mock_instance
    mock_instance.vector_store.search.return_value = []
    mock_instance.ask.return_value = ("Нет информации", [])
    answer, sources = fresh_rag_service.ask("Невозможный вопрос?")
    assert answer == "Нет информации"
    assert sources == []
