from utils.intent_service import detect_intent, detect_intent_structured_llm
from services.vector_service import handle_vector_query
from services.sql_service import handle_sql_query, build_schema_prompt, handle_sql
from services.hybrid import is_hybrid_query, handle_hybrid_query
from utils.parser import parse_query
from config.schema import ALLOWED_SCHEMA
from services.comparison import is_comparison_query, handle_comparison_query

def handle_query(user_query):
    parsed = parse_query(user_query)

    # if is_hybrid_query(parsed):
        # return handle_hybrid_query(parsed)
    
    # 🔥 STEP 0: Comparison check (TOP PRIORITY)
    # if is_comparison_query(user_query):
        # return handle_comparison_query(user_query)

    intent = detect_intent_structured_llm(parsed)
    print("INTENT : ", intent)
    if intent == "HYBRID":
        return handle_hybrid_query(parsed)
    elif intent == "SQL":
        # schema_prompt = build_schema_prompt(ALLOWED_SCHEMA)
        # return handle_sql_query(parsed, schema_prompt)
        return handle_sql(parsed)
    elif intent == "VECTOR":
        return handle_vector_query(parsed["raw"])

    return {
        "type": "text",
        "message": "Sorry, I couldn't understand your query."
    }