from dotenv import load_dotenv
import os
import pymysql

load_dotenv()

# -------- MYSQL (DYNAMIC) --------
def get_db_config():
    return {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "cursorclass": pymysql.cursors.DictCursor
    }

QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi"

COLLECTION_NAME = "hr_docs"