import pytest
from unittest.mock import MagicMock, Mock, patch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

def test_embedder_has_expected_methods():
    with patch("shared.embeddings.embedder.Config"), \
         patch("shared.embeddings.embedder.AutoTokenizer"), \
         patch("shared.embeddings.embedder.AutoModel"), \
         patch("shared.embeddings.embedder.torch.cuda.is_available", return_value=False):
        from shared.embeddings.embedder import Embedder
        assert hasattr(Embedder, 'encode')
        assert hasattr(Embedder, '_mean_pooling')
        assert callable(getattr(Embedder, 'encode'))
        assert callable(getattr(Embedder, '_mean_pooling'))

def test_mean_pooling_signature():
    with patch("shared.embeddings.embedder.Config"), \
         patch("shared.embeddings.embedder.AutoTokenizer"), \
         patch("shared.embeddings.embedder.AutoModel"), \
         patch("shared.embeddings.embedder.torch.cuda.is_available", return_value=False):
        from shared.embeddings.embedder import Embedder
        import inspect
        sig = inspect.signature(Embedder._mean_pooling)
        params = list(sig.parameters.keys())
        assert 'model_output' in params
        assert 'attention_mask' in params
