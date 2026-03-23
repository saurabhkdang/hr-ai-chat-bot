from dotenv import load_dotenv
load_dotenv()
import pymysql
from config import get_db_config
import os

def get_schema():

    # conn = pymysql.connect(**DB_CONFIG)
    # cursor = conn.cursor()

    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
            cursorclass=pymysql.cursors.DictCursor
        )

        cursor = connection.cursor()

        #cursor.execute("SHOW TABLES")
        #tables = cursor.fetchall()
        # print("test")
        # print(tables)
        schema = ""

        tables = ["api_users_hrdb"
        # , "hrdb_annual_review", 
        # "hrdb_jd_pay_grade", 
        # "hrdb_job_description_details", 
        # "hrdb_monthly_accural", 
        # "hrdb_users_attendance", 
        # "hrdb_users_leaves", 
        # "hrdb_users_salary"
        ]

        for table in tables:
            # table_name = list(table.values())[0]
            table_name = table
            # print(table_name)
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            cols = [col['Field'] for col in columns]

            schema += f"{table_name}({', '.join(cols)})\n"

        conn.close()
        print('below schema')
        print(schema)

        return schema
        # with connection.cursor() as cursor:

        # connection.close()

        #print("✅ Database connected successfully!")
        # print("Test Query Result:", result)
    except Exception as e:
        return e
        #print("❌ Database connection failed!")
        #print("Error:", e)

    

    # return schema