#!/usr/bin/env python3
"""
Debug SISF response structure
"""
import requests
import json

SISF_URL = "http://localhost:8017"
API_KEY = "79346e24206bda0e9ccd04b76f38d98b7f785650df28b9c3"

print("=" * 72)
print("TESTING SISF /v1/generate ENDPOINT")
print("=" * 72)

# Test with simple query
test_query = "test honeypot SSH attack"

print(f"\nSending query: '{test_query}'")
print(f"To: {SISF_URL}/v1/generate")

payload = {
    "query": test_query,
    "top_k": 3
}

try:
    response = requests.post(
        f"{SISF_URL}/v1/generate",
        headers={
            "Content-Type": "application/json",
            "X-Umbra-Key": API_KEY
        },
        json=payload,
        timeout=30
    )
    
    print(f"\nHTTP Status: {response.status_code}")
    print(f"\nResponse text (first 2000 chars):")
    print("-" * 72)
    print(response.text[:2000])
    print("-" * 72)
    
    # Try to parse as JSON
    try:
        parsed = json.loads(response.text)
        print(f"\n✓ Valid JSON")
        print(f"Type: {type(parsed)}")
        print(f"Keys: {parsed.keys() if isinstance(parsed, dict) else 'N/A'}")
        
        # Print structure
        if isinstance(parsed, dict):
            print("\nJSON structure:")
            for key, value in parsed.items():
                if isinstance(value, str):
                    print(f"  {key}: {value[:100]}..." if len(value) > 100 else f"  {key}: {value}")
                else:
                    print(f"  {key}: {type(value).__name__} = {str(value)[:100]}")
    except json.JSONDecodeError as e:
        print(f"\n✗ JSON decode error: {e}")
        print(f"Error at position {e.pos}: {response.text[max(0,e.pos-20):e.pos+20]}")
        
except Exception as e:
    print(f"\n✗ Request failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 72)
