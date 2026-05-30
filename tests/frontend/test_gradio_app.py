import pytest
import frontend.gradio_app as app
from unittest.mock import patch, MagicMock


def test_handle_register_success(mock_requests_success):
    result = app.handle_register("new@example.com", "SecurePass123!")
    assert isinstance(result, str)


def test_handle_login_success(mock_requests_auth, frontend_test_data):
    success, token = app.handle_login(
        frontend_test_data["valid_email"], 
        "valid_pass"
    )
    assert success is True
    assert token == frontend_test_data["test_token"]


def test_handle_login_invalid_password(mock_requests_auth):
    success, token = app.handle_login("user@example.com", "wrong_pass")
    assert success is False
    assert token is None

def test_fetch_history_queries_with_token(mock_requests_auth, frontend_test_data):
    queries = app.fetch_history_queries(frontend_test_data["test_token"])
    assert isinstance(queries, list)
    assert "Как оформить заявку?" in queries


def test_fetch_history_queries_no_token():
    queries = app.fetch_history_queries(None)
    assert queries == []


def test_format_history_html_empty():
    html = app.format_history_html([])
    assert "history-empty" in html
    assert "История пуста" in html


def test_format_history_html_with_items():
    queries = ["Первый вопрос", "Второй вопрос с очень длинным текстом" * 10]
    html = app.format_history_html(queries)
    
    assert "history-container" in html
    assert "history-item" in html
    html_xss = app.format_history_html(["<script>alert('xss')</script>"])
    assert "&lt;script&gt;" in html_xss


def test_user_message_normal():
    message = "Привет, как дела?"
    history = []
    new_msg, new_history = app.user_message(message, history)
    assert new_msg == ""
    assert len(new_history) == 1
    assert new_history[0]["role"] == "user"


def test_bot_response_no_token():
    history = [{"role": "user", "content": "Вопрос"}]
    new_history, _ = app.bot_response(history, token=None, history_html="")
    assert len(new_history) == 2
    assert new_history[-1]["role"] == "assistant"
    assert "enter" in new_history[-1]["content"].lower() or "авториз" in new_history[-1]["content"].lower()


def test_bot_response_success(mock_requests_rag_response, frontend_test_data):
    history = [{"role": "user", "content": frontend_test_data["test_query"]}]
    new_history, new_html = app.bot_response(
        history, 
        token=frontend_test_data["test_token"], 
        history_html=""
    )
    assert len(new_history) == 2
    assert new_history[-1]["role"] == "assistant"
    assert "Согласно Положению" in new_history[-1]["content"]
    assert "**Страница:** 5" in new_history[-1]["content"]
    assert "**Раздел:** 3.1" in new_history[-1]["content"]


def test_bot_response_api_error(mock_requests_error, frontend_test_data):
    history = [{"role": "user", "content": "Вопрос"}]
    new_history, _ = app.bot_response(
        history, 
        token=frontend_test_data["test_token"], 
        history_html=""
    )
    assert len(new_history) == 2
    assert "error" in new_history[-1]["content"].lower()


def test_clear_chat():
    chat, txt = app.clear_chat()
    assert chat == []
    assert txt == ""


def test_toggle_sidebar():
    _, new_state = app.toggle_sidebar(True)
    assert new_state is False
    _, new_state2 = app.toggle_sidebar(False)
    assert new_state2 is True
