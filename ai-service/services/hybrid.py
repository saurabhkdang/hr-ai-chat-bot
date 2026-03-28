from services.sql_service import handle_sql_query, build_schema_prompt
from services.vector_service import handle_vector_query
from config.schema import ALLOWED_SCHEMA

def is_hybrid_query(query):
    q = query.lower()

    sql_keywords = ["leave", "salary", "attendance", "employee"]
    vector_keywords = ["policy", "rule", "process", "how"]

    has_sql = any(k in q for k in sql_keywords)
    has_vector = any(k in q for k in vector_keywords)

    return has_sql and has_vector

def handle_hybrid_query(user_query):
    try:
        # 1. Split query
        sql_part, vector_part = split_hybrid_query(user_query)

        # 2. Process SQL
        schema_prompt = build_schema_prompt(ALLOWED_SCHEMA)
        sql_result = handle_sql_query(sql_part, schema_prompt)

        # 3. Process Vector
        vector_result = None
        if vector_part:
            vector_result = handle_vector_query(vector_part)

        # 4. Merge results
        return merge_hybrid_response(sql_result, vector_result, user_query)

    except Exception as e:
        return {
            "type": "text",
            "message": f"Hybrid Error: {str(e)}"
        }

def split_hybrid_query(query):
    query = query.lower()

    if " and " in query:
        parts = query.split(" and ")

        sql_part = ""
        vector_part = ""

        for p in parts:
            if any(k in p for k in ["policy", "rules", "how", "why"]):
                vector_part += p + " "
            else:
                sql_part += p + " "

        return sql_part.strip(), vector_part.strip()

    return query, None

def merge_hybrid_response(sql_res, vector_res, user_query):
    if not sql_res:
        return vector_res

    if not vector_res:
        return sql_res

    merged = dict(sql_res)

    insight_type = get_dynamic_key(user_query)

    insight = {
        "type": insight_type,
        "label": insight_type.capitalize(),
        "content": vector_res.get("message", "")
    }

    # attach safely
    merged.setdefault("insights", []).append(insight)

    return merged

def rule_based_key(query: str):
    q = query.lower()

    # 🎯 POLICY / RULES
    if any(word in q for word in ["policy", "policies"]):
        return "policy"

    if any(word in q for word in ["rule", "rules", "guideline", "guidelines"]):
        return "rules"

    # 🎯 REASON / WHY
    if any(word in q for word in ["why", "reason", "cause"]):
        return "reason"

    # 🎯 PROCESS / HOW
    if any(word in q for word in ["how", "process", "procedure", "steps"]):
        return "process"

    # 🎯 ELIGIBILITY / CRITERIA
    if any(word in q for word in ["eligible", "eligibility", "criteria"]):
        return "eligibility"

    # 🎯 BENEFITS / ENTITLEMENTS
    if any(word in q for word in ["benefit", "benefits", "entitlement", "entitlements"]):
        return "benefits"

    # 🎯 DEFINITION / MEANING
    if any(word in q for word in ["what is", "define", "meaning"]):
        return "definition"

    # 🎯 SUMMARY / EXPLANATION
    if any(word in q for word in ["explain", "summary", "details", "about"]):
        return "explanation"

    # 🎯 DEFAULT FALLBACK
    return None

def get_dynamic_key(query):
    key = rule_based_key(query)
    if key:
        return key

    return generate_dynamic_key(query)

def generate_dynamic_key(user_query):
    prompt = f"""
    Generate a short JSON key name (1-2 words) for the below query.

    Examples:
    - "leave policy" → policy
    - "why low balance" → reason
    - "attendance rules" → rules

    Return ONLY the key name.

    Query:
    {user_query}
    """

    key = ask_ai(prompt)

    if not key:
        return "info"

    return key.strip().lower().replace(" ", "_")