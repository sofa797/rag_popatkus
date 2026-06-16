import sys
from pathlib import Path
from typing import Optional
from shared.pipeline.rag_pipeline import RAGPipeline


project_root = Path(__file__).resolve().parent.parent.parent.parent
shared_path = project_root / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class RAGService:
    def __init__(self):
        self._pipeline: Optional[RAGPipeline] = None
    
    def _get_pipeline(self) -> RAGPipeline:
        if self._pipeline is None:
            self._pipeline = RAGPipeline()
        return self._pipeline
    
    def ask(self, query: str):
        top_chunks = self._get_pipeline().vector_store.search(query, top_k=5)
        
        # for i, chunk in enumerate(top_chunks[:3]):
        #    text_preview = chunk['text'][:150].replace('\n', ' ')
        #   meta = chunk.get('metadata', {})

        answer, chunks = self._get_pipeline().ask(query)
        return answer, chunks

rag_service = RAGService()
