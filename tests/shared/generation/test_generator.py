import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))


def test_build_prompt_formats_context():
    with patch("shared.generation.generator.Config") as mock_config:
        mock_config.PROMPT = "Контекст: {context}\n\nВопрос: {query}"
        mock_config.MISTRAL_API_KEY = "test-key"
        mock_config.MISTRAL_MODEL = "test-model"
        mock_config.TEMPERATURE = 0.2
        mock_config.MAX_TOKENS = 500
        from shared.generation.generator import Generator
        gen = Generator()
        chunks = [{"text": "Чанк 1"}, {"text": "Чанк 2"}]
        prompt = gen.build_prompt("Какой вопрос?", chunks)
        assert "Чанк 1" in prompt
        assert "Чанк 2" in prompt
        assert "Какой вопрос?" in prompt


def test_generate_success():
    with patch("shared.generation.generator.requests") as mock_requests, \
         patch("shared.generation.generator.Config") as mock_config:
        mock_config.PROMPT = "Context: {context}\nQuery: {query}"
        mock_config.MISTRAL_API_KEY = "test-key"
        mock_config.MISTRAL_MODEL = "test-model"
        mock_config.TEMPERATURE = 0.2
        mock_config.MAX_TOKENS = 500
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Ответ от модели"}}]
        }
        mock_requests.post.return_value = mock_resp
        from shared.generation.generator import Generator
        gen = Generator()
        result = gen.generate("Вопрос?", [{"text": "Контекст"}])
        assert result == "Ответ от модели"
        mock_requests.post.assert_called_once()


def test_generate_api_error():
    with patch("shared.generation.generator.requests") as mock_requests, \
         patch("shared.generation.generator.Config") as mock_config:
        mock_config.PROMPT = "Context: {context}\nQuery: {query}"
        mock_config.MISTRAL_API_KEY = "test-key"
        mock_config.MISTRAL_MODEL = "test-model"
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Rate limit exceeded"
        mock_requests.post.return_value = mock_resp
        from shared.generation.generator import Generator
        gen = Generator()
        result = gen.generate("Вопрос?", [{"text": "Контекст"}])
        assert "error LLM" in result
        assert "429" in result or "Rate limit" in result
