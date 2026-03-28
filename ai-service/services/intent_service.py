import re
from utils.llm import ask_ai

def detect_intent(query):
    # 1. Rule-based
    intent = detect_intent_rule_based(query)
    
    if intent:
        return intent

    # 2. Pattern-based
    intent = detect_intent_pattern(query)
    
    if intent:
        return intent

    # 3. LLM fallback
    intent = detect_intent_llm(query)
    
    return intent 

def detect_intent_rule_based(query):
    q = query.lower()

    if any(word in q for word in ["leave balance", "sick leave", "casual leave"]):
        return "SQL"

    if any(word in q for word in ["policy", "rule", "process", "how"]):
        return "VECTOR"

    return None

def detect_intent_pattern(query):
    q = query.lower()

    if re.search(r"(how many|balance|remaining).*(leave)", q):
        return "SQL"

    if re.search(r"(what|how).*(policy|rule)", q):
        return "VECTOR"

    return None

def detect_intent_llm(query):
    prompt = f"""
    You are an intent classifier.

    Classify the user query into EXACTLY one of these:
    - SQL → ONLY when user is asking for specific data retrieval (numbers, records, lists, dates, balances, reports)
    - VECTOR → when user is asking for explanation, definition, policy, rules, how-to, meaning
    - HYBRID → when BOTH data + explanation is requested

    STRICT RULES:
    - If query contains words like: what, why, how, explain, policy, rules → VECTOR
    - If query asks for specific person data (name, balance, DOB, report) → SQL
    
    - NEVER assume SQL unless clearly asked

    Return ONLY one word: SQL or VECTOR or HYBRID
    Do NOT explain.

    Query:
    {query}
    """
    # - If unclear or generic (e.g. "leave", "details") → VECTOR (DO NOT use SQL)
    res = ask_ai(prompt)
    
    return clean_intent_response(res)

def clean_intent_response(response: str):
    if not response:
        return None

    res = response.strip().upper()

    if "SQL" in res:
        return "SQL"
    if "VECTOR" in res:
        return "VECTOR"

    return None