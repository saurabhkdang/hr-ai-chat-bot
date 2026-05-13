from services.query import handle_query

def test_queries():
    test_cases = [
        # SQL
        "saurabh dang leave balance as on march 2026",
        "show last 7 days attendance for mukesh kumar sharma",
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

        # "attendance status of saurabh dang on 23rd March 2026",
        # "leaves taken by saurabh dang in feb 2026",
        # "process to take work from?",
        # "share me the important points of referral program",
        # "Show leave balance of saurabh dang in march 2026 and leave policy",
        # "leave balance of saurabh dang in march 2026",
        # "leave details",
        # "apply leave process",
        # "get all active emplyoees with name contain saurabh",
        # "leave balance of saurabh dang in april 2026 and leave policy",
        # "show last 7 days attendance for mukesh kumar sharma",
        # "what is leave policy",
        # "leave balance and leave policy",
        # "saurabh dang leave balance till today and work from home approval prcoess",
        # "last 7 days attendance report of saurabh dang",
        # "compare leave balance of saurabh dang and shanky",
        # "leaves taken by mukesh kumar in march 2026",
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