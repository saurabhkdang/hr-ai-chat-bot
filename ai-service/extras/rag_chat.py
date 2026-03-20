import ollama
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

model = SentenceTransformer('all-MiniLM-L6-v2')
client = QdrantClient("localhost", port=6333)

query = input("Ask HR question: ")


vector = model.encode(query).tolist()

results = client.query_points(
    collection_name="hr_docs",
    query=vector,
    limit=3
)

context = "\n".join([r.payload["text"] for r in results.points])

prompt = f"""
Use the context to give the short answer in one line to the question.

Context:
{context}

Question:
{query}
"""

response = ollama.chat(
    model='phi',
    messages=[{"role": "user", "content": prompt}]
)

print(response['message']['content'])