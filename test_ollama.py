from ollama import chat

response = chat(
    model="qwen2.5:3b",
    messages=[
        {
            "role": "user",
            "content": "Explain what a foreign key is in one sentence."
        }
    ],
)

print(response.message.content)