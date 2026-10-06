
import requests
import json

# Test 1: OpenAI-compatible format
print("\nTest 1: OpenAI format")
try:
    r = requests.post("http://localhost:8001/v1/chat/completions", 
        json={
            "model": "dolphin-llama3",
            "messages": [{"role": "user", "content": "Say hi"}],
            "temperature": 0.7
        }, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Ollama format
print("\nTest 2: Ollama format")
try:
    r = requests.post("http://localhost:8001/api/generate",
        json={
            "model": "dolphin-llama3",
            "prompt": "Say hi"
        }, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Simple prompt format
print("\nTest 3: Simple prompt")
try:
    r = requests.post("http://localhost:8001/v1/chat/completions",
        json={"prompt": "Say hi"}, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
