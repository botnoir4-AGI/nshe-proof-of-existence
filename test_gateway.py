#!/usr/bin/env python3
import requests
import json

GATEWAY_URL = "http://localhost:8001/v1/chat/completions"

def test_gateway(url, model="qwen2.5:1.5b"):
    # Test format 1: dengan prompt field (OpenAI-compatible)
    payload1 = {
        "model": model,
        "prompt": "Say 'OK' if you receive this",
        "stream": False,
        "max_tokens": 50
    }
    
    # Test format 2: dengan messages field (standard)
    payload2 = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'OK' if you receive this"}],
        "stream": False,
        "max_tokens": 50
    }
    
    print("Testing format 1 (prompt field)...")
    try:
        r1 = requests.post(url, json=payload1, timeout=30)
        print(f"  Status: {r1.status_code}")
        print(f"  Response: {r1.text[:200]}")
    except Exception as e:
        print(f"  Exception: {e}")
    
    print("\nTesting format 2 (messages field)...")
    try:
        r2 = requests.post(url, json=payload2, timeout=30)
        print(f"  Status: {r2.status_code}")
        print(f"  Response: {r2.text[:200]}")
    except Exception as e:
        print(f"  Exception: {e}")

test_gateway(GATEWAY_URL)
