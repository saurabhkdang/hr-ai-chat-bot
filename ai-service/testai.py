from openai import OpenAI
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Say hello in one line"}
        ],
        temperature=0
    )

    print("✅ API Key is working!")
    print("Response:", response.choices[0].message.content)

except Exception as e:
    print("❌ Error occurred!")
    print("Error:", str(e))