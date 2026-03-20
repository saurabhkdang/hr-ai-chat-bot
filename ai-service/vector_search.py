from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from config import COLLECTION_NAME, QDRANT_HOST, QDRANT_PORT

model = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)

def search_docs(query, top_k=3):

    query_vector = model.encode(query).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k
    )

    return [r.payload["text"] for r in results.points]