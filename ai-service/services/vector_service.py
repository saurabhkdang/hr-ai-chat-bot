from vector_search import search_docs
from utils.llm import ask_ai

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
        summary = ask_ai(f"""
        Answer the question based on the context below.

        Question:
        {user_query}

        Context:
        {context}

        Give a clear and concise answer.
        """)

        return {
            "type": "text",
            "message": summary
        }

    except Exception as e:
        return {
            "type": "text",
            "message": f"Error processing request: {str(e)}"
        }