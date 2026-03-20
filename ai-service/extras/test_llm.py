import ollama

response = ollama.chat(
    model='phi',
    messages=[
        {"role": "user", "content": "Explain leave policy"}
    ]
)

print(response['message']['content'])