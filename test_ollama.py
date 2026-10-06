#!/usr/bin/env python3
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
GATEWAY_URL = "http://localhost:8001/v1/chat/completions"

def test_ollama(url, model="qwen2.5:1.5b"):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'OK' if you receive this"}],
        "stream": False
    }
    
    try:
        r = requests.post(url, json=payload, timeout=30)
        if r.status_code == 200:
            data = r.json()
            response = data.get("message", {}).get("content", "")
            return f"SUCCESS: {response[:100]}"
        else:
            return f"ERROR: HTTP {r.status_code} - {r.text[:100]}"
    except Exception as e:
        return f"EXCEPTION: {str(e)}"

print("Testing Ollama (11434)...")
result1 = test_ollama(OLLAMA_URL)
print(result1)

print("\nTesting Gateway (8001)...")
result2 = test_ollama(GATEWAY_URL)
print(result2)
