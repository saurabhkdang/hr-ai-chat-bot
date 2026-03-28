from fastapi import FastAPI, HTTPException
from services.query import handle_query

app = FastAPI()

@app.post("/ask")
def ask(data: dict):
    
    try:
        user_query = data["question"]

        if not user_query.strip():
            return {
                "type": "text",
                "message": "Please enter a query"
            }
        
        response = handle_query(user_query)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================
# HEALTH CHECK
# =============================
@app.get("/")
def health():
    return {"status": "HR AI Chatbot running 🚀"}