import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from shared.embeddings.embedder import Embedder
from shared.utils.config import Config

class QdrantStore:
    def __init__(self, embedder=None):
        self.client = QdrantClient(path=Config.QDRANT_PATH)
        if embedder is not None:
            self.embedder = embedder
        else:
            self.embedder = Embedder()
        self._ensure_collection()

    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        exists = any(c.name == Config.COLLECTION_NAME for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=Config.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=Config.EMBEDDING_DIM, 
                    distance=Distance.COSINE
                ),
            )

    def add_documents(self, chunks):
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.encode(texts, is_query=False)
        points = []
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": chunk["text"],
                        "metadata": chunk["metadata"]
                    }
                )
            )
            
        self.client.upload_points(
            collection_name=Config.COLLECTION_NAME, 
            points=points, 
            wait=True
        )

    def search(self, query, top_k=5):
        query_vector = self.embedder.encode([query], is_query=True)[0]
        search_results = self.client.query_points(
            collection_name=Config.COLLECTION_NAME,
            query=query_vector,
            limit=top_k
        )
        
        retrieved_chunks = []
        for point in search_results.points:
            retrieved_chunks.append({
                "text": point.payload["text"],
                "metadata": point.payload["metadata"]
            })
        return retrieved_chunks

    def clear_collection(self):
        self.client.delete_collection(collection_name=Config.COLLECTION_NAME)
        self._ensure_collection()
