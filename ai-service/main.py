from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.query import handle_query

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://rapidly-approved-regarded-layer.trycloudflare.com/",
        "https://rapidly-approved-regarded-layer.trycloudflare.com",
        "https://hrdb.interlynxsystems.com"
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
