import ollama

response = ollama.chat(
    model="llama3",
    messages=[
        {"role": "user", "content": "Explain TCP three‑way handshake in networking"}
    ]
)
print(response["message"]["content"])