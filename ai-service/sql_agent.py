import requests
from config import OLLAMA_URL, MODEL_NAME
from schema import get_schema
from ai_client import ask_ai

def generate_sql(question):

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
- Output must start directly with SELECT
- Try to return the columns which are being asked only.

Database schema:
Table Name : api_users_hrdb
Field : id, name, email, report_to, dob
# name: employee's full name
# email: employee's email address
# dob: date of birth of employee

Generate ONLY SQL query.

Question: {question}
"""

    return ask_ai(prompt)

    """ res = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    })

    return res.json()["response"] """