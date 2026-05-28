from sql_agent import generate_sql_strict, enforce_name_filter
from sql_tool import run_sql
from utils.llm import ask_ai
from utils.formatter import format_response
from datetime import datetime, timedelta
import re
from utils.llm_service import call_llm
from utils.entity_extractor import extract_employee_names
from services.sql_builder import build_sql, build_sql_updated
from services.intent_parser import parse_query_intelligent, normalize_intent_data
import json

ALLOWED_OPERATIONS = ["SELECT"]
BLOCKED_KEYWORDS = [
    "DELETE", "UPDATE", "INSERT", "DROP", "ALTER",
    "TRUNCATE", "EXEC", "UNION"
]

ALLOWED_SQL_VIEWS = [
    "employee_attendance_leaves_status",
    "employees",
    "employees_job_details",
]


BLOCKED_SQL_KEYWORDS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "CREATE",
    "REPLACE",
    "EXEC",
    "MERGE",
    "GRANT",
    "REVOKE",
]

import re
from datetime import datetime, timedelta

import re
from datetime import datetime, timedelta
import calendar

def is_destructive_prompt(query: str) -> bool:
    q = query.lower()

    destructive_words = [
        "delete",
        "remove",
        "drop",
        "truncate",
        "erase",
        "clear",
        "update",
        "modify",
        "change",
        "insert",
        "create"
    ]

    return any(word in q.split() for word in destructive_words)

def handle_sql(user_query, allow_empty=False):
    try:
        if not user_query["raw"].strip():
            return {
                "type": "text",
                "message": "Please enter a query"
            }

        query = user_query["raw"]

        if is_destructive_prompt(query):
            return {
                "type": "text",
                "message": "I can only answer HR data questions using read-only SELECT queries. I cannot delete, update, or modify employee data."
            }

        print("query : ", query)
        sql_data = build_sql_updated(query)
        sql_query = sql_data["sql"]
        selected_tables = sql_data["tables"]

        print("Selected tables/views:", selected_tables)
        print("sql query : ", sql_query)

        is_valid, validation_message = validate_sql(
            sql_query,
            allowed_views=selected_tables
        )

        if not is_valid:
            return {
                "type": "text",
                "message": f"Generated SQL blocked: {validation_message}",
                "debug_sql": sql_query
            }

        result = run_sql(sql_query)
        
        if result.get("error"):
            print(f"[SQL Execution] Error: {result['error']}")
            return {
                "type": "text",
                "message": f"Query execution error: {result['error']}"
            }
        
        # ===== STEP 8: Format response =====
        rows = normalize_rows(result)
        print(f"[Query Handler] Got {len(rows)} rows")

        if not rows:
            if allow_empty:
                return {
                    "type": "table",
                    "data": [],
                    "summary": "No matching SQL records found.",
                    "sql": sql_query
                }
            return {
                "type": "text",
                "message": "I found no matching records for this query. The SQL was valid, but the filters may be too strict.",
                "debug_sql": sql_query
            }
        
        return build_final_response(rows, query)

    except ValueError as e:
        return {
            "type": "text",
            "message": str(e)
        }
    except Exception as e:
        import traceback
        print(f"[Query Handler] Exception: {e}")
        traceback.print_exc()
        return {
            "type": "text",
            "message": f"Error processing request: {str(e)}"
        }

def extract_date_range(query: str):
    query = query.lower()
    today = datetime.today()

    # 🔥 1. last N days
    match = re.search(r"last (\d+) days", query)
    if match:
        days = int(match.group(1))
        start = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        return start, end

    # 🔥 2. last N months
    match = re.search(r"last (\d+) months", query)
    if match:
        months = int(match.group(1))
        start = (today - timedelta(days=30 * months)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        return start, end

    # 🔥 3. till today
    if "till today" in query or "until today" in query:
        return None, today.strftime('%Y-%m-%d')

    # 🔥 4. specific date (23rd March 2026 or 9th May)
    match = re.search(r"on (\d{1,2})(st|nd|rd|th)? (\w+)(?: (\d{4}))?", query)
    if match:
        day = int(match.group(1))
        month_str = match.group(3)
        year = int(match.group(4)) if match.group(4) else today.year

        try:
            date_obj = datetime.strptime(f"{day} {month_str} {year}", "%d %B %Y")
        except:
            try:
                date_obj = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
            except:
                return None, None

        date_str = date_obj.strftime('%Y-%m-%d')
        return date_str, date_str

    # 🔥 5. month + year (feb 2026 / february 2026)
    match = re.search(r"in (\w+) (\d{4})", query)
    if match:
        month_str = match.group(1)
        year = int(match.group(2))

        try:
            # full month
            month = datetime.strptime(month_str, "%B").month
        except:
            try:
                # short month
                month = datetime.strptime(month_str, "%b").month
            except:
                return None, None

        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day)

        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

    # 🔥 6. only month (assume current year)
    match = re.search(r"in (\w+)", query)
    if match:
        month_str = match.group(1)

        try:
            month = datetime.strptime(month_str, "%B").month
        except:
            try:
                month = datetime.strptime(month_str, "%b").month
            except:
                return None, None

        year = today.year
        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day)

        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

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
        - NEVER use incomplete dates like '2023-10'
        - ALWAYS use full date format 'YYYY-MM-DD'
        - If month is given, use:
        BETWEEN 'YYYY-MM-01' AND 'YYYY-MM-31'
    - Always apply date filters if mentioned:
        - "today" → current date
        - "last N days" → BETWEEN dates
    - If "till today" → use <= current_date
    - Add LIMIT 10
    - Do not explain anything

    Return only corrected SQL.
    """
    try:
        content = call_llm(prompt)
    except Exception as e:
        print(f"Retry LLM failed: {e}")
        return sql_query

    if not content:
        return sql_query

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

    strong_sql = [
        "balance", "report", "attendance", "salary", "taken",
        "count", "how many", "job description", "job title", "designation", "job role"
    ]
    weak_sql = ["leave", "details"]

    field_keywords = [
        "dob", "date of birth",
        "email", "phone", "mobile",
        "address", "salary",
        "manager", "report to", "reports to", "reporting manager"
    ]

    # ✅ Field-based lookup
    if any(f in user_query for f in field_keywords) and is_lookup_query(user_query):
        return True

    # ✅ Strong SQL signals
    if any(k in user_query for k in strong_sql):
        return True

    # ✅ Weak SQL but with context
    if any(k in user_query for k in weak_sql):
        if extract_employee_names(user_query) or extract_date_range(user_query) != (None, None):
            return True

    # ✅ Generic SQL actions
    if any(k in user_query for k in ["show", "list", "get"]):
        return True

    return False

def is_valid_sql_query11(user_query):
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

def detect_metric(query):
    q = query.lower()
    print("Q : ",q)
    if "hierarchy" in q:
        return "employee_hierarchy"

    if any(phrase in q for phrase in ["manager of", "manager name", "reporting manager", "reports to", "report to"]):
        return "manager_info"

    if any(word in q for word in ["team member", "team members", "direct report", "direct reports"]):
        return "employee_list"

    if any(word in q for word in ["employee", "employees", "emplyoee", "emplyoees"]):
        return "employee_list"

    if any(phrase in q for phrase in ["job description of", "job title of", "designation of", "job role of", "what is job description", "what is job title"]):
        return "job_description"

    if any(phrase in q for phrase in ["job description", "job title", "designation", "job role"]):
        return "employee_list"

    # 🔥 Attendance
    if "attendance" in q:
        return "attendance"

    # 🔥 Leave
    if "leave" in q:
        return "leave_balance"

    # 🔥 DOB
    if "dob" in q or "date of birth" in q:
        return "dob"

    # ❌ REMOVE bad default
    return None

def should_use_fast_sql_path(metric: str):
    return metric in {"employee_list", "leave_balance", "attendance", "applied_leaves", "job_description", "manager_info", "employee_hierarchy"}

def extract_name_like_filter(query: str):
    match = re.search(
        r"\b(?:name\s+contain|name\s+contains|contain|contains|like|named|name\s+is)\s+([a-zA-Z]{2,}(?:\s+[a-zA-Z]{2,}){0,3})\b",
        query,
        re.IGNORECASE
    )

    if not match:
        return None

    value = match.group(1).strip().lower()
    return re.sub(r"\s+", " ", value)

def extract_job_title_filter(query: str):
    patterns = [
        r"\bwith\s+([a-zA-Z][a-zA-Z\s\-/]{1,60}?)\s+as\s+(?:job description|job title|designation|job role)\b",
        r"\b(?:job description|job title|designation|job role)\s+(?:is|as|like)\s+([a-zA-Z][a-zA-Z\s\-/]{1,60})\b",
        r"\bwith\s+([a-zA-Z][a-zA-Z\s\-/]{1,60}?)\s+(?:designation|job title|job role)\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if not match:
            continue

        value = re.sub(r"\s+", " ", match.group(1)).strip().lower()
        return value.strip(" -/")

    return None


def extract_manager_name(query: str):
    patterns = [
        r"team members?(?: name)? of\s+([a-zA-Z][a-zA-Z\s]{1,60})",
        r"direct reports?(?: name)? of\s+([a-zA-Z][a-zA-Z\s]{1,60})",
        r"reports? to\s+([a-zA-Z][a-zA-Z\s]{1,60})",
        r"manager(?: name)? of\s+([a-zA-Z][a-zA-Z\s]{1,60})",
        r"reporting manager of\s+([a-zA-Z][a-zA-Z\s]{1,60})"
    ]

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            name = match.group(1).strip().lower()
            return re.sub(r"\s+", " ", name)

    return None


def requires_employee_name_filter(metric: str, filters: dict):
    if metric == "employee_list":
        return False

    if metric == "job_description" and filters.get("job_title_like"):
        return False

    return True

def extract_fast_filters(query: str, metric: str):
    filters = {}
    q = query.lower()

    if metric == "leave_balance":
        if any(phrase in q for phrase in ["leave balance", "balance", "remaining leave", "remaining leaves", "leave remaining"]):
            filters["leave_view"] = "balance"
        elif any(phrase in q for phrase in ["leave taken", "leaves taken", "taken leave", "taken leaves", "availed"]):
            filters["leave_view"] = "taken"

    if metric == "employee_list":
        if "active" in q and "inactive" not in q:
            filters["status"] = "active"

        if "absent" in q:
            filters["attendance_status"] = "PL"
        
        if "privilege" in q:
            filters["attendance_status"] = "PL"

        if "sick" in q:
            filters["attendance_status"] = "SL"

        if "casual" in q:
            filters["attendance_status"] = "CL"

        if "present" in q and "absent" not in q:
            filters["attendance_status"] = "P"

        name_like = extract_name_like_filter(query)
        if name_like:
            filters["name_like"] = name_like

        job_title_like = extract_job_title_filter(query)
        if job_title_like:
            filters["job_title_like"] = job_title_like

        manager_name = extract_manager_name(query)
        if manager_name:
            filters["manager_name"] = manager_name

        if any(phrase in q for phrase in ["how many", "count", "number of"]):
            filters["result_mode"] = "count"

    if metric == "job_description":
        if any(phrase in q for phrase in ["how many", "count", "number of"]):
            filters["result_mode"] = "count"

        job_title_like = extract_job_title_filter(query)
        if job_title_like:
            filters["job_title_like"] = job_title_like

    return filters

def fallback_structured_intent(query: str):
    metric = detect_metric(query)

    return {
        "intent": metric,
        "employee_names": extract_employee_names(query),
        "filters": extract_fast_filters(query, metric) if metric else {},
        "date_range": extract_date_range(query)
    }


def handle_employee_hierarchy_query(query: str):
    names = extract_employee_names(query)
    if not names:
        return {
            "type": "text",
            "message": "Please specify an employee name for the hierarchy query."
        }

    user_ids, error = enforce_name_filter(query)
    if error:
        return {
            "type": "text",
            "message": error
        }

    if not user_ids:
        return {
            "type": "text",
            "message": "No employee found for the hierarchy query."
        }

    user_id = user_ids[0]
    sql = f"SELECT id, name, parent_path FROM api_users_hrdb WHERE id = {user_id}"
    result = run_sql(sql)
    rows = normalize_rows(result)

    if not rows:
        return {
            "type": "text",
            "message": "Unable to find hierarchy data for the specified employee."
        }

    row = rows[0]
    parent_path = row.get("parent_path") or ""
    if not parent_path:
        return {
            "type": "text",
            "message": f"No hierarchy path found for {row.get('name')}."
        }

    path_ids = [pid for pid in parent_path.split("/") if pid.strip()]
    if not path_ids:
        return {
            "type": "text",
            "message": f"No hierarchy path found for {row.get('name')}."
        }

    placeholders = ",".join(path_ids)
    manager_sql = f"SELECT id, name FROM api_users_hrdb WHERE id IN ({placeholders})"
    manager_result = run_sql(manager_sql)
    manager_rows = normalize_rows(manager_result)
    id_to_name = {str(r.get("id")): r.get("name") for r in manager_rows}
    chain = [id_to_name.get(pid, pid) for pid in path_ids]

    return {
        "type": "text",
        "message": f"Hierarchy for {row.get('name')}: {' > '.join(chain)}"
    }


def extract_structured_intent(query):
    prompt = f"""
    Extract structured intent from the query.

    Return JSON only.

    Supported intents:
    - attendance
    - leave_balance
    - employee_list
    - employee_info
    - manager_info
    - employee_hierarchy
    - applied_leaves
    - job_description
    

    Extract:
    - intent
    - employee_names (if any)
    - filters (status, name_like)
    - date_range (if any)

    Query: {query}
    """
    #- dob
    response = call_llm(prompt)
    if not response:
        return fallback_structured_intent(query)

    try:
        response = clean_llm_json(response)
        print("JSON response : ", response)
        return json.loads(response)
    except Exception:
        return fallback_structured_intent(query)

def clean_llm_json(response):
    if not response:
        raise ValueError("Empty response from LLM")

    # Remove markdown code blocks
    response = response.strip()

    if response.startswith("```"):
        response = response.replace("```json", "").replace("```", "").strip()

    # Extra safety (sometimes model adds text before JSON)
    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1:
        response = response[start:end+1]

    return response

def handle_sql_query(user_query, SCHEMA_PROMPT):
    """
    New LLM-based query handler.
    Flow: LLM (intent detection) → config-based SQL builder → execute
    """
    try:
        if not user_query["raw"].strip():
            return {
                "type": "text",
                "message": "Please enter a query"
            }

        query = user_query["raw"]

        # ===== STEP 1: Parse with LLM =====
        intent_data = parse_query_intelligent(query)
        print("Parsed intent data:", intent_data)
        intent_data = normalize_intent_data(intent_data)
        print("Normalized intent data:", intent_data)
        metric = intent_data.get("metric")
        entities = intent_data.get("entities", {})
        filters = intent_data.get("filters", {})
        date_range = intent_data.get("date_range")
        
        print(f"[Query Handler] metric={metric}, entities={entities}, filters={filters}")
        
        if not metric:
            return {
                "type": "text",
                "message": "Sorry, I couldn't understand what data you are looking for."
            }

        # ===== STEP 2: Handle special metric cases =====
        
        # Hierarchy query is handled specially
        if metric == "employee_hierarchy":
            employee_name = entities.get("employees", [None])[0]
            if not employee_name:
                return {"type": "text", "message": "Please specify an employee name for the hierarchy query."}
            return handle_employee_hierarchy_query(f"hierarchy of {employee_name}")
        
        # ===== STEP 3: Resolve entities to IDs =====
        
        user_ids = None
        
        # If employees are specified, resolve them to IDs
        if entities.get("employees"):
            employee_query = " ".join(entities["employees"])
            user_ids, error = enforce_name_filter(employee_query)
            if error:
                return {"type": "text", "message": error}
        
        # If manager is specified, resolve manager ID and set report_to_ids filter
        if entities.get("manager"):
            manager_ids, error = enforce_name_filter(entities["manager"])
            if error:
                return {"type": "text", "message": error}
            filters["report_to_ids"] = manager_ids
        
        # ===== STEP 4: Build SQL using config =====
        
        # Determine if we should skip LIMIT for this query
        should_skip = filters.get("should_skip_limit", False)
        
        sql_query = build_sql(metric, user_ids, date_range, filters)
        print(f"[Query Handler] Generated SQL: {sql_query}")
        
        # ===== STEP 5: Enforce LIMIT =====
        sql_query = enforce_limit(sql_query, skip_limit=should_skip)
        
        # ===== STEP 6: Validate SQL =====
        is_valid, msg = validate_sql_old(sql_query, skip_limit=should_skip)
        if not is_valid:
            print(f"[SQL Validation] Error: {msg}")
            return {
                "type": "text",
                "message": f"Unable to generate valid query: {msg}"
            }
        
        # ===== STEP 7: Execute SQL =====
        result = run_sql(sql_query)
        
        if result.get("error"):
            print(f"[SQL Execution] Error: {result['error']}")
            return {
                "type": "text",
                "message": f"Query execution error: {result['error']}"
            }
        
        # ===== STEP 8: Format response =====
        rows = normalize_rows(result)
        print(f"[Query Handler] Got {len(rows)} rows")
        
        return build_final_response(rows, query)

    except ValueError as e:
        return {
            "type": "text",
            "message": str(e)
        }
    except Exception as e:
        import traceback
        print(f"[Query Handler] Exception: {e}")
        traceback.print_exc()
        return {
            "type": "text",
            "message": f"Error processing request: {str(e)}"
        }


def enforce_limit(query: str, limit=10, skip_limit=False):
    q = query.strip().rstrip(";")

    if "LIMIT" not in q.upper() and not skip_limit:
        return q + f" LIMIT {limit};"

    return q


def should_skip_limit(metric: str, query: str, filters: dict):
    query_text = query.lower() if query else ""

    if filters and filters.get("result_mode") == "count":
        return False

    if metric == "employee_list":
        if filters and filters.get("report_to_ids"):
            return True
        if any(phrase in query_text for phrase in ["all team members", "all direct reports", "all employees", "all team", "complete team"]):
            return True

    return False

def validate_sql(sql_query: str, allowed_views=None):
    if not sql_query or not isinstance(sql_query, str):
        return False, "Empty SQL query"

    allowed_views = allowed_views or ALLOWED_SQL_VIEWS

    query = sql_query.strip()
    query_upper = query.upper()

    # 1. Only SELECT allowed
    if not query_upper.startswith("SELECT"):
        return False, "Only SELECT queries are allowed"

    # 2. Prevent multiple SQL statements
    if ";" in query[:-1]:
        return False, "Multiple SQL statements are not allowed"

    # 3. Block dangerous SQL keywords
    for keyword in BLOCKED_SQL_KEYWORDS:
        if re.search(rf"\b{keyword}\b", query_upper):
            return False, f"Blocked SQL keyword found: {keyword}"

    # 4. Block SELECT *
    if re.search(r"\bSELECT\s+\*", query_upper):
        return False, "SELECT * is not allowed"

    # 5. Must use at least one allowed view
    query_lower = query.lower()
    used_views = [
        view for view in allowed_views
        if re.search(rf"\b{re.escape(view.lower())}\b", query_lower)
    ]

    if not used_views:
        return False, "SQL does not use any allowed view"

    # 6. Block unknown table/view usage after FROM or JOIN
    referenced_tables = re.findall(
        r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        query,
        flags=re.IGNORECASE
    )

    for table in referenced_tables:
        if table not in allowed_views:
            return False, f"Unauthorized table/view used: {table}"

    # 7. Block UNION for now
    if re.search(r"\bUNION\b", query_upper):
        return False, "UNION queries are not allowed"

    return True, "SQL is valid"

def validate_sql_old(query: str, skip_limit=False) -> tuple[bool, str]:
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

    # must have LIMIT unless the caller intentionally skipped it
    if "LIMIT" not in q and not skip_limit:
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

    # Avoid a second LLM call for simple SQL table responses.
    if rows and base.get("type") == "table":
        summary = generate_summary(rows, user_query)
        base["summary"] = summary

    return base

def generate_summary(rows, user_query):
    query_text = user_query.lower()

    if rows and all("status" in row for row in rows):
        name = rows[0].get("name") or rows[0].get("u.name")
        status_counts = {}
        status_labels = {
            "P": "Present",
            "A": "Absent",
            "WO": "Weekly Off",
            "L": "Leave",
            "H": "Holiday",
            "HD": "Half Day"
        }

        for row in rows:
            status = str(row.get("status", "")).strip()
            if not status:
                continue
            status_counts[status] = status_counts.get(status, 0) + 1

        if status_counts:
            parts = []
            for status, count in sorted(status_counts.items()):
                label = status_labels.get(status, status)
                unit = "day" if count == 1 else "days"
                parts.append(f"{label} {count} {unit}")

            if name and len(status_counts) == 1 and sum(status_counts.values()) == 1:
                only_status = next(iter(status_counts))
                label = status_labels.get(only_status, only_status)
                return f"Attendance status for {name} is {label}."

            if name:
                return f"Attendance summary for {name}: {', '.join(parts)}."
            return ", ".join(parts) + "."

    if len(rows) == 1:
        row = rows[0]
        name = row.get("name") or row.get("u.name")

        value_parts = []
        for key, value in row.items():
            if key in {"name", "u.name"}:
                continue

            label = key.replace("total_", "").replace("_", " ")
            value_parts.append(f"{label}: {value}")

        if name and value_parts:
            return f"{name} -> {', '.join(value_parts)}."

        if value_parts:
            return ", ".join(value_parts) + "."

    name_values = []
    seen_names = set()
    for row in rows:
        name = row.get("name") or row.get("u.name")
        if name and name not in seen_names:
            seen_names.add(name)
            name_values.append(str(name))

    if name_values and any(word in query_text for word in ["employee", "employees", "name", "list", "show", "get"]):
        return f"Found {len(name_values)} matching employees: {', '.join(name_values)}."

    return f"Found {len(rows)} matching records."