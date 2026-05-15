import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:31b-cloud"

def call_llm(prompt, temperature=0):
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
        return result.get("response", "").strip()

    except Exception as e:
        print("LLM ERROR:", str(e))
        return None