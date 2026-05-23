# "dob": {
#     "table": "api_users_hrdb",
#     "alias": "u",
#     "column": "dob",
#     "date_column": None
# },
# "leave_balance": {
#     "table": "hrdb_attendance_metrics",
#     "alias": "a",
#     "column": "closing_pl",
#     "date_column": "month_year"
# },



# "leave_taken": {
#     "table": "hrdb_users_leaves",
#     "alias": "l",
#     "column": "total_days",  # confirm your schema
#     "columns": [
#         "start_date",
#         "end_date",
#         "total_days"
#     ],
#     "aggregation": "SUM"
# },

TABLE_INFO = {
    "employees": "this is the table having all employees",
    "employee_attendance_leaves_status" : "table to have all employee attendance status of all days",
    "employees_job_details" : "table to have all data related to employee job details"
}

METRIC_CONFIG = {
    "attendance": {
        "description": "Query attendance records and status for employees",
        "table": "hrdb_users_attendance",
        "alias": "att",
        "column": "status",
        "date_column": "attendance_date"
    },
    "leave_balance": {
        "description": "Query leave balance (balance or taken) for employees",
        "table": "hrdb_attendance_metrics",
        "alias": "a",
        "aggregation": "SUM",
        "aggregation_column_groups": {
            "balance": {
                "closing_pl": "total_closing_pl",
                "closing_cl": "total_closing_cl",
                "closing_sl": "total_closing_sl"
            },
            "taken": {
                "availed_pl": "total_availed_pl",
                "availed_cl": "total_availed_cl",
                "availed_sl": "total_availed_sl"
            }
        },
        "group_by": ["u.id", "u.name"],
        "date_column": "month_year",
    },
    "employee_list": {
        "description": "List employees with filters (active, absent, job title, team members, etc.)",
        "table": "api_users_hrdb",
        "alias": "u",
        "column": "name",
        "date_column": None
    },

    "employee_info": {
        "description": "Get employee information (DOB, email, contact, manager)",
        "table": "api_users_hrdb",
        "alias": "u",
        "column": ["dob", "name", "email", "report_to"],
        "date_column": None
    },

    "manager_info": {
        "description": "Get manager information for employees",
        "table": "api_users_hrdb",
        "alias": "u",
        "select_expressions": [
            "u.name as employee_name",
            "mgr.name as manager_name"
        ],
        "joins": [
            {
                "table": "api_users_hrdb",
                "alias": "mgr",
                "on": "u.report_to = mgr.id"
            }
        ],
        "date_column": None
    },

    "job_description": {
        "description": "Query job descriptions and details by job title",
        "table": "api_job_description",
        "alias": "jd",
        "select_expressions": [
            "jd.job_title",
            "jdd.type",
            "jdd.description"
        ],
        "mode_joins": {
            "count": []
        },
        "join_on": "u.jd_id = jd.id",
        "joins": [
            {
                "table": "hrdb_job_description_details",
                "alias": "jdd",
                "on": "jd.id = jdd.jd_id"
            }
        ],
        "date_column": None
    },

    "applied_leaves": {
        "description": "Query applied leaves with date range",
        "table": "hrdb_users_leaves",
        "alias": "l",
        "columns": [
            "start_date",
            "end_date",
            "total_days"
        ],
        "date_column": "start_date",
        "type": "range"
    },

    "employee_hierarchy": {
        "description": "Get hierarchy/reporting chain for an employee",
        "table": "api_users_hrdb",
        "alias": "u",
        "column": "name",
        "date_column": None
    }
    
}