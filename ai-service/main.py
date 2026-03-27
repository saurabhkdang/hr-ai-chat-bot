from fastapi import FastAPI, HTTPException
# from utility import handle_query
from services.intent_service import detect_intent
from services.vector_service import handle_vector_query
from services.sql_service import handle_sql_query, build_schema_prompt
from config.schema import ALLOWED_SCHEMA

app = FastAPI()

@app.post("/ask")
def ask(data: dict):
    
    try:
        user_query = data["question"]
        # response = handle_query(question)
        intent = detect_intent(user_query)

        if intent == "SQL":
            schema_prompt = build_schema_prompt(ALLOWED_SCHEMA)
            response = handle_sql_query(user_query, schema_prompt)

        elif intent == "VECTOR":
            response = handle_vector_query(user_query)

        else:
            response = {
                "type": "text",
                "message": "Sorry, I couldn't understand your query."
            }
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================
# HEALTH CHECK
# =============================
@app.get("/")
def health():
    return {"status": "HR AI Chatbot running 🚀"}