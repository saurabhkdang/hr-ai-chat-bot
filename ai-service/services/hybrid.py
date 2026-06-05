from services.sql_service import handle_sql_query, build_schema_prompt, handle_sql
from services.vector_service import handle_vector_query
from utils.parser import parse_query
from config.schema import ALLOWED_SCHEMA
# from utils.llm import ask_ai
from utils.llm_service import call_llm
from utils.intent_service import detect_intent_for_part
import re

def looks_like_hybrid_query(query: str) -> bool:
    q = query.lower()

    sql_signals = [
        "show",
        "get",
        "list",
        "attendance",
        "leave balance",
        "leaves taken",
        "employee",
        "employees",
        "today",
        "yesterday",
        "last",
        "this month"
    ]

    vector_signals = [
        "policy",
        "rule",
        "rules",
        "process",
        "procedure",
        "guideline",
        "what happens",
        "what is the rule",
        "explain",
        "allowed",
        "not allowed",
        "eligibility",
        "repeated",
        "late attendance"
    ]

    has_sql = any(signal in q for signal in sql_signals)
    has_vector = any(signal in q for signal in vector_signals)

    connector_words = [" and ", " also ", " along with ", " plus "]
    has_connector = any(word in q for word in connector_words)

    return has_sql and has_vector and has_connector

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

    prompt = f"""
    Extract only the semantic search query from this.

    User Query:
    {query}

    Return ONLY cleaned query.
    """

    response = call_llm(prompt)  # your existing LLM function

    return response.strip()

def split_hybrid_query(query):
    q = query.lower()
    print("QUERY : ", q)
    
    separators = [" and ", ",", " also "]

    for sep in separators:
        if sep in q:
            parts = q.split(sep)
            
            sql_part = None
            vector_part = None

            # ✅ MAIN LOOP (REPLACE your existing logic here)
            for part in parts:
                part = part.strip()

                intent = detect_intent_for_part({"raw": part})
                print(f"Part: {part}, Intent: {intent}")

                if intent == "SQL":
                    sql_part = part
                elif intent == "VECTOR":
                    vector_part = part

            # If both parts look SQL → NOT hybrid
            if sql_part and not vector_part:
                return query, None

            # ✅ FALLBACK (ADD HERE — AFTER loop)
            if not vector_part:
                for part in parts:
                    if any(k in part for k in ["policy", "rule", "rules", "guidelines", "process"]):
                        vector_part = part

            print("Parts : ", parts)
            return sql_part, vector_part

    return query, None

def clean_sql_query(query: str):
    q = query.lower()

    REMOVE_PHRASES = [
        "can you", "please", "tell me", "show me",
        "what is", "give me", "i want", "get me"
    ]

    for phrase in REMOVE_PHRASES:
        q = q.replace(phrase, "")

    # remove explanation words
    # remove explain-style patterns
    patterns = [
        r"explain.*",
        r"what is.*",
        r"how.*",
        r"why.*",
        r"policy.*",
        r"rules.*"
    ]

    for p in patterns:
        q = re.sub(p, "", q)

    return q.strip()

def clean_sql_query_r(query: str):
    q = query.lower()

    # remove explain-style patterns
    patterns = [
        r"explain.*",
        r"what is.*",
        r"how.*",
        r"why.*"
    ]

    for p in patterns:
        q = re.sub(p, "", q)

    # remove keywords
    REMOVE_WORDS = ["policy", "rules"]
    for word in REMOVE_WORDS:
        q = q.replace(word, "")

    return q.strip()

def clean_sql_query1(raw_query: str):
    query = raw_query.lower()

    # remove explanation intent parts
    REMOVE_WORDS = ["policy", "rules", "how", "why", "explain"]

    for word in REMOVE_WORDS:
        query = query.replace(word, "")

    # remove "and ..." part if it's mixed
    if " and " in query:
        parts = query.split(" and ")
        query = parts[0]   # keep only first (data part)

    return query.strip()

def handle_hybrid_query(parsed_query):
    try:

        sql_part, vector_part = split_hybrid_query(parsed_query["raw"])
        print("SPLIT PARTS:")
        print("SQL : ", sql_part)
        print("Vector : ", vector_part)
        # ✅ Clean SQL input
        sql_clean = clean_sql_query(sql_part)

        # 1. SQL processing (structured data)
        schema_prompt = build_schema_prompt(ALLOWED_SCHEMA)

        if not sql_part or len(sql_part.strip()) < 5:
            sql_result = None
        else:
            sql_result = handle_sql(parsed_query, allow_empty=True)
            # sql_result = handle_sql_query(parse_query(sql_clean), schema_prompt)

        # 2. Vector processing (explanation)
        vector_query = (vector_part or parsed_query["raw"]).strip()
        print("Vector Query : ", vector_query)

        if not vector_query:
            return sql_result  # skip vector entirely

        vector_result = handle_vector_query(vector_query)
        print("VECTOR RESULT : ", vector_result)
        # 3. Merge
        return build_hybrid_response(
            sql_result,
            vector_result
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

def split_hybrid_query_old(query):
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

def get_text_from_vector_result(vector_result):
    if isinstance(vector_result, str):
        return vector_result

    if isinstance(vector_result, dict):
        # Common cases
        if "message" in vector_result:
            return vector_result["message"]

        if "content" in vector_result:
            return vector_result["content"]

        if "text" in vector_result:
            return vector_result["text"]

        if "data" in vector_result:
            # if list of chunks
            if isinstance(vector_result["data"], list):
                return " ".join(
                    item.get("content", "") for item in vector_result["data"]
                )

        # fallback
        return str(vector_result)

    return str(vector_result)

def classify_vector_content_rule_based(vector_result):
    text = get_text_from_vector_result(vector_result)
    text_lower = text.lower()

    if "policy" in text_lower:
        return {"type": "policy", "title": "Policy"}
    elif "rule" in text_lower:
        return {"type": "rules", "title": "Rules"}
    elif "process" in text_lower or "steps" in text_lower:
        return {"type": "process", "title": "Process"}
    elif "faq" in text_lower:
        return {"type": "faq", "title": "FAQ"}

    return {"type": "text", "title": "Information"}

def classify_vector_content(text):
    prompt = f"""
    Classify the below content into one of these categories:
    - policy
    - rules
    - process
    - faq
    - general
    - leaves
    - attendance

    Also generate a short title (2-4 words).

    Return JSON:
    {{
        "type": "...",
        "title": "..."
    }}

    Content:
    {text}
    """

    response = call_llm(prompt)

    response = response.replace("```json", "").replace("```", "").strip()

    try:
        import json
        return json.loads(response)
    except:
        return {
            "type": "text",
            "title": "Information"
        }

def summarize_vector_result(vector_result):
    text = get_text_from_vector_result(vector_result)

    # छोटे text को skip करो (performance optimization)
    if len(text) < 300:
        return text

    prompt = f"""
    Summarize the below HR-related content into a short, clear answer.

    RULES:
    - Keep it under 3-4 lines
    - Be precise and user-friendly
    - Do NOT miss key rules or numbers
    - Do NOT add extra info
    - Do NOT explain anything

    Content:
    {text}
    """

    response = call_llm(prompt)

    # cleanup
    response = response.replace("```", "").strip()

    return response

def build_hybrid_response(sql_result, vector_result):
    response = {
        "type": "hybrid",
        "sections": []
    }

    # 🟢 SQL TABLE
    if sql_result:
        response["sections"].append({
            "type": "table",
            "title": "Result",
            "columns": sql_result.get("columns", []),
            "rows": sql_result.get("rows", [])
        })

    # 🟢 SUMMARY
    if sql_result and sql_result.get("summary"):
        response["sections"].append({
            "type": "summary",
            "title": "Summary",
            "content": sql_result["summary"]
        })

    if vector_result:
        raw_text = get_text_from_vector_result(vector_result)
        summary_text = raw_text.strip()
        meta = classify_vector_content_rule_based(summary_text)

        response["sections"].append({
            "type": meta.get("type", "text"),
            "title": meta.get("title", "Information"),
            "content": summary_text   # ✅ FIXED
        })

    return response

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

    key = call_llm(prompt)

    if not key:
        return "info"

    return key.strip().lower().replace(" ", "_")