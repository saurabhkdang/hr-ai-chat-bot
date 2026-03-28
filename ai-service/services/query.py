from services.intent_service import detect_intent
from services.vector_service import handle_vector_query
from services.sql_service import handle_sql_query, build_schema_prompt
from services.hybrid import is_hybrid_query, handle_hybrid_query
from config.schema import ALLOWED_SCHEMA

def handle_query(user_query):
    if is_hybrid_query(user_query):
        return handle_hybrid_query(user_query)

    intent = detect_intent(user_query)
    print(intent)
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