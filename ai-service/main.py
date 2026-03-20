from fastapi import FastAPI
from router import route_question
from sql_agent import generate_sql
from sql_tool import run_sql
from vector_search import search_docs
from rag_answer import generate_answer

app = FastAPI()

@app.post("/ask")
def ask(data: dict):

    question = data["question"]

    route = route_question(question)

    if route == "sql":

        sql = generate_sql(question)
        
        # Remove markdown ```sql ``` blocks
        if sql.startswith("```"):
            sql = sql.replace("```sql", "").replace("```", "").strip()

        # Remove leading "sql"
        if sql.lower().startswith("sql"):
            sql = sql[3:].strip()

        print(sql)

        db_result = run_sql(sql)
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