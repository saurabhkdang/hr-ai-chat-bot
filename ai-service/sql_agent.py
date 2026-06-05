import requests
from config.schema import OLLAMA_URL, MODEL_NAME
from schema import get_schema
# from utils.llm import ask_ai
from utils.llm_service import call_llm
from utils.entity_extractor import extract_employee_names
from config.schema import get_db_config
from sql_tool import run_sql
import re
# from dotenv import load_dotenv
# import os
# import pymysql

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

def enforce_name_filter(query):
    names = extract_employee_names(query)

    print("Extracted names for filtering:", names)

    if not names:
        return None, "Please specify employee name."

    user_ids = []

    for name in names:
        # 🔥 Clean again (double safety)
        name = name.lower().strip()
        name = re.sub(r'\s+', ' ', name)

        sql = """
            SELECT id, name
            FROM api_users_hrdb
            WHERE LOWER(name) LIKE %s
        """

        param = f"%{name}%"

        print(f"Running SQL for name: {name}")

        result = run_sql(sql, [param])

        print("Users found:", result)

        if result and result.get("data"):
            for u in result["data"]:
                user_ids.append(str(u["id"]))

    if not user_ids:
        return None, "No employee found."

    # 🔥 Remove duplicates
    user_ids = list(set(user_ids))

    print("Final user_ids:", user_ids)

    return user_ids, None

def inject_user_filter(sql, user_ids):
    condition = f"u.id IN ({','.join(user_ids)})"

    # Normalize
    sql = sql.strip().rstrip(";")

    # Regex to find ORDER BY or LIMIT
    match = re.search(r"\b(order\s+by|limit)\b", sql, re.IGNORECASE)

    if match:
        split_index = match.start()
        before = sql[:split_index].strip()
        after = sql[split_index:].strip()
    else:
        before = sql
        after = ""

    # Inject condition into WHERE
    if "where" in before.lower():
        before += f" AND {condition}"
    else:
        before += f" WHERE {condition}"

    # Rebuild query
    final_sql = f"{before} {after}".strip()

    return final_sql

# def generate_sql_with_ids(query, user_ids, metric_info, schema_prompt):
#     user_filter = ""

#     if user_ids:
#         ids = ", ".join(map(str, user_ids))
#         user_filter = f"AND u.id IN ({ids})"

#     prompt = f"""
#     Generate SQL query.

#     RULES:
#     - ALWAYS use alias 'u' for users table
#     - ALWAYS include: {user_filter}
#     - Do NOT change alias

#     Query: {query}
#     """

#     return call_llm(prompt)

def generate_sql_strict(user_query, schema_prompt):

    user_ids, error = enforce_name_filter(user_query)
    print("User IDs for filtering:", user_ids, "Error:", error)

    if error:
        raise ValueError(error)

    user_filter = ""

    if user_ids:
        ids = ", ".join(map(str, user_ids))
        user_filter = f"AND u.id IN ({ids})"

    prompt = f"""
    You are an expert SQL generator.

    STRICT RULES:
    - Only generate MySQL SELECT queries
    - NEVER use SELECT *
    - Use ONLY columns from schema
    - ALWAYS include: {user_filter}
    - ALWAYS use table aliases (u, a, etc.)
    - ALWAYS prefix column names with table alias
    - NEVER use ambiguous column names
    - If multiple tables have same column, choose correct table based on context
    - ALWAYS include WHERE if name/date present
    - If only month and year are given:
        → Use date range (BETWEEN or >= and <)
    - Do NOT assume a single day
    - Always include full date format YYYY-MM-DD
    - NEVER hallucinate columns
    - DO NOT explain anything
    - ALWAYS use 'u' as alias for users table
    - NEVER use u1, u2, usr, etc.
    DATE RULES:
    - NEVER use incomplete dates like '2023-10'
    - ALWAYS use full date format 'YYYY-MM-DD'
    - If month is given, use:
    BETWEEN 'YYYY-MM-01' AND 'YYYY-MM-31'

    CONSISTENCY RULE:
    - Opening and closing must be from SAME month
    - NEVER mix different months in same query

    COLUMN RULE:
    - Use only actual columns from schema
    - DO NOT invent columns like opening_month or closing_month

    Schema:
    {schema_prompt}

    User Query:
    {user_query}

    Return ONLY SQL.
    """
    # - Add LIMIT 10
    response = call_llm(prompt)

    # clean response
    response = response.replace("```sql", "").replace("```", "").strip()

    if response.lower().startswith("sql"):
        response = response[3:].strip()

    # 🧹 Clean response (VERY IMPORTANT)
    if "```" in response:
        response = response.split("```")[-2]

    print("Generated SQL:", response)
    
    # db = pymysql.connect(**get_db_config())
    # cursor = db.cursor()
    
    # db.close()

    response = response.strip().rstrip(";")

    # Inject into SQL
    response = inject_user_filter(response, user_ids)


    return response

def generate_sql(question, schema_prompt):

    # schema = get_schema()
    # print('below is schema')
    # print(schema)
    prompt = f"""
You are an HR SQL expert.

Rules:
- Do not use any other table names except in the given schema
- Use only given tables and columns
- Do not assume any columns
- Return ONLY SQL query (no explanation)
- DO NOT include:
    - 'sql'
    - backticks (```)
    - explanations
    - formatting
- Date Handling Rules (STRICT):
    - NEVER use MONTH(), YEAR(), or DATE() functions for filtering
    - ALWAYS convert month/year into full date range
    - ALWAYS use BETWEEN for date filtering
- Output must start directly with SELECT
- Try to return the columns which are being asked only.

Database schema:
{schema_prompt}

Generate ONLY SQL query.

Question: {question}
"""

# Table Name : api_users_hrdb
# Field : id, name, email, report_to, dob

    return call_llm(prompt)

    """ res = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    })

    return res.json()["response"] """