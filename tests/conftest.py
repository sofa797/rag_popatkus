import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.core.config import settings

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    Path("test.db").unlink(missing_ok=True)

@pytest.fixture
def db_session():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    def override_get_db():
        try:
            yield session
        finally:
            session.close()
    app.dependency_overrides[get_db] = override_get_db
    yield session
    transaction.rollback()
    connection.close()
    app.dependency_overrides.clear()

@pytest.fixture
def mock_rag_pipeline_class():
    with patch("backend.app.services.rag_service.RAGPipeline") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.vector_store.search.return_value = [
            {"text": "Тестовый чанк из Положения", "metadata": {"page": 3, "section": "2.1"}}
        ]
        mock_instance.ask.return_value = (
            "Согласно Положению «Попаткус», пункт 2.1, допускается...",
            [{"text": "Тестовый чанк", "metadata": {"page": 3}}]
        )
        mock_cls.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_rag_service_ask():
    with patch("backend.app.services.rag_service.rag_service.ask") as mock_ask:
        mock_ask.return_value = (
            "Согласно Положению «Попаткус», пункт 2.1, допускается",
            [{"text": "Тестовый чанк", "metadata": {"page": 3, "section": "2.1"}}]
        )
        yield mock_ask

@pytest.fixture
def client(db_session, mock_rag_service_ask):
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_user_data():
    return {"email": "test@example.com", "password": "SecurePass123!"}

@pytest.fixture
def auth_token(client, test_user_data):
    client.post("/api/v1/auth/register", json=test_user_data)
    resp = client.post("/api/v1/auth/login", json=test_user_data)
    return resp.json()["access_token"]
