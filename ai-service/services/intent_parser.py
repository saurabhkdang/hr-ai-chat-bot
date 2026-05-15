import json
import re
from datetime import datetime, timedelta
import calendar
from utils.llm_service import call_llm
from services.sql_config import METRIC_CONFIG
from utils.entity_extractor import extract_employee_names


def extract_date_range_local(query: str):
    """Extract date range from query string. Local version to avoid circular import."""
    query = query.lower()
    today = datetime.today()

    # 1. last N days
    match = re.search(r"last (\d+) days", query)
    if match:
        days = int(match.group(1))
        start = (today - timedelta(days=days)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        return {"start": start, "end": end}

    # 2. last N months
    match = re.search(r"last (\d+) months", query)
    if match:
        months = int(match.group(1))
        start = (today - timedelta(days=30 * months)).strftime('%Y-%m-%d')
        end = today.strftime('%Y-%m-%d')
        return {"start": start, "end": end}

    # 3. till today
    if "till today" in query or "until today" in query:
        return {"start": None, "end": today.strftime('%Y-%m-%d')}

    # 4. specific date (23rd March 2026 or 9th May)
    match = re.search(r"on (\d{1,2})(st|nd|rd|th)? (\w+)(?: (\d{4}))?", query)
    if match:
        day = int(match.group(1))
        month_str = match.group(3)
        year = int(match.group(4)) if match.group(4) else today.year

        try:
            date_obj = datetime.strptime(f"{day} {month_str} {year}", "%d %B %Y")
        except:
            try:
                date_obj = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
            except:
                return None

        date_str = date_obj.strftime('%Y-%m-%d')
        return {"start": date_str, "end": date_str}

    # 5. month + year (feb 2026 / february 2026)
    match = re.search(r"in (\w+) (\d{4})", query)
    if match:
        month_str = match.group(1)
        year = int(match.group(2))

        try:
            month = datetime.strptime(month_str, "%B").month
        except:
            try:
                month = datetime.strptime(month_str, "%b").month
            except:
                return None

        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day)

        return {"start": start_date.strftime('%Y-%m-%d'), "end": end_date.strftime('%Y-%m-%d')}

    # 6. only month (assume current year)
    match = re.search(r"in (\w+)", query)
    if match:
        month_str = match.group(1)

        try:
            month = datetime.strptime(month_str, "%B").month
        except:
            try:
                month = datetime.strptime(month_str, "%b").month
            except:
                return None

        year = today.year
        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day)

        return {"start": start_date.strftime('%Y-%m-%d'), "end": end_date.strftime('%Y-%m-%d')}

    return None


def build_metric_descriptions():
    """Generate human-readable descriptions of available metrics"""
    descriptions = []
    for metric, config in METRIC_CONFIG.items():
        desc = f"- {metric}: {config.get('description', 'Query for ' + metric)}"
        descriptions.append(desc)
    return "\n".join(descriptions)


def parse_query_intelligent(query: str):
    """
    Use LLM to parse query into structured intent.
    LLM maps user query to one of the available metrics in METRIC_CONFIG.
    Returns: {metric, entities, filters, date_range}
    """
    
    available_metrics = list(METRIC_CONFIG.keys())
    metric_descriptions = build_metric_descriptions()
    
    prompt = f"""
    You are an HR database chatbot parser.
    
    Your task: Parse the user query and extract:
    1. Which HR metric/intent applies
    2. Entity names (employee names, manager names, job titles)
    3. Relevant filters
    4. Date range if mentioned
    
    Available metrics (intents):
    {metric_descriptions}
    
    Rules:
    - Return ONLY valid JSON
    - Map user intent to ONE metric from available metrics
    - Extract all employee/manager names mentioned
    - Extract job titles if mentioned
    - Identify filter keywords (active, inactive, absent, present, privilege, sick, casual)
    - If asking "how many" or "count", set result_mode: "count"
    - If asking for "all", set should_skip_limit: true
    - DO NOT generate SQL
    
    Response format:
    {{
        "metric": "<metric_name>",
        "entities": {{
            "employees": ["name1", "name2"],
            "manager": "manager_name",
            "job_title": "title"
        }},
        "filters": {{
            "status": "active|inactive",
            "attendance_status": "P|A|PL|SL|CL",
            "job_title_like": "title_pattern",
            "result_mode": "count|list",
            "leave_view": "balance|taken",
            "should_skip_limit": true|false
        }},
        "date_range": {{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}}
    }}
    
    Examples:
    
    Query: "show all team members of manoj"
    → {{"metric": "employee_list", "entities": {{"manager": "manoj"}}, "filters": {{"should_skip_limit": true}}, "date_range": null}}
    
    Query: "how many employees are absent today"
    → {{"metric": "employee_list", "entities": {{}}, "filters": {{"attendance_status": "A", "result_mode": "count"}}, "date_range": {{"start": "2026-05-14", "end": "2026-05-14"}}}}
    
    Query: "leave balance of saurabh"
    → {{"metric": "leave_balance", "entities": {{"employees": ["saurabh"]}}, "filters": {{"leave_view": "balance"}}, "date_range": null}}
    
    Query: "job description of backend engineer"
    → {{"metric": "job_description", "entities": {{"job_title": "backend engineer"}}, "filters": {{"job_title_like": "backend engineer"}}, "date_range": null}}
    
    Query: "hierarchy of saurabh till top"
    → {{"metric": "employee_hierarchy", "entities": {{"employees": ["saurabh"]}}, "filters": {{}}, "date_range": null}}
    
    Query: "list all active employees who were absent on 9th may"
    → {{"metric": "employee_list", "entities": {{}}, "filters": {{"status": "active", "attendance_status": "A"}}, "date_range": {{"start": "2026-05-09", "end": "2026-05-09"}}}}
    
    User Query: {query}
    
    Return ONLY the JSON object, nothing else.
    """
    
    try:
        response = call_llm(prompt)
        if not response:
            raise ValueError("Empty response from LLM")
        
        # Clean JSON
        response = response.strip()
        if response.startswith("```"):
            response = response.replace("```json", "").replace("```", "").strip()
        
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end != -1:
            response = response[start:end+1]
        
        data = json.loads(response)
        
        # Validate metric exists in config
        if data.get("metric") not in available_metrics:
            print(f"Invalid metric from LLM: {data.get('metric')}, falling back to entity extraction")
            return _fallback_parse(query)
        
        print(f"[Intent Parser] Parsed: metric={data['metric']}, entities={data.get('entities')}")
        return data
        
    except json.JSONDecodeError as e:
        print(f"[Intent Parser] JSON parse error: {e}, falling back")
        return _fallback_parse(query)
    except Exception as e:
        print(f"[Intent Parser] Error: {e}, falling back")
        return _fallback_parse(query)


def _fallback_parse(query: str):
    """
    Fallback: If LLM fails, use context-aware keyword extraction.
    Better than crashing, worse than working LLM.
    """
    print("[Intent Parser] Using fallback parsing")
    
    q = query.lower()
    
    # Detect metric from keywords
    metric = "employee_list"
    if "leave" in q:
        metric = "leave_balance"
    elif "attendance" in q:
        metric = "attendance"
    elif "job description" in q or "job title" in q or "designation" in q:
        metric = "job_description"
    elif "hierarchy" in q:
        metric = "employee_hierarchy"
    
    # Extract entity names intelligently based on context
    entities = {}
    filters = {}
    
    # CHECK MANAGER PHRASES FIRST (before generic name extraction)
    manager_phrases = [
        "team members of",
        "team members name of",
        "team members names of",
        "direct reports of",
        "reports to",
        "manager of",
        "who works under",
        "team of"
    ]
    if any(phrase in q for phrase in manager_phrases):
        manager_name = _extract_name_after_phrase(query, manager_phrases)
        if manager_name:
            entities["manager"] = manager_name
            print(f"[Fallback] Detected manager: {manager_name}")
        else:
            print("[Fallback] Manager phrase detected but name extraction failed")
    else:
        # For count-like queries without a clear name context, avoid accidental name extraction
        count_like = any(phrase in q for phrase in ["how many", "count"])
        explicit_name_context = any(token in q for token in [" of ", " for ", " named ", " called "])

        if not count_like or explicit_name_context:
            names = extract_employee_names(query)
            if names:
                entities["employees"] = names
                print(f"[Fallback] Detected employees: {names}")
        else:
            print("[Fallback] Count query detected, skipping generic employee extraction")
    
    # Extract filters
    if "active" in q and "inactive" not in q:
        filters["status"] = "active"
    if "inactive" in q:
        filters["status"] = "inactive"
        
    if "absent" in q:
        filters["attendance_status"] = "A"
    elif "present" in q:
        filters["attendance_status"] = "P"
        
    if "how many" in q or "count" in q:
        filters["result_mode"] = "count"
    if "all" in q:
        filters["should_skip_limit"] = True
    
    # Extract date range
    date_range = extract_date_range_local(query)
    
    return {
        "metric": metric,
        "entities": entities,
        "filters": filters,
        "date_range": date_range
    }


def _extract_name_after_phrase(query: str, phrases: list):
    """Extract a name that appears after one of the given phrases."""
    q = query.lower()
    
    for phrase in phrases:
        if phrase in q:
            # Find position after phrase
            pos = q.find(phrase) + len(phrase)
            remainder = query[pos:].strip()
            
            # Extract first 1-3 words as name
            words = remainder.split()[:3]
            name = " ".join(words).strip()
            
            # Remove trailing punctuation/noise
            name = re.sub(r'[?.,;]+$', '', name).strip()
            
            if name and len(name) > 2:
                return name
    
    return None


def normalize_intent_data(intent_data):
    """
    Ensure intent_data has all required fields with proper types.
    Called after parsing to validate structure.
    """
    return {
        "metric": intent_data.get("metric"),
        "entities": intent_data.get("entities") or {},
        "filters": intent_data.get("filters") or {},
        "date_range": intent_data.get("date_range")
    }
