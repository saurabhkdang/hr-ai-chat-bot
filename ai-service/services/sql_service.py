from sql_agent import generate_sql
from sql_tool import run_sql
from utils.llm import ask_ai
from datetime import datetime, timedelta
import re

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
    conent = ask_ai(prompt)
    # 🔥 CLEAN RESPONSE
    content = content.replace("```sql", "").replace("```", "").strip()

    if content.lower().startswith("sql"):
        content = content[3:].strip()

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

def is_valid_sql_query(user_query):
    user_query = user_query.lower()

    keywords = ["show", "list", "get", "find", "balance", "report", "dob"]

    return any(k in user_query for k in keywords)

def handle_sql_query(user_query, SCHEMA_PROMPT):
    try:
        if not user_query.strip():
            return {
                "type": "text",
                "message": "Please enter a query"
            }

        if not is_valid_sql_query(user_query):
            print("SQL BLOCKED:", user_query)
            return {
                "type": "text",
                "message": "Please provide more specific query"
            }

        start_date, end_date = extract_date_range(user_query)

        if start_date or end_date:
            user_query += f" | DATE_FILTER: {start_date} to {end_date}"        

        # Step 1: Generate SQL
        sql_query = generate_sql(user_query, SCHEMA_PROMPT)

        # Step 2: Enforce LIMIT
        sql_query = enforce_limit(sql_query)

        # Step 3: Validate
        is_valid, msg = validate_sql(sql_query)
        if not is_valid:
            return {
                "type": "text",
                "message": f"Invalid query: {msg}"
            }

        # Step 4: Execute with retry
        result = execute_with_retry(user_query, sql_query, SCHEMA_PROMPT)

        # Step 5: Normalize
        rows = normalize_rows(result)

        # Step 6: Format response
        return build_final_response(rows, user_query)

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

    # Must start with SELECT
    if not q.startswith("SELECT"):
        return False, "Only SELECT queries are allowed."

    # Block dangerous keywords
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", q):
            return False, f"Blocked keyword detected: {keyword}"

    # Prevent multiple statements
    if ";" in q and not q.endswith(";"):
        return False, "Multiple SQL statements are not allowed."

    # Enforce LIMIT
    if "LIMIT" not in q:
        return False, "Query must include LIMIT."

    return True, "Valid query"

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

def detect_response_type(rows):
    if not rows:
        return "empty"

    if len(rows) == 1 and len(rows[0]) == 1:
        return "single_value"

    return "table"

def format_response(rows, user_query):
    response_type = detect_response_type(rows)

    if response_type == "empty":
        return {
            "type": "text",
            "message": "No data found."
        }

    elif response_type == "single_value":
        key = list(rows[0].keys())[0]
        value = rows[0][key]

        return {
            "type": "text",
            "message": f"{key.replace('_', ' ').title()}: {value}"
        }

    else:
        columns = [prettify_column(c) for c in rows[0].keys()]
        return {
            "type": "table",
            "columns": list(columns),
            "rows": [list(row.values()) for row in rows]
        }

def prettify_column(col):
    return col.replace("_", " ").title()

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
    return ask_ai(prompt)