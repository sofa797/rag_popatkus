from embeddings.embedder import Embedder
from vectorstore.qdrant_store import QdrantStore
from generation.generator import Generator
from utils.config import Config

class RAGPipeline:
    def __init__(self):
        self.embedder = Embedder()
        self.vector_store = QdrantStore(embedder=self.embedder)
        self.generator = Generator()

    def ask(self, query: str):
        top_chunks = self.vector_store.search(query, top_k=Config.FINAL_TOP_K)
        answer = self.generator.generate(query, top_chunks)
        return answer, top_chunks
