from langchain_community.llms import Ollama
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA

# ---- CONFIG ----
QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "hr_docs"

# ---- INIT ----
def get_rag_chain():
    
    # 1. Load embeddings (same as your existing)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # 2. Connect Qdrant (your existing DB)
    qdrant = Qdrant(
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        embedding=embeddings
    )

    # 3. Load LLM (Ollama - your current)
    llm = Ollama(model="phi")

    # 4. Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=qdrant.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

    return qa_chain