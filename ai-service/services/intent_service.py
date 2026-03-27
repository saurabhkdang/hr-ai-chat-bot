def detect_intent(query):
    q = query.lower()

    if any(word in q for word in ["leave", "attendance", "employee", "balance"]):
        return "SQL"

    if any(word in q for word in ["policy", "rule", "how", "process"]):
        return "VECTOR"

    return "VECTOR"