from fastapi import FastAPI
from router import route_question
from sql_agent import generate_sql
from sql_tool import run_sql
from vector_search import search_docs
from rag_answer import generate_answer
from ai_client import ask_ai 

app = FastAPI()

@app.post("/ask")
def ask(data: dict):

    question = data["question"]

    route = route_question(question)

    if route == "sql":

        sql = generate_sql(question)
        print("Generated SQL:", sql)

        db_result = run_sql(sql)

        if "error" in db_result:
            print("SQL Error:", db_result["error"])

            fix_prompt = f"""
The following SQL query failed.

Query:
{db_result['query']}

Error:
{db_result['error']}

Fix the SQL query. Return ONLY corrected SQL.
"""

            fixed_sql = ask_ai(fix_prompt)

            print("Fixed SQL:", fixed_sql)

            db_result = run_sql(fixed_sql)
        
        
        context = str(db_result)
        print(context)

    else:

        chunks = search_docs(question)
        context = "\n".join(chunks)

    answer = generate_answer(question, context)

    return {
        "route": route,
        "answer": answer
    }