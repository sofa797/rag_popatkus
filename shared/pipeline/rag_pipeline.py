from shared.embeddings.embedder import Embedder
from shared.vectorstore.qdrant_store import QdrantStore
from shared.generation.generator import Generator
from shared.utils.config import Config

class RAGPipeline:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = QdrantStore(embedder=self.embedder)
        self.generator = Generator()

    def ask(self, query: str):
        top_chunks = self.vector_store.search(query, top_k=Config.FINAL_TOP_K)
        answer = self.generator.generate(query, top_chunks)
        return answer, top_chunks
