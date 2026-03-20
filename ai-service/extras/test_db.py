import os
import pymysql
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def test_db_connection():
    try:
        connection = pymysql.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
            cursorclass=pymysql.cursors.DictCursor
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 as test;")
            result = cursor.fetchone()

        connection.close()

        print("✅ Database connected successfully!")
        print("Test Query Result:", result)

    except Exception as e:
        print("❌ Database connection failed!")
        print("Error:", e)


if __name__ == "__main__":
    test_db_connection()