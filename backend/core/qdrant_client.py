from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from backend.core.config import settings
import uuid
import os


class QdrantVectorDB:
    def __init__(self):
        qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.client = QdrantClient(host=qdrant_host, port=qdrant_port)

    def _ensure_collection(self, collection_name: str):
        if not self.client.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def add_chunks(self, collection_name: str, chunks: list[str], embeddings: list[list[float]], metadata: list[dict]):
        self._ensure_collection(collection_name)
        points = []
        for i, (chunk, vector, meta) in enumerate(zip(chunks, embeddings, metadata)):
            point_id = str(uuid.uuid4())
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"text": chunk, **meta}
                )
            )
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )

    def search(self, collection_name: str, query_vector: list[float], limit: int = 5):
        if not self.client.collection_exists(collection_name):
            return []
            
        response = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit
        )
        return response.points

    def get_collections(self) -> list[str]:
        response = self.client.get_collections()
        return [col.name for col in response.collections]
        
    def delete_collection(self, collection_name: str):
        if self.client.collection_exists(collection_name):
            self.client.delete_collection(collection_name)

qdrant_db = QdrantVectorDB()
