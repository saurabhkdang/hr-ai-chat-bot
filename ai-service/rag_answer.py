import requests
from config import OLLAMA_URL, MODEL_NAME
import ollama
from ai_client import ask_ai

def generate_answer(question, context):

    prompt = f"""
Use the context to give the short answer in one line to the question.

Context:
{context}

Question:
{question}
"""
    return ask_ai(prompt)
    
    """ res = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    })
    return res.json()["response"] """

    """ response = ollama.chat(
        model='phi',
        messages=[{"role": "user", "content": prompt}]
    )

    return response['message']['content'] """