from router import route_question
from sql_agent import generate_sql
from sql_tool import run_sql
from vector_search import search_docs

def ask(question):

    route = route_question(question)

    if route == "sql":

        sql = generate_sql(question)
        result = run_sql(sql)

        return result

    else:

        docs = search_docs(question)

        return docs