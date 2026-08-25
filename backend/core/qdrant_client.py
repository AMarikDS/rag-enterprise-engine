from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from backend.core.config import settings
import uuid
import os


class QdrantVectorDB:
    def __init__(self):
        self.collection_name = settings.qdrant_collection_name
        # Используем локальное хранилище вместо Docker
        db_path = os.path.join(os.getcwd(), "data", "qdrant_storage")
        self.client = QdrantClient(path=db_path)
        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def add_chunks(self, chunks: list[str], embeddings: list[list[float]], metadata: list[dict]):
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
            collection_name=self.collection_name,
            points=points
        )

    def search(self, query_vector: list[float], limit: int = 5):
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit
        )
        return response.points

    def get_collection_info(self):
        if self.client.collection_exists(self.collection_name):
            return self.client.get_collection(self.collection_name)
        return None

qdrant_db = QdrantVectorDB()
