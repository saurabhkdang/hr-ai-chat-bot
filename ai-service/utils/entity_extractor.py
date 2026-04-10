from utils.llm_service import call_llm
import json
import re

def extract_employee_names(query: str):
    prompt = f"""
    Extract employee names from the query.

    STRICT RULES:
    - Return ONLY JSON
    - Format: {{ "names": ["name1", "name2"] }}
    - ONLY include actual person names
    - DO NOT include words like "employee", "for", "report", etc.
    - DO NOT explain anything
    - If no name found, return: {{ "names": [] }}

    Query:
    {query}
    """

    response = call_llm(prompt)

    # 🔥 Step 1: Clean raw LLM response
    response = response.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(response)
        names = data.get("names", [])
    except Exception as e:
        print("Name extraction JSON parse error:", e)
        return []

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