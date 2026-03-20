from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient("localhost", port=6333)

query = "wfh approval?"

vector = model.encode(query).tolist()

hits = client.query_points(
    collection_name="hr_docs",
    query=vector,
    limit=3
)

for hit in hits.points:
    print(hit.payload["text"])