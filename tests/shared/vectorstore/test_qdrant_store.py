import pytest
from unittest.mock import MagicMock, patch, Mock
import uuid as uuid_module
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))


@pytest.fixture
def mock_qdrant_modules():
    with patch("shared.vectorstore.qdrant_store.QdrantClient") as mock_client_cls, \
         patch("shared.vectorstore.qdrant_store.PointStruct") as mock_point_cls, \
         patch("shared.vectorstore.qdrant_store.Distance") as mock_distance, \
         patch("shared.vectorstore.qdrant_store.VectorParams") as mock_vector_params:
        
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        
        mock_collections_response = MagicMock()
        mock_collections_response.collections = []
        mock_client.get_collections.return_value = mock_collections_response
        
        mock_search_response = MagicMock()
        mock_point = MagicMock()
        mock_point.payload = {"text": "Тестовый чанк", "metadata": {"page": 1, "section": "1.1"}}
        mock_search_response.points = [mock_point]
        mock_client.query_points.return_value = mock_search_response
        
        mock_point_cls.side_effect = lambda id, vector, payload: Mock(id=id, vector=vector, payload=payload)
        yield {
            "client_cls": mock_client_cls,
            "client": mock_client,
            "point_cls": mock_point_cls,
            "distance": mock_distance,
            "vector_params": mock_vector_params
        }


def test_ensure_collection_creates_if_missing(mock_qdrant_modules):
    with patch("shared.vectorstore.qdrant_store.Config") as mock_config:
        mock_config.QDRANT_PATH = "./test_qdrant_tmp"
        mock_config.COLLECTION_NAME = "test_collection"
        mock_config.EMBEDDING_DIM = 768
        
        from shared.vectorstore.qdrant_store import QdrantStore

        mock_embedder = MagicMock()
        # store = QdrantStore(embedder=mock_embedder)
        mock_qdrant_modules["client"].create_collection.assert_called_once()
        call_kwargs = mock_qdrant_modules["client"].create_collection.call_args[1]
        assert call_kwargs["collection_name"] == "test_collection"


def test_add_documents_calls_upload(mock_qdrant_modules, sample_chunks):
    with patch("shared.vectorstore.qdrant_store.Config") as mock_config, \
         patch("shared.vectorstore.qdrant_store.uuid") as mock_uuid:
        
        mock_config.QDRANT_PATH = "./test_tmp"
        mock_config.COLLECTION_NAME = "test_collection"
        mock_uuid.uuid4.return_value = uuid_module.UUID("12345678-1234-5678-1234-567812345678")
        mock_embedder = MagicMock()
        mock_embedder.encode.return_value = [[0.1] * 768] * len(sample_chunks)
        from shared.vectorstore.qdrant_store import QdrantStore
        store = QdrantStore(embedder=mock_embedder)
        store.add_documents(sample_chunks)
        mock_qdrant_modules["client"].upload_points.assert_called_once()
        call_args = mock_qdrant_modules["client"].upload_points.call_args
        assert call_args[1]["collection_name"] == "test_collection"
        assert len(call_args[1]["points"]) == len(sample_chunks)


def test_search_returns_chunks(mock_qdrant_modules):
    with patch("shared.vectorstore.qdrant_store.Config") as mock_config:
        mock_config.QDRANT_PATH = "./test_tmp_search"
        mock_config.COLLECTION_NAME = "test_collection"
        mock_embedder = MagicMock()
        mock_embedder.encode.return_value = [[0.1] * 768]
        from shared.vectorstore.qdrant_store import QdrantStore
        store = QdrantStore(embedder=mock_embedder)
        results = store.search("тестовый запрос", top_k=3)
        assert len(results) == 1
        assert "text" in results[0]
        assert "metadata" in results[0]
        assert results[0]["metadata"]["page"] == 1


def test_clear_collection_recreates(mock_qdrant_modules):
    with patch("shared.vectorstore.qdrant_store.Config") as mock_config:
        mock_config.QDRANT_PATH = "./test_tmp_clear"
        mock_config.COLLECTION_NAME = "test_collection"
        mock_config.EMBEDDING_DIM = 768
        mock_embedder = MagicMock()
        from shared.vectorstore.qdrant_store import QdrantStore
        store = QdrantStore(embedder=mock_embedder)
        store.clear_collection()
        mock_qdrant_modules["client"].delete_collection.assert_called_once()
        assert mock_qdrant_modules["client"].create_collection.called
