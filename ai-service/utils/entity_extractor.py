from utils.llm_service import call_llm
import json
import re

MONTH_WORDS = (
    "january|february|march|april|may|june|july|august|september|october|november|december|"
    "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec"
)

def clean_name(name):
    noise_words = ["for", "employee", "report", "data"]

    parts = name.split()
    cleaned = [w for w in parts if w.lower() not in noise_words]

    return " ".join(cleaned)

def fallback_name_extraction(query):
    query = query.lower()

    direct_match = re.search(
        r"\b(?:named|name(?:\s+is)?|contain|contains|like)\s+([a-z]{3,}(?:\s+[a-z]{3,}){0,3})\b",
        query
    )
    if direct_match:
        return [direct_match.group(1).strip()]

    # Only match 2–4 word sequences (reduces noise)
    matches = re.findall(r"\b([a-z]{3,}(?:\s+[a-z]{3,}){1,3})\b", query)

    # Remove common noise phrases
    noise_phrases = ["last days", "attendance report", "leave balance"]

    filtered = []
    for m in matches:
        if not any(noise in m for noise in noise_phrases):
            filtered.append(m)

    return filtered

def fast_name_extraction(query):
    query = query.lower()

    patterns = [
        rf"\b(?:of|for)\s+([a-z]{{2,}}(?:\s+[a-z]{{2,}}){{0,3}}?)(?=\s+(?:in\s+(?:{MONTH_WORDS})\b|on\b|from\b|between\b|and\b|with\b|where\b|policy\b|rules\b|reporting\s+manager\b|manager\b|reports\s+to\b|report\s+to\b)|$)",
        r"\b(?:named|name(?:\s+is)?|contain|contains|like)\s+([a-z]{2,}(?:\s+[a-z]{2,}){0,3})\b",
        r"^([a-z]{2,}(?:\s+[a-z]{2,}){0,3}?)(?=\s+(?:leave|attendance|salary|report|reporting|manager|status|dob|date|email|phone|address|till|today|in|for|of|and|how|many)\b)",
    ]

    noise_words = {
        "leave", "balance", "attendance", "report", "policy", "rules",
        "active", "inactive", "employee", "employees", "details", "data", "status", "manager", "reporting",
        "how", "many", "count"
    }

    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if not match:
            continue

        candidate = re.sub(r"\s+", " ", match.group(1)).strip()
        words = [word for word in candidate.split() if word not in noise_words and not word.isdigit()]

        if 1 <= len(words) <= 4:
            return [" ".join(words)]

    return []

def clean_llm_json(response):
    if not response:
        raise ValueError("Empty response from LLM")

    # Remove markdown code blocks
    response = response.strip()

    if response.startswith("```"):
        response = response.replace("```json", "").replace("```", "").strip()

    # Extra safety (sometimes model adds text before JSON)
    start = response.find("{")
    end = response.rfind("}")

    if start != -1 and end != -1:
        response = response[start:end+1]

    return response

def extract_employee_names(query: str):
    fast_names = fast_name_extraction(query)
    if fast_names:
        print("Fast extracted names:", fast_names)
        return fast_names

    prompt = f"""
    Extract employee names from the query.

    STRICT RULES:
    - Return ONLY JSON
    - Format: {{ "names": ["name1", "name2"] }}
    - Names are usually 2 to 4 words
    - Ignore words like: show, get, report, attendance, leave, for, last, days
    - Extract only human names
    - DO NOT include extra words before or after the name
    - If no name found, return: {{ "names": [] }}
    - NEVER return null or None

    Query:
    {query}
    """

    response = call_llm(prompt)
    print("Name extraction Response:", response)

    # 🔥 Step 0: fallback if LLM fails
    if not response:
        print("LLM returned empty response, using fallback extraction.")
        return fallback_name_extraction(query)

    try:
        cleaned = clean_llm_json(response)
        print("Cleaned LLM JSON:", cleaned)
        data = json.loads(cleaned)
        names = data.get("names", [])

    except Exception as e:
        print("LLM parsing failed:", e)
        return fallback_name_extraction(query)

    # 🔥 Step 1: Clean LLM output
    cleaned_names = []
    print("Raw names from LLM:", names)
    for name in names:
        name = name.lower().strip()

        # Remove noise words
        name = re.sub(r'\b(for|employee|of|report|reporting|manager|attendance|details|data|last|days)\b', '', name)

        # Remove special chars
        name = re.sub(r'[^a-zA-Z\s]', '', name)

        # Normalize spaces
        name = re.sub(r'\s+', ' ', name).strip()

        # Keep only 1–4 word names so single-name lookups still work.
        words = name.split()
        if 1 <= len(words) <= 4:
            cleaned_names.append(name)
    print("Cleaned names after processing:", cleaned_names)
    # 🔥 Step 2: fallback if empty
    if not cleaned_names:
        cleaned_names = fallback_name_extraction(query)
    print("Names after fallback (if needed):", cleaned_names)
    # Remove duplicates
    cleaned_names = list(set(cleaned_names))

    print("Extracted Names:", cleaned_names)

    return cleaned_names

def extract_employee_names111(query: str):
    prompt = f"""
    Extract employee names from the query.

    STRICT RULES:
    - Return ONLY JSON
    - Format: {{ "names": ["name1", "name2"] }}
    - Names are usually 2 to 4 words (e.g., "mukesh kumar sharma")
    - Ignore words like: show, get, report, attendance, leave, for, last, days
    - Extract only human names
    - DO NOT include extra words before or after the name
    - If no name found, return: {{ "names": [] }}
    - NEVER return null or None

    Query:
    {query}
    """

    response = call_llm(prompt)
    print("Name extraction Response: ", response)
    # 🔥 Step 1: Clean raw LLM response

    if not response:
        return fallback_name_extraction(query)

    try:
        cleaned = clean_llm_json(response)
        data = json.loads(cleaned)
        names = data.get("names", [])

        names = [clean_name(n) for n in names]

        if not names:
            names = fallback_name_extraction(query)

        # return names
    except Exception as e:
        names = fallback_name_extraction(query)

    # 🔥 Step 2: Strong cleaning layer
    cleaned_names = []
    for name in names:
        name = name.lower().strip()

        # Remove unwanted words
        name = re.sub(r'\b(for|employee|of|report|attendance|details|data)\b', '', name)

        # Remove special chars
        name = re.sub(r'[^a-zA-Z\s]', '', name)

        # Normalize spaces
        name = re.sub(r'\s+', ' ', name).strip()

        # Heuristic: max 3 words
        words = name.split()
        if len(words) > 3:
            name = " ".join(words[:3])

        # Final validation (only alphabets + spaces)
        if re.match(r'^[a-zA-Z\s]+$', name) and len(name) > 2:
            cleaned_names.append(name)

    # Remove duplicates
    cleaned_names = list(set(cleaned_names))

    print("Extracted Names:", cleaned_names)

    return cleaned_names