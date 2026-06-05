from dotenv import load_dotenv
import os
import pymysql
# from config.schema import get_db_config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

def get_db_connection():

    host = os.getenv("DB_HOST")
    port = int(os.getenv("DB_PORT"))
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    database_schema = os.getenv("DB_NAME")

    connection = pymysql.connect(
        host=host,
        user=username,
        password=password,
        database=database_schema,
        port=port,
        cursorclass=pymysql.cursors.DictCursor,
        ssl_disabled=True
    )

    return connection

def get_table_info(table_names):

    connection = get_db_connection()

    cursor = connection.cursor()

    schema_info = ""

    for table in table_names:

        # GET CREATE TABLE / VIEW
        cursor.execute(f"SHOW CREATE TABLE {table}")

        result = cursor.fetchone()

        create_statement = list(result.values())[1]

        schema_info += f"\n\n{create_statement}"

    connection.close()

    return schema_info

def run_sql(query, params=None):

    if not query.strip().lower().startswith("select"):
        return "Only SELECT queries allowed"

    try:
        
        connection = get_db_connection()
        print("conn : " , connection)
        cursor = connection.cursor()

        print("Executing query:", query)
        query = query.replace("%", "%%")
        cursor.execute(query, params or [])
        
        result = cursor.fetchall()
        print("Result : ", result)
        return {"data": result}
    
    except Exception as e:
        return {
            "error": str(e),
            "query": query
        }
    finally:
        if connection:
            connection.close()