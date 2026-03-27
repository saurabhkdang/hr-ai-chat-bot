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

ALLOWED_SCHEMA = {
    "api_users_hrdb": {
        "description": "Employee master table",
        "columns": {
            "id": "Unique employee ID",
            "name": "Employee full name",
            "email": "Employee email address",
            "report_to": "Manager ID (reports to)",
            "jd_id": "Job description ID",
            "dob" : "date of birth"
        }
    },

    "api_job_description": {
        "description": "Job roles and titles",
        "columns": {
            "id": "Job description ID",
            "job_title": "Title of the job role"
        }
    },

    "hrdb_job_description_details": {
        "description": "Detailed job responsibilities and skills",
        "columns": {
            "id": "Primary key",
            "jd_id": "Job description ID (foreign key)",
            "type": "Type of detail (e.g., skill, responsibility)",
            "description": "Detailed description of the job requirement"
        }
    },

    "hrdb_users_attendance": {
        "description": "Daily attendance records of employees",
        "columns": {
            "id": "Primary key",
            "user_id": "Employee ID",
            "attendance_date": "Date of attendance",
            "status": "Attendance status (Present, Absent, Leave, etc.)"
        }
    },

    "hrdb_attendance_metrics": {
        "description": "Monthly leave and attendance summary",
        "columns": {
            "id": "Primary key",
            "user_id": "Employee ID",
            "month_year": "Month and year of record",

            "closing_sl": "Sick Leave balance (SL = Sick Leave)",
            "closing_cl": "Casual Leave balance (CL = Casual Leave)",
            "closing_pl": "Privileged Leave balance (PL = Privileged Leave)",

            "availed_sl": "Sick Leave taken",
            "availed_cl": "Casual Leave taken",
            "availed_pl": "Privileged Leave taken",

            "accural_sl": "Sick Leave earned/accrued",
            "accural_cl": "Casual Leave earned/accrued",
            "accural_pl": "Privileged Leave earned/accrued",

            "opening_sl": "Opening Sick Leave balance",
            "opening_cl": "Opening Casual Leave balance",
            "opening_pl": "Opening Privileged Leave balance"
        }
    }
}