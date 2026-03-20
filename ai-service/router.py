def route_question(question):

    sql_keywords = [
        "employee", "salary", "manager",
        "leave balance", "attendance",
        "promotion", "increment"
    ]

    for word in sql_keywords:
        if word in question.lower():
            return "sql"

    return "vector"