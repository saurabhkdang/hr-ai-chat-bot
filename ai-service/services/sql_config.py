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

METRIC_CONFIG = {
    "attendance": {
        "table": "hrdb_users_attendance",
        "alias": "att",
        "column": "status",  # or present_days based on your schema
        "date_column": "attendance_date"
    },
    "leave_balance": {
        "table": "hrdb_attendance_metrics",
        "alias": "a",
        "aggregation": "SUM",
        "aggregation_columns": {
            "availed_pl": "total_availed_pl",
            "availed_cl": "total_availed_cl",
            "availed_sl": "total_availed_sl"
        },
        "group_by": ["u.id", "u.name"],
        "date_column": "month_year",
    },
    "employee_list": {
        "table": "api_users_hrdb",
        "alias": "u",
        "column": "name",
        "date_column": None
    },

    "employee_info": {
        "table": "api_users_hrdb",
        "alias": "u",
        "column": ["dob"],  # extend later
        "date_column": None
    },

    "applied_leaves": {
        "table": "hrdb_users_leaves",   # 👈 your table name
        "alias": "l",
        "columns": [
            "start_date",
            "end_date",
            "total_days"
        ],
        "date_column": "start_date",  # primary filter column
        "type": "range"               # 🔥 important (explained below)
    }
}