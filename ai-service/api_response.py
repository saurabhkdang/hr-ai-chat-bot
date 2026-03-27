def format_for_api(rows):
    if not rows:
        return {
            "type": "table",
            "columns": [],
            "rows": []
        }

    return {
        "type": "table",
        "columns": list(rows[0].keys()),
        "rows": [list(row.values()) for row in rows]
    }