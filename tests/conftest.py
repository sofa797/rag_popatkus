import sys
from unittest.mock import MagicMock
if "gradio" not in sys.modules:
    mock_gradio = MagicMock()
    mock_gradio.Blocks = MagicMock
    mock_gradio.State = MagicMock
    mock_gradio.Chatbot = MagicMock
    mock_gradio.Textbox = MagicMock
    mock_gradio.Button = MagicMock
    mock_gradio.Row = MagicMock
    mock_gradio.Column = MagicMock
    mock_gradio.Group = MagicMock
    mock_gradio.Markdown = MagicMock
    mock_gradio.HTML = MagicMock
    sys.modules["gradio"] = mock_gradio

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


@pytest.fixture
def mock_requests_success():
    with patch("frontend.gradio_app.requests") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}
        mock_resp.text = ""
        mock_req.get.return_value = mock_resp
        mock_req.post.return_value = mock_resp
        yield mock_req


@pytest.fixture
def mock_requests_auth():
    with patch("frontend.gradio_app.requests") as mock_req:
        def mock_post(url, json=None, headers=None, **kwargs):
            resp = MagicMock()
            if "/auth/login" in url and json and json.get("password") == "valid_pass":
                resp.status_code = 200
                resp.json.return_value = {"access_token": "test_token_123"}
            elif "/auth/register" in url:
                resp.status_code = 201
                resp.json.return_value = {"message": "User created"}
            else:
                resp.status_code = 401
                resp.json.return_value = {"detail": "Invalid credentials"}
            return resp
        
        def mock_get(url, headers=None, **kwargs):
            resp = MagicMock()
            if "/rag/history" in url and headers and "Bearer test_token_123" in headers.get("Authorization", ""):
                resp.status_code = 200
                resp.json.return_value = [
                    {"id": 1, "query": "Как оформить заявку?", "answer": "Ответ 1", "created_at": "2024-01-01T00:00:00"},
                    {"id": 2, "query": "Срок действия?", "answer": "Ответ 2", "created_at": "2024-01-02T00:00:00"}
                ]
            else:
                resp.status_code = 401
                resp.json.return_value = {"detail": "Unauthorized"}
            return resp
        mock_req.post.side_effect = mock_post
        mock_req.get.side_effect = mock_get
        yield mock_req


@pytest.fixture
def mock_requests_error():
    with patch("frontend.gradio_app.requests") as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.json.return_value = {"detail": "Internal error"}
        mock_resp.text = "Internal Server Error"
        mock_resp.raise_for_status.side_effect = Exception("HTTP 500")
        mock_req.get.return_value = mock_resp
        mock_req.post.return_value = mock_resp
        yield mock_req


@pytest.fixture
def mock_requests_rag_response():
    with patch("frontend.gradio_app.requests.post") as mock_post:
        def _mock_rag(url, json=None, headers=None, **kwargs):
            resp = MagicMock()
            if "/rag/ask" in url and headers and "Bearer" in headers.get("Authorization", ""):
                resp.status_code = 200
                resp.json.return_value = {
                    "answer": "Согласно Положению «Попаткус», пункт 3.1, допускается оформление заявки через личный кабинет.",
                    "sources": [
                        {
                            "text": "Пункт 3.1. Заявка подаётся пользователем через веб-интерфейс после авторизации",
                            "metadata": {"page": 5, "section": "3.1", "source": "popatkus.pdf"}
                        },
                        {
                            "text": "Пункт 3.2. Срок рассмотрения заявки составляет не более 5 рабочих дней",
                            "metadata": {"page": 6, "section": "3.2", "source": "popatkus.pdf"}
                        }
                    ]
                }
            else:
                resp.status_code = 401
                resp.json.return_value = {"detail": "Unauthorized"}
            return resp
        mock_post.side_effect = _mock_rag
        yield mock_post


@pytest.fixture
def frontend_test_data():
    return {
        "valid_email": "user@example.com",
        "valid_password": "SecurePass123!",
        "invalid_email": "not-an-email",
        "weak_password": "123",
        "test_query": "Как оформить заявку?",
        "test_answer": "Согласно Положению, заявка подаётся через личный кабинет.",
        "test_token": "test_token_123"
    }



@pytest.fixture
def mock_torch():
    """Мок для torch и torch.nn.functional"""
    with patch("torch.cuda.is_available") as mock_cuda, \
         patch("torch.nn.functional.normalize") as mock_norm, \
         patch("torch.no_grad") as mock_no_grad, \
         patch("torch.sum") as mock_sum, \
         patch("torch.clamp") as mock_clamp:
        
        mock_cuda.return_value = False
        mock_norm.side_effect = lambda x, **kw: x
        mock_no_grad.return_value.__enter__ = MagicMock()
        mock_no_grad.return_value.__exit__ = MagicMock()
        mock_sum.return_value = MagicMock()
        mock_clamp.return_value = MagicMock()
        mock_tensor = MagicMock()
        mock_tensor.unsqueeze.return_value = mock_tensor
        mock_tensor.expand.return_value = mock_tensor
        mock_tensor.float.return_value = mock_tensor
        mock_tensor.size.return_value = (1, 10, 768)
        mock_tensor.cpu.return_value = mock_tensor
        mock_tensor.numpy.return_value = [[0.1] * 768]
        with patch("torch.tensor", return_value=mock_tensor):
            yield {"tensor": mock_tensor, "norm": mock_norm}


@pytest.fixture
def mock_transformers():
    with patch("transformers.AutoTokenizer") as mock_tok, \
         patch("transformers.AutoModel") as mock_model:
        mock_tokenizer = MagicMock()
        mock_tokenizer.return_value = {
            "input_ids": MagicMock(),
            "attention_mask": MagicMock()
        }
        mock_tokenizer.return_value.to = MagicMock(return_value=mock_tokenizer.return_value)
        mock_tok.from_pretrained.return_value = mock_tokenizer
        mock_model_instance = MagicMock()
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.eval.return_value = mock_model_instance
        mock_model_instance.return_value = [MagicMock()]
        mock_model.from_pretrained.return_value = mock_model_instance
        
        yield {"tokenizer": mock_tokenizer, "model": mock_model_instance}


@pytest.fixture
def mock_qdrant_client():
    with patch("qdrant_client.QdrantClient") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        mock_instance.get_collections.return_value = MagicMock(
            collections=[]
        )
        mock_instance.create_collection = MagicMock()
        mock_instance.upload_points = MagicMock()
        mock_instance.query_points.return_value = MagicMock(
            points=[
                MagicMock(
                    payload={
                        "text": "Тестовый чанк",
                        "metadata": {"page": 1, "section": "1.1"}
                    }
                )
            ]
        )
        mock_instance.delete_collection = MagicMock()
        yield mock_instance


@pytest.fixture
def mock_pdfplumber():
    with patch("pdfplumber.open") as mock_open:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "I. Раздел один\n1. Пункт первый – определение"
        mock_page.page_number = 1
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_pdf.__exit__.return_value = None
        mock_open.return_value = mock_pdf
        
        yield mock_open


@pytest.fixture
def sample_parsed_data():
    return [
        {
            "type": "paragraph",
            "section": "I",
            "section_title": "Общие положения",
            "item": "1",
            "subitem": None,
            "text": "Текст первого пункта",
            "page": 3
        },
        {
            "type": "subparagraph",
            "section": "I",
            "section_title": "Общие положения", 
            "item": "1",
            "subitem": "1.1",
            "text": "Текст подпункта",
            "page": 3
        },
        {
            "type": "definition",
            "term": "Термин",
            "text": "Термин – это определение",
            "page": 5
        },
        {
            "type": "section",
            "section": "II",
            "text": "Заголовок раздела",
            "page": 10
        }
    ]


@pytest.fixture
def sample_chunks():
    return [
        {
            "text": "Текст чанка 1",
            "metadata": {"page": 1, "section": "1.1", "type": "paragraph"}
        },
        {
            "text": "Текст чанка 2", 
            "metadata": {"page": 2, "section": "1.2", "type": "subparagraph"}
        }
    ]
