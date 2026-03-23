from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_ai(prompt, system="You are a helpful AI assistant."):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content.strip()

    # 🔥 CLEAN RESPONSE
    content = content.replace("```sql", "").replace("```", "").strip()

    if content.lower().startswith("sql"):
        content = content[3:].strip()

    return content