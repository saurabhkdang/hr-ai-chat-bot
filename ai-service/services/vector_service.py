from vector_search import search_docs
from utils.llm import ask_ai
from utils.llm_service import call_llm
import re

def normalize_chunk(chunk):
    chunk = re.sub(r"\s+", " ", chunk).strip(" -•|:")

    if not chunk:
        return ""

    if chunk[0].islower() and not chunk.lower().startswith(("wfh", "work from home")):
        return ""

    return chunk

def clean_policy_text(text):
    text = re.sub(r"Interlynx Digital Solutions Private Limited \|.*?(?=(Work From Home|WFH|Request and Approval Process|$))", "", text, flags=re.IGNORECASE)
    text = re.sub(r"CIN:.*?(?=(Work From Home|WFH|Request and Approval Process|$))", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def build_extractive_answer(user_query, docs):
    cleaned_docs = [clean_policy_text(doc) for doc in docs]

    query_terms = {
        term for term in re.findall(r"[a-zA-Z]{3,}", user_query.lower())
        if term not in {"what", "with", "from", "that", "this", "your", "into", "about", "the", "and"}
    }
    scoring_terms = query_terms | {"approval", "approve", "approved", "process", "request", "manager", "recorded", "policy", "wfh"}

    text = "\n".join(cleaned_docs)
    raw_chunks = [
        segment.strip()
        for segment in re.split(r"\n+|[•●➢]|(?<=[.!?])\s+", text)
        if segment.strip()
    ]
    chunks = [chunk for chunk in (normalize_chunk(segment) for segment in raw_chunks) if chunk]

    if not chunks:
        return "Relevant documents were found, but a concise answer could not be generated."

    ranked_chunks = []
    seen = set()
    for chunk in chunks:
        normalized = chunk.strip()
        normalized_key = normalized.lower()
        if normalized_key in seen:
            continue

        seen.add(normalized_key)
        chunk_terms = set(re.findall(r"[a-zA-Z]{3,}", normalized.lower()))
        overlap = len(scoring_terms & chunk_terms)
        process_bonus = 0
        if any(term in normalized.lower() for term in ["approval", "approved in advance", "manager approval", "recorded", "request"]):
            process_bonus += 2

        ranked_chunks.append((overlap + process_bonus, len(normalized), normalized))

    ranked_chunks.sort(key=lambda item: (-item[0], item[1]))

    selected = [chunk for score, _, chunk in ranked_chunks if score > 1][:3]

    if not selected:
        selected = [chunk for _, _, chunk in ranked_chunks[:1]]

    concise_answer = " ".join(selected)
    concise_answer = re.sub(r"\s+", " ", concise_answer).strip()

    if len(concise_answer) > 320:
        concise_answer = concise_answer[:317].rstrip() + "..."

    return concise_answer

def handle_vector_query(user_query):
    try:
        print(user_query)
        
        if not user_query.strip():
            return {
                "type": "text",
                "message": "Please enter a query"
            }
        # Step 1: Search from vector DB (FAISS / Pinecone etc.)
        docs = search_docs(user_query)  # returns top matches

        if not docs:
            return {
                "type": "text",
                "message": "No relevant information found."
            }

        # Step 2: Combine context
        # context = "\n".join([d["text"] for d in docs[:3]])

        context = "\n".join(docs)

        # answer = generate_answer(user_query, context)

        # print("Context for LLM:", context)
        # Step 3: Ask LLM
        summary = call_llm(f"""
        Answer the question based on the context below.

        Question:
        {user_query}

        Context:
        {context}

        Give a clear and concise answer.
        """)

        if not summary:
            summary = build_extractive_answer(user_query, docs)

        return {
            "type": "text",
            "message": summary
        }

    except Exception as e:
        return {
            "type": "text",
            "message": f"Error processing request: {str(e)}"
        }