from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen2.5:3b",
    temperature=0,
)

response = llm.invoke(
    "Explain what a foreign key is in one sentence."
)

print(response.content)