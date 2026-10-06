#!/usr/bin/env python3
"""
LucidForge Trigger Module
Allows SYS5 to trigger self-mutation in SISF when system needs adaptation.

Trigger mechanisms (in order of preference):
1. HTTP POST to SISF /v1/mutate endpoint
2. File-based trigger (SISF monitors this file)
3. Anomaly counter boost (write to SISF state)
"""

import requests
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

SISF_URL = "http://localhost:8017"
API_KEY = "79346e24206bda0e9ccd04b76f38d98b7f785650df28b9c3"

# Load API key from config
api_key_file = Path(r"C:\UMBRA_CORE\SISF\umbra_apikey.json")
if api_key_file.exists():
    try:
        with open(api_key_file, "r") as f:
            config = json.load(f)
            API_KEY = config.get("key", API_KEY)
    except:
        pass

# Trigger file paths
SISF_TRIGGER_FILE = Path(r"C:\UMBRA_CORE\SISF\lucidforge_trigger.json")
MUTATION_LOG = Path(__file__).parent.parent / "threat_intel" / "mutation_log.json"


def log_mutation_event(trigger_reason: str, method: str, success: bool):
    """Log mutation event untuk audit trail"""
    try:
        log = []
        if MUTATION_LOG.exists():
            log = json.loads(MUTATION_LOG.read_text(encoding="utf-8"))
        
        log.append({
            "timestamp": datetime.now().isoformat(),
            "trigger_reason": trigger_reason,
            "method": method,
            "success": success
        })
        
        # Keep last 100 events
        log = log[-100:]
        MUTATION_LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[LUCIDFORGE] Log error: {e}")


def trigger_via_http(reason: str) -> bool:
    """Try to trigger LucidForge via HTTP endpoint"""
    try:
        payload = {
            "action": "mutate",
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "source": "autarch_sys5"
        }
        
        response = requests.post(
            f"{SISF_URL}/v1/mutate",
            headers={
                "Content-Type": "application/json",
                "X-Umbra-Key": API_KEY
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"[LUCIDFORGE] ✓ HTTP trigger accepted: {reason}")
            log_mutation_event(reason, "http", True)
            return True
        else:
            print(f"[LUCIDFORGE] ⚠ HTTP trigger failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("[LUCIDFORGE] ⚠ HTTP trigger timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("[LUCIDFORGE] ⚠ SISF not reachable")
        return False
    except Exception as e:
        print(f"[LUCIDFORGE] ⚠ HTTP error: {e}")
        return False


def trigger_via_file(reason: str) -> bool:
    """Trigger LucidForge via file-based mechanism"""
    try:
        trigger_data = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "priority": "high",
            "source": "autarch_sys5",
            "status": "pending"
        }
        
        SISF_TRIGGER_FILE.write_text(json.dumps(trigger_data, indent=2), encoding="utf-8")
        print(f"[LUCIDFORGE] ✓ File trigger created: {SISF_TRIGGER_FILE}")
        log_mutation_event(reason, "file", True)
        return True
        
    except Exception as e:
        print(f"[LUCIDFORGE] ⚠ File trigger error: {e}")
        return False


def trigger_lucidforge(reason: str) -> bool:
    """
    Main trigger function. Tries multiple methods.
    
    Args:
        reason: Why mutation is needed
        
    Returns:
        True if trigger successful, False otherwise
    """
    print(f"[LUCIDFORGE] Triggering autopoiesis: {reason}")
    
    # Method 1: HTTP endpoint
    if trigger_via_http(reason):
        return True
    
    # Method 2: File-based trigger
    if trigger_via_file(reason):
        return True
    
    # All methods failed
    print(f"[LUCIDFORGE] ✗ All trigger methods failed")
    log_mutation_event(reason, "all_failed", False)
    return False


def check_trigger_conditions(mus_history: list, error_rate: float, 
                            vector_db_growth: int, honeypot_events: int) -> Optional[str]:
    """
    Check if LucidForge should be triggered.
    
    Returns:
        Trigger reason if conditions met, None otherwise
    """
    # Condition 1: MUS declining 3+ cycles
    if len(mus_history) >= 3:
        recent_trends = [h.get("trend") for h in mus_history[-3:]]
        if all(t == "declining" for t in recent_trends):
            return "MUS declining for 3 consecutive cycles"
    
    # Condition 2: High error rate
    if error_rate > 0.3:
        return f"High error rate: {error_rate:.1%}"
    
    # Condition 3: Vector DB stagnation
    if len(mus_history) >= 5:
        recent_growth = [h.get("cycle_data", {}).get("vector_db_growth", 0) 
                        for h in mus_history[-5:]]
        if all(g == 0 for g in recent_growth):
            return "Vector DB stagnation (no growth 5+ cycles)"
    
    # Condition 4: Honeypot overload without learning
    if honeypot_events > 100 and vector_db_growth == 0:
        return f"Honeypot overload ({honeypot_events} events) without learning"
    
    return None


if __name__ == "__main__":
    # Test trigger
    print("Testing LucidForge trigger...")
    result = trigger_lucidforge("test_trigger_from_script")
    print(f"Result: {result}")
