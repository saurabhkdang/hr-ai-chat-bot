import requests
from config.schema import OLLAMA_URL, MODEL_NAME
from schema import get_schema
from utils.llm import ask_ai

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

    return ask_ai(prompt)

    """ res = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    })

    return res.json()["response"] """