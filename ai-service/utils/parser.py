import re
from datetime import datetime, timedelta

def extract_name(query: str):
    match = re.search(r"(of|for)\s+([a-zA-Z\s]+)", query.lower())
    return match.group(2).strip() if match else None


def extract_date_range(query: str):
    query = query.lower()
    today = datetime.today()

    # last N days
    match = re.search(r"last (\d+) days", query)
    if match:
        days = int(match.group(1))
        start = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        return {"start": start, "end": end}

    # till today
    if "till today" in query or "until today" in query:
        return {"start": None, "end": today.strftime('%Y-%m-%d')}

    return None


def is_explanation_query(query: str):
    keywords = ["what", "why", "how", "policy", "rules", "explain"]
    return any(k in query.lower() for k in keywords)


def parse_query(query: str):
    if not query:   # 👈 handles None, "", etc
        return {
            "raw": "",
            "name": None,
            "date_range": None,
            "needs_explanation": False
        }
        
    return {
        "raw": query,
        "name": extract_name(query),
        "date_range": extract_date_range(query),
        "needs_explanation": is_explanation_query(query)
    }