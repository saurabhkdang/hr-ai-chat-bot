import requests
from config.schema import OLLAMA_URL, MODEL_NAME
from schema import get_schema
import ollama

#question = input("Ask HR question: ")
question = "please get the email of the employee whose named is similar to saurabh"

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
- Try to return the columns which are being asked only.

Database schema:
api_users_hrdb(id, name, email, report_to, dob)
# name: employee's full name
# email: employee's email address
# dob: date of birth of employee

Generate ONLY SQL query.

Question: {question}
"""

response = ollama.chat(
    model='phi',
    messages=[{"role": "user", "content": prompt}]
)

print(response['message']['content'])

# res = requests.post(OLLAMA_URL, json={
#     "model": MODEL_NAME,
#     "prompt": prompt,
#     "stream": False
# })

# print(res.json()["response"])