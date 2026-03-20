import pymysql
from config import DB_CONFIG
import os

def run_sql(query):

    if not query.strip().lower().startswith("select"):
        return "Only SELECT queries allowed"

    #conn = pymysql.connect(**DB_CONFIG)
    connection = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

    cursor = connection.cursor()
    # cursor = conn.cursor()
    #query = "select name from api_users_hrdb where id = 124;"
    print("Executing query:", query)
    cursor.execute(query)
    result = cursor.fetchall()

    connection.close()

    return result