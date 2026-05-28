from services.sql_config import METRIC_CONFIG, TABLE_INFO
from utils.llm_call import call
from sql_tool import get_table_info

def detect_tables(question):
    prompt = f"""
You are a database assistant.

Available tables:
{TABLE_INFO}

Tasks:
1. Understand the user question even if spelling mistakes exist
2. Correct spelling mentally before reasoning
3. Identify relevant tables

Return JSON only in below format:

{{
    "normalized_question": "corrected question here",
    "tables": ["table1","table2"]
}}

Rules:
- No explanation
- JSON only
- Do not wrap JSON inside markdown
- Table names must come only from available tables list

Question:
{question}
"""

    content = call(prompt, "json")

    if not content:
        raise ValueError("Unable to detect relevant SQL view.")

    if isinstance(content, str):
        import json

        cleaned = content.strip()

        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")

        if start != -1 and end != -1:
            cleaned = cleaned[start:end + 1]

        content = json.loads(cleaned)

    tables = content.get("tables", [])

    if not tables:
        raise ValueError("No relevant SQL view detected.")

    allowed_tables = set(TABLE_INFO.keys())

    valid_tables = [
        table for table in tables
        if table in allowed_tables
    ]

    if not valid_tables:
        raise ValueError("Detected SQL view is not allowed.")

    return {
        "normalized_question": content.get("normalized_question", question),
        "tables": valid_tables
    }

def get_sql_query(schema, question):
    prompt = f"""
Based on the table schema below, write a SQL query that answers the user's question.

Business Semantics:
- Use attendance_category for leave/work/holiday related filtering
- attendance_category values:
    - LEAVE
    - WORK
    - HOLIDAY

Important Query Rules:
- For employee name searches, use LIKE instead of exact match
- Use partial matching for names
- Example:
    employee_name LIKE '%Rahul%'    

STRICT SQL RULES:
- Return ONLY SQL query
- No explanation
- Single line only
- No markdown
- Use SELECT only
- NEVER use SELECT *
- Always explicitly list required columns
- Use only columns present in the schema
- Use only the provided table/view schema
- Add LIMIT 100 unless the query uses COUNT, SUM, AVG, MIN, or MAX
- If user asks attendance, include employee name, attendance date/status/category columns if available
- If user asks employee list, include employee name and relevant requested columns only

Important View Behavior:
- Some views may contain multiple rows per employee because of related records like tasks, leave entries, attendance entries, or designation mappings.
- When user asks for employee lists, employee names, managers, or people, avoid duplicate employee rows.

Rules:
- Return ONLY SQL query
- No explanation
- Single line only
- No markdown

Schema:
{schema}

Question:
{question}

SQL Query:
"""
    sql_query = call(prompt, "string")
    return sql_query

def build_sql_updated(question):

    result = detect_tables(question)

    normalized_question = result["normalized_question"]

    table_list = result["tables"]

    schema = get_table_info(table_list)

    sql = get_sql_query(schema, question)

    resp = {
        "sql": sql.strip(),
        "tables": table_list,
        "normalized_question": normalized_question
    }

    return resp

def build_sql(metric, user_ids=None, date_range=None, filters=None):
    config = METRIC_CONFIG.get(metric)

    if not config:
        raise ValueError(f"Unsupported metric: {metric}")

    table = config["table"]
    alias = config["alias"]
    date_column = config.get("date_column")
    group_by = config.get("group_by", [])
    join_on = config.get("join_on", f"u.id = {alias}.user_id")
    extra_joins = list(config.get("joins", []))
    filters = filters or {}
    result_mode = filters.get("result_mode")
    if config.get("mode_joins") and result_mode in config["mode_joins"]:
        extra_joins = config["mode_joins"][result_mode]

    if table == "api_users_hrdb":
        if filters.get("job_title_like"):
            extra_joins.append({"table": "api_job_description", "alias": "jd", "on": "u.jd_id = jd.id"})
        if filters.get("attendance_status"):
            extra_joins.append({"table": "hrdb_users_attendance", "alias": "att", "on": "u.id = att.user_id"})

    aggregation_columns = config.get("aggregation_columns")

    if config.get("aggregation_column_groups"):
        leave_view = filters.get("leave_view", "taken")
        aggregation_columns = config["aggregation_column_groups"].get(leave_view)

    # 🔥 SELECT clause
    if result_mode == "count":
        cols = "COUNT(DISTINCT u.id) as employee_count"

    elif config.get("select_expressions"):
        cols = ", ".join(config["select_expressions"])

    elif config.get("aggregation") == "SUM" and aggregation_columns:
        cols = ", ".join(
            f"SUM({alias}.{column}) as {result_alias}"
            for column, result_alias in aggregation_columns.items()
        )

    elif config.get("aggregation") == "SUM":
        cols = f"SUM({alias}.{config['aggregation_column']}) as total_value"

    elif "columns" in config:
        cols = ", ".join([f"{alias}.{c}" for c in config["columns"]])

    elif "column" in config:
        cols = f"{alias}.{config['column']}"

    else:
        raise ValueError(f"No column defined for metric: {metric}")

    select_columns = cols
    if table != "api_users_hrdb" and result_mode != "count":
        select_columns = f"u.name, {cols}"

    sql = f"""
    SELECT {select_columns}
    FROM api_users_hrdb u
    """

    # 🔥 JOIN
    if table != "api_users_hrdb":
        sql += f"""
        JOIN {table} {alias} ON {join_on}
        """

    for join in extra_joins:
        sql += f"""
        JOIN {join['table']} {join['alias']} ON {join['on']}
        """

    sql += " WHERE 1=1 and u.status = 1 "  # only active employees by default

    # 🔥 User filter
    if user_ids:
        ids = ",".join(map(str, user_ids))
        sql += f" AND u.id IN ({ids}) "

    # 🔥 Date filter (fixed)
    print("Date range:", date_range)
    if date_range:
        start = date_range.get("start")
        end = date_range.get("end")
        print("Start:", start, "End:", end)
        if config.get("type") == "range":
            sql += f"""
            AND (
                {alias}.start_date <= '{end}'
                AND {alias}.end_date >= '{start}'
            )
            """
        elif date_column and start and end:
            sql += f" AND {alias}.{date_column} BETWEEN '{start}' AND '{end}' "
        elif date_column and not start and end:
            sql += f" AND {alias}.{date_column} <= '{end}' "
        elif date_column and start and not end:
            sql += f" AND {alias}.{date_column} >= '{start}' "

    if table == "api_users_hrdb" and filters.get("attendance_status") and date_range:
        # start, end = date_range
        if start and end:
            sql += f" AND att.attendance_date BETWEEN '{start}' AND '{end}' "

    # 🔥 Filters
    if filters:
        print("Filters: ", filters)
        for key, value in filters.items():
            if value is None:
                continue
            if isinstance(value, str) and value.strip().lower() in {"", "none"}:
                continue
            if key == "report_to_ids" and not value:
                continue

            if key == "status" and value == "active":
                sql += " AND u.status = 1 "

            elif key == "name_like":
                escaped_value = str(value).replace("'", "''")
                sql += f" AND u.name LIKE '%%{escaped_value}%%' "

            elif key == "job_title_like":
                escaped_value = str(value).replace("'", "''").lower()
                sql += f" AND LOWER(jd.job_title) LIKE '%%{escaped_value}%%' "

            elif key == "attendance_status":
                status_value = str(value).upper()
                if status_value == "ABSENT":
                    status_value = "PL"
                if status_value == "A":
                    status_value = "PL"
                sql += f" AND att.status = '{status_value}' "

            elif key == "report_to_ids":
                ids = ",".join(map(str, value))
                sql += f" AND u.report_to IN ({ids}) "

    if group_by and result_mode != "count":
        sql += " GROUP BY " + ", ".join(group_by)

    return sql.strip()

def build_sql11(metric, user_ids=None, date_range=None, filters=None):
    config = METRIC_CONFIG.get(metric)

    if not config:
        raise ValueError(f"Unsupported metric: {metric}")

    table = config["table"]
    alias = config["alias"]
    # column = config["column"]
    date_column = config["date_column"]

    # 🔥 Handle multiple columns OR single column

    if "columns" in config:
        cols = ", ".join([f"{alias}.{c}" for c in config["columns"]])
    elif config.get("aggregation") == "SUM":
        cols = f"SUM({alias}.{config['aggregation_column']}) as total_value"
    else:
        cols = f"{alias}.{config['column']}"

    # Base query
    sql = f"""
    SELECT u.name, {cols}
    FROM api_users_hrdb u
    """

    # Join if needed
    if table != "api_users_hrdb":
        sql += f"""
        JOIN {table} {alias} ON u.id = {alias}.user_id
        """

    # WHERE clause
    sql += " WHERE 1=1 "

    # User filter
    if user_ids:
        ids = ",".join(map(str, user_ids))
        sql += f" AND u.id IN ({ids}) "

    # Date filter
    if date_range and date_column:
        start, end = date_range
        if start and end:
            sql += f" AND {alias}.{date_column} BETWEEN '{start}' AND '{end}' "

    if date_range and config.get("type") == "range":
        start, end = date_range

        sql += f"""
        AND (
            {alias}.start_date <= '{end}'
            AND {alias}.end_date >= '{start}'
        )
        """

    # Extra filters
    if filters:
        for f in filters:
            sql += f" AND {f} "

    return sql.strip()