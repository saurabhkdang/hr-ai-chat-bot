from dotenv import load_dotenv
import os
import pymysql
from config.schema import get_db_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

def run_sql(query, params=None):

    if not query.strip().lower().startswith("select"):
        return "Only SELECT queries allowed"


    try:
        
        connection = pymysql.connect(**get_db_config())
        print("conn : " , connection)
        cursor = connection.cursor()

        print("Executing query:", query)
        cursor.execute(query, params or [])

        result = cursor.fetchall()
        connection.close()

        return {"data": result}
    
    except Exception as e:
        return {
            "error": str(e),
            "query": query
        }