from sql_agent import enforce_name_filter, generate_sql_strict
from sql_tool import run_sql
from config.schema import ALLOWED_SCHEMA
from services.sql_service import build_schema_prompt,enforce_limit,retry_with_error,validate_sql

def is_comparison_query(query):
    q = query.lower()

    keywords = [
        "compare", "vs", "versus",
        "more than", "less than",
        "higher", "lower", "difference"
    ]

    return any(k in q for k in keywords)

def detect_comparison_metric(query):
    q = query.lower()

    if "leave" in q:
        return {
            "metric": "leave_balance",
            "table_hint": "leave"
        }

    elif "attendance" in q:
        return {
            "metric": "attendance",
            "table_hint": "attendance"
        }

    return {
        "metric": "leave_balance",
        "table_hint": "leave"
    }

def format_comparison_table(data, metric):
    columns = ["Name", metric.replace("_", " ").title()]
    rows = []

    for row in data:
        value = (
            row.get("closing_pl") or
            row.get("leave_balance") or
            row.get("present_days") or
            0
        )

        rows.append([row.get("name"), value])

    return columns, rows

def generate_comparison_insight(rows):
    if len(rows) < 2:
        return "Not enough data to compare."

    try:
        sorted_rows = sorted(rows, key=lambda x: x[1], reverse=True)

        top = sorted_rows[0]
        second = sorted_rows[1]

        diff = top[1] - second[1]

        return f"{top[0]} has {diff} more than {second[0]}."
    except:
        return "Comparison completed."

def handle_comparison_query(query):
    # 🔹 Step 1: Extract names
    user_ids, error = enforce_name_filter(query)

    if error:
        return {
            "type": "text",
            "message": error
        }

    if len(user_ids) < 2:
        return {
            "type": "text",
            "message": "Please provide at least two employees for comparison."
        }

    # 🔹 Step 2: Detect metric
    metric = detect_comparison_metric(query)

    # 🔹 Step 3: Generate SQL
    # schema_prompt = build_schema_prompt(ALLOWED_SCHEMA)
    # sql_query = generate_sql_strict(query, schema_prompt)

    schema_prompt = build_schema_prompt(ALLOWED_SCHEMA)
    sql_query = generate_sql_strict(query, schema_prompt)

    # Step 31: Enforce LIMIT
    sql_query = enforce_limit(sql_query)

    # Step 32: Validate
    is_valid, msg = validate_sql(sql_query)
    if not is_valid:
        print("[SQL INVALID BEFORE EXEC]", msg)

        sql_query = retry_with_error(
            user_query["raw"],
            sql_query,
            msg,
            schema_prompt
        )

        sql_query = enforce_limit(sql_query)

        is_valid, msg = validate_sql(sql_query)

        if not is_valid:
            return {
                "type": "text",
                "message": "Unable to generate valid query. Please rephrase."
            }


    print("Comparison SQL:", sql_query)

    # 🔹 Step 4: Run SQL
    result = run_sql(sql_query)

    print("Result : ", result)

    if not result or not result.get("data"):
        return {
            "type": "text",
            "message": "No data found for comparison."
        }

    data = result["data"]

    # 🔹 Step 5: Format table
    columns, rows = format_comparison_table(data, metric)

    # 🔹 Step 6: Insight
    insight = generate_comparison_insight(rows)

    # 🔹 Final response
    return {
        "type": "comparison",
        "sections": [
            {
                "type": "table",
                "title": "Comparison",
                "columns": columns,
                "rows": rows
            },
            {
                "type": "insight",
                "content": insight
            }
        ]
    }