from sql_agent import generate_sql_strict
from sql_tool import run_sql
from utils.llm import ask_ai
from utils.formatter import format_response
from datetime import datetime, timedelta
import re
from utils.llm_service import call_llm
from utils.entity_extractor import extract_employee_names

ALLOWED_OPERATIONS = ["SELECT"]
BLOCKED_KEYWORDS = [
    "DELETE", "UPDATE", "INSERT", "DROP", "ALTER",
    "TRUNCATE", "EXEC", "UNION"
]

def extract_date_range(query: str):
    query = query.lower()
    today = datetime.today()

    # last N days
    match = re.search(r"last (\d+) days", query)
    if match:
        days = int(match.group(1))
        start = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        return start, end

    # last N months
    match = re.search(r"last (\d+) months", query)
    if match:
        months = int(match.group(1))
        start = (today - timedelta(days=30*months)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        return start, end

    # till today
    if "till today" in query or "until today" in query:
        return None, today.strftime('%Y-%m-%d')

    return None, None

def retry_with_error(user_query, sql_query, error_msg, schema_prompt):
    prompt = f"""
    You are an expert SQL assistant.

    The following SQL query failed.

    User Question:
    {user_query}

    SQL Query:
    {sql_query}

    Error:
    {error_msg}

    Schema:
    {schema_prompt}

    Fix the SQL query.

    Rules:
    - Only SELECT queries
    - Use correct column names from schema
    - ALWAYS use table aliases (u, a, etc.)
    - ALWAYS prefix column names with table alias
    - NEVER use ambiguous column names
    - If multiple tables have same column, choose correct table based on context
    - Date Handling Rules (STRICT):
        - NEVER use MONTH(), YEAR(), or DATE() functions for filtering
        - ALWAYS convert month/year into full date range
        - ALWAYS use BETWEEN for date filtering
    - Always apply date filters if mentioned:
        - "today" → current date
        - "last N days" → BETWEEN dates
    - If "till today" → use <= current_date
    - Add LIMIT 10
    - Do not explain anything

    Return only corrected SQL.
    """
    conent = call_llm(prompt)
    # 🔥 CLEAN RESPONSE
    # content = content.replace("```sql", "").replace("```", "").strip()

    # if content.lower().startswith("sql"):
    #     content = content[3:].strip()

    return content

def build_schema_prompt(schema):
    lines = []

    for table, details in schema.items():
        cols = details["columns"]
        col_desc = "\n".join(
            f"- {col}: {desc}" for col, desc in cols.items()
        )

        lines.append(f"""
        Table: {table}
        Columns:
        {col_desc}
        """)

    return "\n".join(lines)

def is_lookup_query(q):
    return (
        len(q.split()) <= 6 and
        any(word in q for word in ["of", "for"])
    )

def is_valid_sql_query(user_query):
    user_query = user_query.lower()

    strong_sql = ["balance", "report", "attendance", "salary"]
    weak_sql = ["leave", "details"]

    # 🔥 NEW: field keywords
    field_keywords = [
        "dob", "date of birth",
        "email", "phone", "mobile",
        "address", "salary"
    ]

    # 🔥 NEW: entity pattern
    if any(f in user_query for f in field_keywords) and is_lookup_query(user_query):
        return True

    if any(k in user_query for k in strong_sql):
        return True

    if any(k in user_query for k in weak_sql):
        return False

    return any(k in user_query for k in ["show", "list", "get"])

def handle_sql_query(user_query, SCHEMA_PROMPT):
    try:
        if not user_query["raw"].strip():
            return {
                "type": "text",
                "message": "Please enter a query"
            }

        if not is_valid_sql_query(user_query["raw"]):
            print("SQL BLOCKED:", user_query["raw"])
            return {
                "type": "text",
                "message": "Please provide more specific query"
            }

        query = user_query["raw"]

        names = extract_employee_names(query)

        if not names:
            return {
                "type": "text",
                "message": "Please specify employee name."
            }


        if user_query["name"]:
            query += f" for employee {user_query['name']}"

        if user_query["date_range"]:
            query += f" | DATE_RANGE: {user_query['date_range']}"


        start_date, end_date = extract_date_range(query)

        if start_date or end_date:
            query += f" | DATE_FILTER: {start_date} to {end_date}"        

        # Step 1: Generate SQL
        sql_query = generate_sql_strict(query, SCHEMA_PROMPT)

        # Step 2: Enforce LIMIT
        sql_query = enforce_limit(sql_query)

        # Step 3: Validate
        is_valid, msg = validate_sql(sql_query)
        if not is_valid:
            print("[SQL INVALID BEFORE EXEC]", msg)

            sql_query = retry_with_error(
                user_query["raw"],
                sql_query,
                msg,
                SCHEMA_PROMPT
            )

            sql_query = enforce_limit(sql_query)

            is_valid, msg = validate_sql(sql_query)

            if not is_valid:
                return {
                    "type": "text",
                    "message": "Unable to generate valid query. Please rephrase."
                }

        # Step 4: Execute with retry
        result = execute_with_retry(user_query["raw"], sql_query, SCHEMA_PROMPT)
        print("SQL Result:", result)
        # Step 5: Normalize
        rows = normalize_rows(result)
        print("Normalize Rows: ", rows)
        # Step 6: Format response
        return build_final_response(rows, user_query["raw"])

    except ValueError as e:
        return {
            "type": "text",
            "message": str(e)
        }
    except Exception as e:
        return {
            "type": "text",
            "message": f"Error processing request: {str(e)}"
        }

def enforce_limit(query: str, limit=10):
    q = query.strip().rstrip(";")

    if "LIMIT" not in q.upper():
        return q + f" LIMIT {limit};"

    return q

def validate_sql(query: str) -> (bool, str):
    q = query.upper().strip()

    # must start with SELECT
    if not q.startswith("SELECT"):
        return False, "Only SELECT queries allowed"

    # block dangerous keywords
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", q):
            return False, f"Blocked keyword: {keyword}"

    # prevent multiple statements
    if ";" in q[:-1]:
        return False, "Multiple statements not allowed"

    # prevent SELECT *
    if "SELECT *" in q:
        return False, "SELECT * not allowed"

    # must have LIMIT
    if "LIMIT" not in q:
        return False, "LIMIT missing"

    return True, "Valid"

def execute_with_retry(user_query, sql_query, schema_prompt, max_retries=2):
    attempt = 0

    while attempt <= max_retries:
        try:
            return run_sql(sql_query)

        except Exception as e:
            error_msg = str(e)

            print(f"Attempt {attempt + 1} failed:", error_msg)

            if attempt == max_retries:
                raise Exception("Max retries reached")

            # 🔥 Generate corrected SQL
            sql_query = retry_with_error(
                user_query,
                sql_query,
                error_msg,
                schema_prompt
            )

            attempt += 1

def normalize_rows(result):
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    elif isinstance(result, list):
        return result
    else:
        return []

def build_final_response(rows, user_query):
    base = format_response(rows, user_query)

    # Add summary only if data exists
    if rows:
        summary = generate_summary(rows, user_query)
        base["summary"] = summary

    return base

def generate_summary(rows, user_query):
    prompt = f"""
    Convert the following database result into a short human-friendly response.

    User Question:
    {user_query}

    Data:
    {rows}

    Keep it short and clear.
    """
    return call_llm(prompt)