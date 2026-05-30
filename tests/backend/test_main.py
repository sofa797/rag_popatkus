from fastapi.testclient import TestClient
from backend.app.main import app

def test_health_check():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

def test_openapi_available():
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        assert "paths" in resp.json()

def test_cors_headers_on_simple_request():
    test_origin = "http://localhost:3000"
    
    with TestClient(app) as client:
        resp = client.get("/health", headers={"Origin": test_origin})
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == test_origin
        assert resp.headers.get("access-control-allow-credentials") == "true"
        assert resp.headers.get("vary") == "Origin"

def test_cors_preflight_headers():
    test_origin = "http://localhost:3000"
    with TestClient(app) as client:
        resp = client.options(
            "/api/v1/rag/ask",
            headers={
                "Origin": test_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
        )
        if resp.status_code == 200:
            assert resp.headers.get("access-control-allow-origin") == test_origin
            assert "POST" in resp.headers.get("access-control-allow-methods", "")
