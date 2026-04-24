import re
from utils.llm import ask_ai
from utils.llm_service import call_llm

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
        if any(k in part for k in ["policy", "rule", "guidelines"]):
            return "VECTOR"
        return "SQL"
    
    return intent

def detect_intent(query):
    
    # ✅ Normalize input
    if isinstance(query, dict):
        q = query.get("raw", "")
    else:
        q = query

    if not isinstance(q, str):
        q = str(q)

    q = q.lower()

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
        "address",
        "joining date", "doj", "leaves taken"
    ]

    medium_sql = [
        "list", "show", "get", "fetch"
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
        if word in query:
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
    if query.get("name"):
        sql_score += 2   # strong signal for SQL

    if any(word in q for word in ["get", "list", "show"]) and "employee" in q:
        sql_score += 2
    
    # 🔥 Boost vector for definition queries
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
        if "employee" in q or "name" in q:
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
        "attendance", "salary", "report"
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
    {query["raw"]}
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