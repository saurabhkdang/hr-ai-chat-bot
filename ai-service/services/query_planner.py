from utils.name_extractor import extract_employee_names
from utils.date_parser import extract_date_range
from utils.metric_detector import detect_metric


def build_query_plan(query: str):
    plan = {
        "metric": None,
        "users": [],
        "date_range": {"start": None, "end": None},
        "filters": {},
        "comparison": False,
        "aggregation": None,
        "raw_query": query
    }

    metric = detect_metric(query)
    names = extract_employee_names(query)
    date_range = extract_date_range(query)

    plan["metric"] = metric
    plan["users"] = names
    plan["date_range"] = date_range or {"start": None, "end": None}

    if len(names) > 1:
        plan["comparison"] = True

    return plan