from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

vector = model.encode("Leave policy for employees")

print(len(vector))