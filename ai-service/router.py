def route_question(question):

    sql_keywords = [
        "employee", "salary", "manager",
        "leave balance", "attendance",
        "promotion", "increment"
    ]

    for word in sql_keywords:
        if word in question.lower():
            # return "sql"
            if "policy" in question.lower() or "rules" in question.lower():
                if any(k in question.lower() for k in ["leave", "employee", "attendance"]):
                    return "hybrid"
                return "vector"

            return "sql"

    return "vector"