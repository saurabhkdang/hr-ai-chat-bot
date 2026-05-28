import json
import re
from utils.llm_service import call_llm

VALID_INTENTS = {"SQL", "VECTOR", "HYBRID"}

SUPPORTED_SQL_METRICS = {
    "attendance",
    "leave_balance",
    "employee_list",
    "employee_info",
    "manager_info",
    "job_description",
    "applied_leaves",
    "employee_hierarchy"
}


def normalize_query(query):
    if isinstance(query, dict):
        raw_query = query.get("raw", "")
        parsed_name = query.get("name")
    else:
        raw_query = query
        parsed_name = None

    if not isinstance(raw_query, str):
        raw_query = str(raw_query)

    return raw_query, raw_query.lower().strip(), parsed_name


def clean_json_response(response):
    if not response:
        return None

    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        return None

    try:
        return json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return None

def detect_intent_old(query):
    # 1️⃣ Rule-based (fast + strong for hybrid)
    intent = detect_intent_rule_based(query)
    if intent:
        return intent

    # 2️⃣ Pattern-based (backup)
    intent = detect_intent_pattern(query)
    if intent:
        return intent

    # 3️⃣ LLM (final fallback)
    intent = detect_intent_llm(query)
    if intent:
        return intent

    # 4️⃣ Default (safe fallback)
    return "VECTOR"

def is_definition_query(query):
    q = query.lower()

    patterns = [
        "what is",
        "define",
        "explain",
        "policy",
        "meaning",
        "how does",
        "rules",
        "guidelines"
    ]

    return any(p in q for p in patterns)

def check_hybrid_query(q):
    return any(sep in q for sep in [" and ", ",", " & "])

def detect_intent_for_part(part):
    print(f"Intent for part '{part}'")
    intent = detect_intent(part)
    if intent == "HYBRID":
        part_text = part.get("raw", "") if isinstance(part, dict) else str(part)
        part_text = part_text.lower()
        if any(k in part_text for k in ["policy", "rule", "guidelines"]):
            return "VECTOR"
        return "SQL"
    
    return intent

def detect_intent(query):
    raw_query, q, parsed_name = normalize_query(query)

    print("Detecting intent for query:", q)

    # quick_intent = detect_intent_quick_rules(q, parsed_name)
    # if quick_intent:
    #     print("Intent source: quick rules")
    #     return quick_intent

    llm_intent = detect_intent_structured_llm(raw_query)
    if llm_intent:
        print("Intent source: structured llm")
        return llm_intent

    print("Intent source: keyword score fallback")
    return detect_intent_keyword_score(query)


def detect_intent_quick_rules(q, parsed_name=None):
    if not q:
        return "VECTOR"

    normalized_q = q.replace("prcoess", "process")

    sql_terms = [
        "balance", "attendance", "salary", "dob", "date of birth",
        "email", "phone", "manager of", "reporting manager", "reports to",
        "report to", "job description", "job title", "designation",
        "team members", "direct reports", "hierarchy"
    ]
    vector_terms = [
        "policy", "rules", "guidelines", "process", "procedure",
        "approval", "approve", "how to", "why", "explain", "define", "meaning",
        "work from home", "wfh"
    ]
    data_question_terms = [
        "who", "which employee", "which employees", "how many",
        "list", "show", "get", "fetch"
    ]
    leave_status_terms = [
        "on leave", "due to leave", "because of leave", "not working",
        "not been working", "not worked", "absent", "present", "weekly off"
    ]

    has_sql = any(term in normalized_q for term in sql_terms) or parsed_name
    has_vector = any(term in normalized_q for term in vector_terms)
    has_data_question = any(term in normalized_q for term in data_question_terms)
    has_leave_status = any(term in normalized_q for term in leave_status_terms)

    if check_hybrid_query(normalized_q) and has_sql and has_vector:
        return "HYBRID"

    if has_leave_status and (has_data_question or "employee" in q or "leave" in q):
        return "SQL"

    if has_sql and not has_vector:
        return "SQL"

    if has_vector and not has_sql:
        return "VECTOR"

    if has_sql and has_vector:
        data_action_terms = [
            "show", "list", "get", "fetch", "how many", "count",
            "balance", "report", "status"
        ]
        if not any(term in q for term in data_action_terms):
            return "VECTOR"

    if q in {"leave", "details", "leave details"}:
        return "VECTOR"

    return None


def detect_intent_structured_llm(raw_query):
    prompt = f"""
    You are an intent router for an HR assistant.

    Classify the user's query into exactly one intent:
    - SQL: user asks for employee/database facts, records, lists, counts, attendance, leave status, salary, DOB, manager, hierarchy, job description, or filters over employees.
    - VECTOR: user asks for policy, rules, process, explanation, meaning, guidelines, or general HR knowledge.
    - HYBRID: user asks for both database facts and policy/explanation in the same query.

    Supported SQL metrics:
    {", ".join(sorted(SUPPORTED_SQL_METRICS))}

    Return ONLY valid JSON:
    {{
        "intent": "SQL|VECTOR|HYBRID",
        "confidence": 0.0,
        "sql_metric": "one supported SQL metric or null",
        "vector_topic": "short topic or null",
        "reason": "short reason"
    }}

    Rules:
    - Use SQL for prompts like "who is on leave today", "who has not been working this week due to leave", or "which employees were absent".
    - Use VECTOR for prompts like "how to apply leave", "leave policy", or "what is sick leave".
    - Use HYBRID when one query asks for both data and policy/rules/process.
    - If unsure, choose VECTOR with low confidence.

    User query:
    {raw_query}
    """

    try:
        response = call_llm(prompt)
    except Exception as e:
        print(f"Structured intent LLM failed: {e}")
        return None

    data = clean_json_response(response)
    return validate_structured_intent(data)


def validate_structured_intent(data):
    if not isinstance(data, dict):
        return None

    intent = str(data.get("intent", "")).strip().upper()
    if intent not in VALID_INTENTS:
        return None

    try:
        confidence = float(data.get("confidence", 0))
    except (TypeError, ValueError):
        confidence = 0

    if confidence < 0.55:
        return None

    metric = data.get("sql_metric")
    if intent in {"SQL", "HYBRID"} and metric and metric not in SUPPORTED_SQL_METRICS:
        return None

    return intent


def detect_intent_keyword_score(query):
    
    # ✅ Normalize input
    if isinstance(query, dict):
        raw_query = query.get("raw", "")
        parsed_name = query.get("name")
    else:
        raw_query = query
        parsed_name = None

    if not isinstance(raw_query, str):
        raw_query = str(raw_query)
    
    q = raw_query.lower().strip()

    print("Detecting intent for query:", q)
    policy_keywords = [
        "policy", "rules", "guidelines",
        "process", "procedure"
    ]

    # if any(k in q for k in policy_keywords):
    #     # If query ALSO has SQL signals → don't force vector
    #     if not any(k in q for k in ["balance", "salary", "attendance", "report", "dob"]):
    #         return "VECTOR"

    sql_score = 0
    vector_score = 0

    # ---------------- SQL SIGNALS ----------------
    strong_sql = [
        "balance", "remaining", "total", "count",
        "attendance", "salary", "report",
        "employee", "employees", "active", "inactive",
        # 🔥 ADD THESE
        "dob", "date of birth",
        "email", "phone",
        "address", "manager", "reporting manager", "reports to", "report to",
        "joining date", "doj", "leaves taken",
        "job description", "job title", "designation", "job role",
        "team member", "team members", "direct report", "direct reports",
        "hierarchy"
    ]

    medium_sql = [
        "list", "show", "get", "fetch", "how many", "number of"
    ]

    weak_sql = [
        "leave", "details"
    ]

    STRONG_SQL_SIGNALS = [
        "taken", "balance", "report", "status", "list"
    ]

    # ---------------- VECTOR SIGNALS ----------------
    strong_vector = [
        "policy", "rule", "rules", "process", "wfh", "work from home"
    ]

    medium_vector = [
        "how", "why", "explain", "meaning", "what"
    ]

    # ---------------- SCORING ----------------

    for word in strong_sql:
        if word in q:
            sql_score += 3
    
    for word in STRONG_SQL_SIGNALS:
        if word in q:
            sql_score += 2  # 🔥 boost

    for word in medium_sql:
        if word in q:
            sql_score += 2

    for word in weak_sql:
        if word in q:
            sql_score += 1

    for word in strong_vector:
        if word in q:
            vector_score += 3

    for word in medium_vector:
        if word in q:
            vector_score += 2

    # ---------------- NAME BOOST ----------------
    if parsed_name:
        sql_score += 2   # strong signal for SQL

    if any(word in q for word in ["get", "list", "show"]) and "employee" in q:
        sql_score += 2

    if any(phrase in q for phrase in ["manager of", "reporting manager", "reports to", "report to"]):
        sql_score += 3

    # Attendance/leave status queries often do not say "attendance" directly.
    data_question_terms = [
        "who", "which employee", "which employees", "which team member",
        "which team members", "whose"
    ]
    leave_status_terms = [
        "not working", "not been working", "not worked",
        "on leave", "due to leave", "because of leave",
        "absent", "absence", "present", "weekly off"
    ]
    date_terms = [
        "today", "yesterday", "this week", "last week",
        "this month", "last month", "this year", "last year"
    ]
    leave_type_terms = [
        "privilege leave", "sick leave", "casual leave",
        "pl", "sl", "cl"
    ]

    has_data_question = any(term in q for term in data_question_terms)
    has_leave_status = any(term in q for term in leave_status_terms)
    has_date_context = any(term in q for term in date_terms)
    has_leave_type = any(term in q for term in leave_type_terms)

    if has_leave_status:
        sql_score += 3

    if has_data_question and ("leave" in q or has_leave_status or has_leave_type):
        sql_score += 4

    if "leave" in q and has_date_context and (has_data_question or has_leave_status or has_leave_type):
        sql_score += 3

    if is_definition_query(q):
        vector_score += 2

    # ---------------- POLICY GUARD (ADD HERE) ----------------
    if any(k in q for k in policy_keywords):
        if sql_score == 0:
            return "VECTOR"


    # ---------------- DEBUG ----------------
    print(f"SQL SCORE: {sql_score}, VECTOR SCORE: {vector_score}")

    # ---------------- DECISION ----------------

    # ✅ HYBRID → both strong
    if check_hybrid_query(q) and sql_score >= 2 and vector_score >= 2:
        return "HYBRID"

    # ✅ STRONG SQL ONLY
    if sql_score >= 3 and vector_score == 0:
        return "SQL"

    # ✅ STRONG VECTOR ONLY
    if vector_score >= 3 and sql_score == 0: 
        return "VECTOR"

    # ⚠️ WEAK SQL (like "leave details") → DO NOT TRUST
    # ⚠️ weak SQL guard but allow employee queries
    if sql_score <= 2 and vector_score == 0:
        if "employee" in q or "name" in q or "manager" in q:
            return "SQL"
        return "VECTOR"
        # return detect_intent_llm(query)

    # ⚖️ NORMAL COMPARISON
    if sql_score > vector_score:
        return "SQL"

    if vector_score > sql_score:
        return "VECTOR"
    
    # If it's clearly descriptive and SQL is weak → force vector
    if sql_score <= 1 and vector_score >= 2:
        return "VECTOR"

    # 🤖 FINAL FALLBACK
    return detect_intent_llm(query)

def detect_intent_rule_based(query):
    q = query["raw"].lower()

    strong_sql = [
        "balance", "remaining", "total", "count",
        "attendance", "salary", "report", "manager"
    ]

    weak_sql = [
        "leave", "details"
    ]

    explain_keywords = [
        "policy", "rule", "rules", "process",
        "how", "why", "what", "explain"
    ]

    has_strong_sql = any(word in q for word in strong_sql)
    has_weak_sql = any(word in q for word in weak_sql)
    has_explain = any(word in q for word in explain_keywords)

    # ✅ HYBRID only if strong SQL + explain
    if has_strong_sql and has_explain:
        return "HYBRID"

    if has_strong_sql:
        return "SQL"

    if has_explain:
        return "VECTOR"

    # ❗ weak SQL alone → don't trust it
    if has_weak_sql:
        return None  # let LLM decide

    return None

def detect_intent_pattern(query):
    q = query["raw"].lower()

    # SQL patterns
    if re.search(r"(how many|count|total|balance|remaining|list|show|get).*(leave|attendance|salary)", q):
        return "SQL"

    # VECTOR patterns
    if re.search(r"(what|how|why|explain).*(policy|rule|process)", q):
        return "VECTOR"

    # HYBRID patterns
    if re.search(r"(balance|report|data).*(and).*(policy|rule|how|why)", q):
        return "HYBRID"

    return None

def detect_intent_llm(query):
    raw_query = query.get("raw", "") if isinstance(query, dict) else str(query)
    prompt = f"""
    You are an intent classifier for an HR assistant.

    Classify the query into EXACTLY one:

    - SQL → if asking for employee-specific data (balance, report, attendance, salary, records)
    - VECTOR → if asking for explanation (policy, rules, process, meaning, how, why)
    - HYBRID → if BOTH data + explanation are present

    Examples:
    - "leave balance of saurabh" → SQL
    - "what is leave policy" → VECTOR
    - "leave balance of saurabh and leave policy" → HYBRID

    Rules:
    - If both types appear → ALWAYS HYBRID
    - Do NOT guess SQL unless clear data intent
    - Prefer VECTOR if unsure

    Return ONLY one word:
    SQL or VECTOR or HYBRID

    Query:
    {raw_query}
    """

    res = call_llm(prompt)
    return clean_intent_response(res)

def clean_intent_response(response: str):
    if not response:
        return None

    res = response.strip().upper()

    if "HYBRID" in res:
        return "HYBRID"
    if "SQL" in res:
        return "SQL"
    if "VECTOR" in res:
        return "VECTOR"

    return None
