# import pytest
from fastapi import status

def test_ask_question_authenticated(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post("/api/v1/rag/ask", json={"query": "Как оформить заявку?"}, headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)
    assert "Попаткус" in data["answer"]

def test_ask_question_unauthenticated(client):
    resp = client.post("/api/v1/rag/ask", json={"query": "Тест"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

def test_ask_question_empty_query(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post("/api/v1/rag/ask", json={"query": ""}, headers=headers)
    assert resp.status_code in (status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_CONTENT)

def test_get_history_authenticated(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    client.post("/api/v1/rag/ask", json={"query": "Тестовый вопрос"}, headers=headers)
    resp = client.get("/api/v1/rag/history", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, list)
    if data:
        assert "id" in data[0]
        assert "query" in data[0]
        assert "answer" in data[0]

def test_get_history_unauthenticated(client):
    resp = client.get("/api/v1/rag/history")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

def test_ask_question_rag_error(client, auth_token, mock_rag_service_ask):
    mock_rag_service_ask.side_effect = RuntimeError("Pipeline error")
    headers = {"Authorization": f"Bearer {auth_token}"}
    resp = client.post("/api/v1/rag/ask", json={"query": "Тест"}, headers=headers)
    assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Pipeline error" in resp.json()["detail"]
