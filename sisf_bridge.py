#!/usr/bin/env python3
"""
SISF Integration Bridge
Connects AUTARCH execution layer to SISF/NSHE cognitive layer.

Flow:
1. AUTARCH executes task
2. Transform execution data to learnable text
3. Send to SISF /v1/feed (updates vector DB)
4. Before next execution, query SISF /v1/generate for context
5. Use NSHE-enriched context for better execution
6. Closed feedback loop → emergent behavior
"""

import requests
import json
from datetime import datetime
import time
from pathlib import Path
from typing import Dict


def _parse_robust_json(text: str) -> dict:
    """Parse JSON robustly - handles extra data, markdown, etc."""
    if not text:
        return {}
    
    text = text.strip()
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract first JSON object
    try:
        decoder = json.JSONDecoder()
        obj, idx = decoder.raw_decode(text)
        return obj
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in code block
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass
    
    # Try to find any JSON object
    start = text.find('{')
    if start >= 0:
        # Find matching closing brace
        brace_count = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except:
                        break
    
    return {}




SISF_URL = "http://localhost:8017"

# Load API key from config
API_KEY = "79346e24206bda0e9ccd04b76f38d98b7f785650df28b9c3"
api_key_file = Path(r"C:\UMBRA_CORE\SISF\umbra_apikey.json")
if api_key_file.exists():
    try:
        with open(api_key_file, "r") as f:
            config = json.load(f)
            API_KEY = config.get("key", API_KEY)
    except:
        pass


def send_to_sisf(execution_data: Dict) -> bool:
    """
    Send execution results to SISF for learning.
    Transforms execution data to text format that SISF /v1/feed expects.
    
    Args:
        execution_data: Dict with task, result, metadata
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Transform execution data to learnable text
        text_parts = []
        
        # Extract task description
        task = execution_data.get("task", {})
        if task:
            task_type = task.get("type", "unknown")
            task_desc = task.get("description", "")
            text_parts.append(f"Task: {task_type} - {task_desc}")
        
        # Extract results
        results = execution_data.get("results", [])
        for result in results:
            task_data = result.get("task", {})
            result_data = result.get("result", {})
            
            # Add task info
            task_type = task_data.get("type", "unknown")
            task_desc = task_data.get("description", "")
            text_parts.append(f"Executed: {task_type}")
            text_parts.append(f"Description: {task_desc}")
            
            # Add output summary (first 500 chars)
            output = result_data.get("output", "")
            if output:
                output_summary = output[:500]
                text_parts.append(f"Output: {output_summary}")
            
            # Add success status
            success = result_data.get("success", False)
            text_parts.append(f"Success: {success}")
        
        # Combine into single text feed
        text_feed = "\n".join(text_parts)
        
        if not text_feed:
            print("[SISF] ⚠ Empty text feed, skipping")
            return False
        
        # Send in SISF-expected format (just {"text": "..."})
        payload = {
            "text": text_feed
        }
        
        response = requests.post(
            f"{SISF_URL}/v1/feed",
            headers={
                "Content-Type": "application/json",
                "X-Umbra-Key": API_KEY
            },
            json=payload,
            timeout=30  # Increased for heavy vector DB operations
        )
        
        if response.status_code == 200:
            result = _parse_robust_json(response.text)
            vector_db_len = result.get("vector_db_len", 0) if isinstance(result, dict) else 0
            print(f"[SISF] ✓ Fed {len(text_feed)} chars (vector DB: {vector_db_len} clusters)")
            return True
        else:
            print(f"[SISF] ✗ Feed failed: HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("[SISF] ⚠ SISF not running (localhost:8017)")
        return False
    except Exception as e:
        print(f"[SISF] ✗ Feed error: {e}")
        return False


def get_nshe_context(query: str, top_k: int = 3) -> str:
    """
    Query SISF for relevant context from NSHE vector DB.
    
    BYPASSED: Qwen coder (qwen2.5:1.5b) generates garbage context.
    Learning feed still active, context injection disabled until Qwen upgraded.
    """
    # BYPASS: Qwen coder generates garbage, skip context injection
    # SISF still learns via send_to_sisf (vector DB grows)
    # Re-enable when Qwen upgraded to 7B+ or prompt improved
    return ""


def check_sisf_health() -> bool:
    """
    Check if SISF is running and responsive.
    
    Returns:
        True if SISF is healthy, False otherwise
    """
    try:
        response = requests.post(
            f"{SISF_URL}/v1/feed",
            headers={
                "Content-Type": "application/json",
                "X-Umbra-Key": API_KEY
            },
            json={"text": ""},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False




# ============================================================
# NSHE CONTEXT CACHE (Efferent Pathway)
# ============================================================
CACHE_FILE = Path(__file__).parent.parent / "threat_intel" / "nshe_context_cache.json"
CACHE_TTL = 3600  # 1 hour

def _load_context_cache() -> Dict:
    """Load context cache dari file"""
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {}

def _save_context_cache(cache: Dict):
    """Save context cache ke file (keep last 50 entries)"""
    # Remove expired entries
    now = time.time()
    cache = {k: v for k, v in cache.items() if now - v.get("timestamp", 0) < CACHE_TTL}
    
    # Keep only last 50
    if len(cache) > 50:
        sorted_items = sorted(cache.items(), key=lambda x: x[1].get("timestamp", 0))
        cache = dict(sorted_items[-50:])
    
    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding="utf-8")

def get_nshe_context_cached(query: str, top_k: int = 3) -> str:
    """
    Get NSHE context dengan cache fallback.
    Jika SISF timeout, pakai cache terakhir.
    """
    # Normalize query untuk cache key
    cache_key = f"{query[:100]}|{top_k}"
    
    # Try fresh query first
    fresh_context = get_nshe_context(query, top_k)
    if fresh_context:
        # Update cache
        cache = _load_context_cache()
        cache[cache_key] = {
            "context": fresh_context,
            "timestamp": time.time(),
            "query": query[:100]
        }
        _save_context_cache(cache)
        return fresh_context
    
    # Fallback to cache if fresh query failed
    cache = _load_context_cache()
    if cache_key in cache:
        cached_context = cache[cache_key].get("context", "")
        if cached_context:
            print(f"[SISF] ⚠ Using cached context ({len(cached_context)} chars)")
            return cached_context
    
    # No fresh, no cache - return empty
    return ""



if __name__ == "__main__":
    print("Testing SISF Bridge...")
    print(f"SISF URL: {SISF_URL}")
    print(f"API Key: {API_KEY[:10]}...")
    
    # Check health
    if check_sisf_health():
        print("✓ SISF is running")
    else:
        print("✗ SISF not reachable")
        exit(1)
    
    # Test feed with realistic data
    test_data = {
        "task": {
            "type": "learn_cve",
            "description": "CVE-2026-81963 - Windows Update Stack vulnerability"
        },
        "results": [
            {
                "task": {
                    "type": "learn_cve",
                    "description": "CVE-2026-81963 - Windows Update Stack vulnerability"
                },
                "result": {
                    "success": True,
                    "output": "CVE-2026-81963 is a critical elevation of privilege vulnerability in Windows Update Stack..."
                }
            }
        ],
        "cycle": 1,
        "timestamp": datetime.now().isoformat()
    }
    
    print("\nTesting /v1/feed...")
    success = send_to_sisf(test_data)
    if success:
        print("✓ Feed successful")
    
    # Test query
    print("\nTesting /v1/generate...")
    context = get_nshe_context("CVE vulnerability analysis")
    if context:
        print(f"✓ Context retrieved ({len(context)} chars)")
    
    print("\n✓ Bridge test complete")
