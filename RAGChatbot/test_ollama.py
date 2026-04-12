import ollama

try:
    # Simple test
    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": "Say hello"}]
    )
    print("Success! Response:", response["message"]["content"][:100] + "...")
except Exception as e:
    print("Error:", e)