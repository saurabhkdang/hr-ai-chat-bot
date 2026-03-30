def format_response(rows, user_query):
    response_type = detect_response_type(rows)

    if response_type == "empty":
        return {
            "type": "text",
            "message": "No data found."
        }

    elif response_type == "single_value":
        key = list(rows[0].keys())[0]
        value = rows[0][key]

        return {
            "type": "text",
            "message": f"{key.replace('_', ' ').title()}: {value}"
        }

    else:
        columns = [prettify_column(c) for c in rows[0].keys()]
        return {
            "type": "table",
            "columns": list(columns),
            "rows": [list(row.values()) for row in rows]
        }

def prettify_column(col):
    return col.replace("_", " ").title()

def detect_response_type(rows):
    if not rows:
        return "empty"

    if len(rows) == 1 and len(rows[0]) == 1:
        return "single_value"

    return "table"