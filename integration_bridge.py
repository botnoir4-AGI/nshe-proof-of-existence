#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
INTEGRATION BRIDGE: AUTARCH → SISF → QWEN
Connects three systems for closed-loop learning:
1. AUTARCH (execution) → SISF (learning)
2. SISF (context) → Qwen (prediction)
3. Qwen (prediction) → AUTARCH (execution)
"""

import json
import requests
import os
from datetime import datetime
from pathlib import Path

# Configuration
SISF_URL = "http://127.0.0.1:8017"
AUTARCH_DIR = Path(r"C:\UMBRA_CORE\umbra-sovereign\autarch")
SISF_DIR = Path(r"C:\UMBRA_CORE\sisf")

# Load API key
API_KEY = None
api_key_file = SISF_DIR / "umbra_apikey.json"
if api_key_file.exists():
    try:
        with open(api_key_file, "r") as f:
            api_data = json.load(f)
            API_KEY = api_data.get("api_key")
            print(f"[BRIDGE] API Key loaded: {API_KEY[:10]}...")
    except Exception as e:
        print(f"[BRIDGE] Error loading API key: {e}")

def get_headers():
    """Get headers with API key"""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-Umbra-Key"] = API_KEY
    return headers

def send_to_sisf(data, endpoint="/chat/completions"):
    """Send data to SISF for learning"""
    try:
        # Convert to OpenAI-compatible format
        payload = {
            "model": "umbra-nshe-v14",
            "messages": [
                {
                    "role": "user",
                    "content": json.dumps(data, indent=2)
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        response = requests.post(
            f"{SISF_URL}{endpoint}",
            headers=get_headers(),
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[BRIDGE] SISF response: {result.get('choices', [{}])[0].get('message', {}).get('content', '')[:100]}")
            return result
        else:
            print(f"[BRIDGE] SISF error: {response.status_code}")
            return None
    except Exception as e:
        print(f"[BRIDGE] Error sending to SISF: {e}")
        return None

def query_sisf(query, top_k=3):
    """Query SISF for relevant context"""
    try:
        payload = {
            "model": "umbra-nshe-v14",
            "messages": [
                {
                    "role": "user",
                    "content": f"Query: {query}\nTop-k: {top_k}"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        response = requests.post(
            f"{SISF_URL}/chat/completions",
            headers=get_headers(),
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            context = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            print(f"[BRIDGE] SISF context: {context[:100]}...")
            return context
        else:
            print(f"[BRIDGE] SISF query error: {response.status_code}")
            return ""
    except Exception as e:
        print(f"[BRIDGE] Error querying SISF: {e}")
        return ""

def send_autarch_execution(execution_result):
    """Send AUTARCH execution result to SISF for learning"""
    data = {
        "type": "autarch_execution",
        "timestamp": datetime.now().isoformat(),
        "task": execution_result.get("task", {}),
        "output": execution_result.get("output", ""),
        "success": execution_result.get("success", False),
        "insights": execution_result.get("insights", []),
        "metadata": {
            "executor": "autarch_daemon",
            "cycle": execution_result.get("cycle", 0),
            "duration": execution_result.get("duration", 0)
        }
    }
    
    print(f"[BRIDGE] Sending execution to SISF: {data['task'].get('type', 'unknown')}")
    return send_to_sisf(data)

def get_enriched_context(task_description):
    """Get enriched context from SISF for Qwen"""
    print(f"[BRIDGE] Querying SISF for context: {task_description[:50]}...")
    context = query_sisf(task_description, top_k=3)
    return context

def query_qwen_with_context(prompt, sisf_context=""):
    """Query Qwen via Ollama with SISF-enriched context"""
    try:
        # Enrich prompt with SISF context
        enriched_prompt = f"{sisf_context}\n\n{prompt}" if sisf_context else prompt
        
        # Call Ollama
        ollama_url = "http://localhost:11434/api/chat"
        payload = {
            "model": "qwen2.5:1.5b",
            "messages": [
                {"role": "user", "content": enriched_prompt}
            ],
            "stream": False
        }
        
        response = requests.post(ollama_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            qwen_response = result.get("message", {}).get("content", "")
            print(f"[BRIDGE] Qwen response: {qwen_response[:100]}...")
            return qwen_response
        else:
            print(f"[BRIDGE] Qwen error: {response.status_code}")
            return ""
    except Exception as e:
        print(f"[BRIDGE] Error querying Qwen: {e}")
        return ""

def full_loop_test():
    """Test full loop: AUTARCH → SISF → Qwen → AUTARCH"""
    print("\n" + "=" * 72)
    print("FULL LOOP TEST")
    print("=" * 72)
    
    # Simulate AUTARCH execution
    test_execution = {
        "task": {
            "type": "learn_cve",
            "description": "Deep analysis: CVE-2026-85880 - Windows ALPC RCE",
            "priority": "high"
        },
        "output": "CVE-2026-85880 is a critical RCE vulnerability in Windows ALPC...",
        "success": True,
        "insights": ["Critical severity", "Remote exploitation", "Windows platform"],
        "cycle": 1,
        "duration": 45.2
    }
    
    print("\n[1/3] Sending AUTARCH execution to SISF...")
    sisf_response = send_autarch_execution(test_execution)
    
    print("\n[2/3] Querying SISF for context...")
    sisf_context = get_enriched_context(test_execution["task"]["description"])
    
    print("\n[3/3] Querying Qwen with SISF context...")
    qwen_prompt = f"Analyze this CVE: {test_execution['task']['description']}"
    qwen_response = query_qwen_with_context(qwen_prompt, sisf_context)
    
    print("\n" + "=" * 72)
    print("FULL LOOP TEST COMPLETE")
    print("=" * 72)
    
    return {
        "sisf_response": sisf_response,
        "sisf_context": sisf_context,
        "qwen_response": qwen_response
    }

if __name__ == "__main__":
    # Run full loop test
    result = full_loop_test()
    
    print("\nResults:")
    print(json.dumps(result, indent=2, default=str)[:1000])
