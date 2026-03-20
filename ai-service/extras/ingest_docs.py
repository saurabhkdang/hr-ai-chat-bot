from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Connect to Qdrant
client = QdrantClient("localhost", port=6333)

import os

# -------- Chunking function --------
def split_text(text, chunk_size=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../docs'))
pdf_files = [f for f in os.listdir(docs_dir) if f.lower().endswith('.pdf')]

all_points = []

for filename in pdf_files:
    filepath = os.path.join(docs_dir, filename)
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    except Exception as e:
        print(f"Error reading PDF {filename}: {e}")
        continue

    chunks = split_text(text)
    print(f"{filename}: {len(chunks)} chunks")

    for chunk in chunks:
        embedding = model.encode(chunk)
        all_points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding.tolist(),
                payload={
                    "text": chunk,
                    "source": filename
                }
            )
        )

# Upload to Qdrant
client.upsert(
    collection_name="hr_docs",
    points=all_points
)

print("All PDFs indexed successfully")

""" for chunk in chunks:

    embedding = model.encode(chunk)

    points.append(
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding.tolist(),
            payload={
                "text": chunk,
                "source": "wfh.pdf"
            }
        )
    )

# Upload to Qdrant
client.upsert(
    collection_name="hr_docs",
    points=points
)

print("PDF indexed successfully") """
