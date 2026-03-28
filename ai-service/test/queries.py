from services.query import handle_query

def test_queries():
    test_cases = [
        # SQL
        "saurabh dang leave balance as on march 2026",
        "show last 7 attendance for mukesh kumar sharma",
        "dob of larry white",
        "list all active employees",

        # VECTOR
        "leave policy",
        "attendance rules",
        "what is sick leave",
        "how to apply leave",

        # HYBRID
        "saurabh dang leave balance till today and leave policy",
        # "why my leave is low and show balance",
        "last 7 days attendance report of saurabh dang and rules",

        # EDGE CASES
        "leave",
        "details",
        "random text asdasd",
        "",
    ]

    for q in test_cases:
        print("\n==============================")
        print("QUERY:", q)
        try:
            response = handle_query(q)
            print("RESPONSE:", response)
        except Exception as e:
            print("ERROR:", str(e))

test_queries()