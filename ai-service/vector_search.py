from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from config.schema import COLLECTION_NAME, QDRANT_HOST, QDRANT_PORT
import re

client = QdrantClient(QDRANT_HOST, port=QDRANT_PORT)
model = None
MIN_RELEVANCE_SCORE = 0.25

def extract_query_terms(query):
    return {
        term for term in re.findall(r"[a-zA-Z]{3,}", query.lower())
        if term not in {"the", "and", "for", "with", "from", "that", "this", "are"}
    }

def rank_document(query, point):
    payload = point.payload or {}
    text = payload.get("text", "") or ""
    text_terms = set(re.findall(r"[a-zA-Z]{3,}", text.lower()))
    query_terms = extract_query_terms(query)
    overlap = len(query_terms & text_terms)

    phrase_bonus = 0
    lowered = text.lower()
    for phrase in ["work from home", "wfh", "approval", "request", "process", "manager approval"]:
        if phrase in lowered:
            phrase_bonus += 1

    vector_score = getattr(point, "score", 0) or 0
    return (overlap + phrase_bonus, vector_score, text)

def get_embedding_model():
    global model

    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")

    return model

def search_docs(query, top_k=3, min_score=MIN_RELEVANCE_SCORE):
    query_vector = get_embedding_model().encode(query).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=max(top_k, 8)
    )

    ranked_points = []
    for point in results.points:
        payload = point.payload or {}
        text = payload.get("text")
        if not text:
            continue

        keyword_score, vector_score, text = rank_document(query, point)
        if vector_score < min_score and keyword_score == 0:
            continue

        ranked_points.append((keyword_score, vector_score, text))

    ranked_points.sort(key=lambda item: (-item[0], -item[1], len(item[2])))

    if ranked_points:
        best_keyword_score = ranked_points[0][0]
        if best_keyword_score >= 2:
            ranked_points = [item for item in ranked_points if item[0] >= 2]

    selected = []
    seen = set()
    for _, _, text in ranked_points:
        normalized = re.sub(r"\s+", " ", text).strip().lower()
        if normalized in seen:
            continue

        seen.add(normalized)
        selected.append(text)

        if len(selected) == top_k:
            break

    return selected