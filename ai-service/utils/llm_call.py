import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:31b-cloud"
temperature = 0

def call(prompt, return_type="string"):

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            },
            timeout=30
        )

        response.raise_for_status()

        result = response.json()

        content = result.get("response", "").strip()

        # remove markdown wrappers if present
        content = content.replace("```json", "").replace("```", "").strip()

        # STRING RESPONSE
        if return_type == "string":
            return content

        # JSON RESPONSE
        elif return_type == "json":
            return json.loads(content)

        # LIST RESPONSE
        elif return_type == "list":
            parsed = json.loads(content)

            if isinstance(parsed, list):
                return parsed

            raise ValueError("Response is not a list")

        # DICT RESPONSE
        elif return_type == "dict":
            parsed = json.loads(content)

            if isinstance(parsed, dict):
                return parsed

            raise ValueError("Response is not a dictionary")

        else:
            raise ValueError(f"Unsupported return_type: {return_type}")

    except Exception as e:
        print("LLM ERROR:", str(e))
        return None