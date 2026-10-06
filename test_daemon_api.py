
import requests
import json

url = "http://localhost:8001/v1/chat/completions"
payload = {
    "prompt": "Hello, this is a test",
    "reset_context": False
}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
