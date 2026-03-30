from services.sql_service import handle_sql_query, build_schema_prompt
from services.vector_service import handle_vector_query
from utils.parser import parse_query
from config.schema import ALLOWED_SCHEMA
from utils.llm import ask_ai
import re

def is_hybrid_query(parsed_query):
    query = parsed_query["raw"].lower()

    has_data = any(k in query for k in [
        "attendance", "leave", "balance", "report", "salary"
    ])

    has_explain = any(k in query for k in [
        "policy", "rules", "how", "why"
    ])

    return has_data and has_explain

def extract_vector_query_llm(query):
    prompt = f"""
    You are an assistant that extracts only the explanation or policy-related part of a query.

    Rules:
    - Keep only parts related to: policy, rules, explanation, how, why
    - Remove employee names, dates, and data queries
    - If no explanation part exists, return empty string

    Query:
    "{query}"

    Return ONLY the extracted text. No extra words.
    """

    response = ask_ai(prompt)  # your existing LLM function

    return response.strip()

def handle_hybrid_query(parsed_query):
    try:
        # 1. SQL processing (structured data)
        schema_prompt = build_schema_prompt(ALLOWED_SCHEMA)
        sql_result = handle_sql_query(parsed_query, schema_prompt)

        # 2. Vector processing (explanation)
        # 2. Vector (LLM cleaned query)
        vector_query = extract_vector_query_llm(parsed_query["raw"])
        print("Vector Query : ", vector_query)
        if not vector_query:
            vector_query = parsed_query["raw"]

        vector_result = handle_vector_query(vector_query)
        print("VECTOR RESULT : ", vector_result)
        # 3. Merge
        return merge_hybrid_response(
            sql_result,
            vector_result,
            parsed_query["raw"]
        )
    except Exception as e:
        return {
            "type": "text",
            "message": f"Hybrid Error: {str(e)}"
        }

def handle_hybrid_query_old(user_query):
    try:
        # 1. Split query
        sql_part, vector_part = split_hybrid_query(user_query["raw"])
        
        print("PART : ", sql_part, vector_part)

        sql_parsed = parse_query(sql_part)
        vector_parsed = parse_query(vector_part)
        
        # print("HYBRID : ", user_query, sql_part, vector_part)
        # 2. Process SQL
        schema_prompt = build_schema_prompt(ALLOWED_SCHEMA)
        sql_result = handle_sql_query(sql_parsed, schema_prompt)

        # 3. Process Vector
        vector_result = None
        if vector_part:
            vector_result = handle_vector_query(vector_parsed)

        # 4. Merge results
        return merge_hybrid_response(sql_result, vector_result, user_query["raw"])

    except Exception as e:
        return {
            "type": "text",
            "message": f"Hybrid Error: {str(e)}"
        }

def contains_keyword(text, keywords):
    return any(re.search(rf"\b{k}\b", text) for k in keywords)

def split_hybrid_query(query):
    query = query.lower()

    if " and " in query:
        parts = query.split(" and ")

        sql_part = ""
        vector_part = ""
        
        for p in parts:
            if contains_keyword(p, ["policy", "rules", "how", "why"]):
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