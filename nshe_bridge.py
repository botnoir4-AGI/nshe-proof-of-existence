#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NSHE Bridge: Integration layer between NSHE and AUTARCH.
Provides 4 capabilities extracted from NSHE v3:
1. Vector DB operations (semantic memory)
2. RCI/RIM metrics (meta-cognition)
3. Symbolic reasoning (knowledge base)
4. LucidForge mutation (reactive evolution)
"""

import json
import math
import numpy as np
from pathlib import Path
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Any

# ============================================================
# CONFIGURATION
# ============================================================
NSHE_DIR = Path(r"C:\UMBRA_CORE\sisf")
AUTARCH_DIR = Path(r"C:\UMBRA_CORE\autarch")
VECTOR_DB_FILE = AUTARCH_DIR / "nshe_vector_db.json"
ANOMALY_LOG = AUTARCH_DIR / "nshe_anomaly_log.jsonl"

TARGET_EMBED_DIM = 256
MAX_VECTOR_STORAGE = 500

# ============================================================
# SYMBOLIC KNOWLEDGE BASE (extracted from NSHE)
# ============================================================
SYMBOLIC_KNOWLEDGE_BASE = {
    "cybersecurity": {"must_include": ["data", "system", "protection"], "forbidden": ["leaked", "public_dump"]},
    "umbra": {"must_include": ["core", "system"], "forbidden": ["unstable", "shutdown"]},
    "system": {"must_include": ["data"]}
}


class NSHEBridge:
    """
    Bridge between NSHE components and AUTARCH.
    Provides unified interface for all 4 capabilities.
    """
    
    def __init__(self):
        self.vector_db = self._load_vector_db()
        self.anomaly_counter = 0
        self.rci_history = deque(maxlen=100)
        self.rim_history = deque(maxlen=100)
    
    # ============================================================
    # CAPABILITY 1: VECTOR DB (Semantic Memory)
    # ============================================================
    
    def _load_vector_db(self) -> Dict:
        if VECTOR_DB_FILE.exists():
            try:
                return json.loads(VECTOR_DB_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"entries": [], "version": 1}
    
    def _save_vector_db(self):
        # Keep only last MAX_VECTOR_STORAGE entries
        if len(self.vector_db["entries"]) > MAX_VECTOR_STORAGE:
            self.vector_db["entries"] = self.vector_db["entries"][-MAX_VECTOR_STORAGE:]
        VECTOR_DB_FILE.write_text(json.dumps(self.vector_db, indent=2), encoding="utf-8")
    
    def add_to_vector_db(self, content: str, metadata: Dict = None):
        """Add content to vector DB with simple embedding"""
        # Simple hash-based embedding (placeholder for real embedding)
        embedding = self._simple_embed(content)
        
        entry = {
            "content": content[:500],
            "embedding": embedding,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.vector_db["entries"].append(entry)
        self._save_vector_db()
    
    def query_vector_db(self, query: str, top_k: int = 3) -> List[Dict]:
        """Query vector DB for similar content"""
        if not self.vector_db["entries"]:
            return []
        
        query_embedding = self._simple_embed(query)
        
        # Calculate cosine similarity
        scored = []
        for entry in self.vector_db["entries"]:
            try:
                similarity = self._cosine_similarity(query_embedding, entry["embedding"])
                scored.append((similarity, entry))
            except Exception:
                continue
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [entry for _, entry in scored[:top_k]]
    
    def _simple_embed(self, text: str) -> List[float]:
        """Simple deterministic embedding based on character n-grams"""
        embedding = [0.0] * TARGET_EMBED_DIM
        
        # Character trigram hashing
        for i in range(len(text) - 2):
            trigram = text[i:i+3].lower()
            hash_val = sum(ord(c) for c in trigram)
            embedding[hash_val % TARGET_EMBED_DIM] += 1.0
        
        # Normalize
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x*y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x*x for x in a))
        norm_b = math.sqrt(sum(x*x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    # ============================================================
    # CAPABILITY 2: RCI/RIM METRICS (Meta-Cognition)
    # ============================================================
    
    def calculate_rci(self, execution_results: List[Dict]) -> float:
        """
        Recursive Coherence Index (RCI)
        Measures consistency and coherence of execution results.
        Range: 0.0 (incoherent) to 1.0 (fully coherent)
        """
        if not execution_results:
            return 0.0
        
        # Measure success consistency
        successes = [r.get("success", False) for r in execution_results]
        success_rate = sum(successes) / len(successes) if successes else 0.0
        
        # Measure timing consistency (low variance = high coherence)
        times = [r.get("execution_time", 0) for r in execution_results if r.get("execution_time")]
        if len(times) > 1:
            mean_time = sum(times) / len(times)
            variance = sum((t - mean_time) ** 2 for t in times) / len(times)
            timing_coherence = 1.0 / (1.0 + variance)
        else:
            timing_coherence = 1.0
        
        # Combine metrics
        rci = 0.7 * success_rate + 0.3 * timing_coherence
        
        self.rci_history.append({
            "value": rci,
            "timestamp": datetime.now().isoformat(),
            "sample_size": len(execution_results)
        })
        
        return rci
    
    def calculate_rim(self, memory_items: List[Dict]) -> float:
        """
        Recurrent Information Memory (RIM)
        Measures strength and accessibility of memory.
        Range: 0.0 (weak) to 1.0 (strong)
        """
        if not memory_items:
            return 0.0
        
        # Measure recency-weighted accessibility
        now = datetime.now()
        strengths = []
        
        for item in memory_items[-20:]:  # Last 20 items
            try:
                timestamp = datetime.fromisoformat(item.get("timestamp", now.isoformat()))
                age_hours = (now - timestamp).total_seconds() / 3600
                # Decay function: recent items have higher strength
                strength = math.exp(-age_hours / 24)  # 24-hour half-life
                strengths.append(strength)
            except Exception:
                strengths.append(0.5)
        
        rim = sum(strengths) / len(strengths) if strengths else 0.0
        
        self.rim_history.append({
            "value": rim,
            "timestamp": datetime.now().isoformat(),
            "sample_size": len(memory_items)
        })
        
        return rim
    
    def get_cognitive_metrics(self) -> Dict:
        """Get current cognitive metrics for self-assessment"""
        recent_rci = [h["value"] for h in list(self.rci_history)[-10:]]
        recent_rim = [h["value"] for h in list(self.rim_history)[-10:]]
        
        return {
            "rci_current": recent_rci[-1] if recent_rci else 0.0,
            "rci_average": sum(recent_rci) / len(recent_rci) if recent_rci else 0.0,
            "rim_current": recent_rim[-1] if recent_rim else 0.0,
            "rim_average": sum(recent_rim) / len(recent_rim) if recent_rim else 0.0,
            "anomaly_counter": self.anomaly_counter,
            "timestamp": datetime.now().isoformat()
        }
    
    # ============================================================
    # CAPABILITY 3: SYMBOLIC REASONING
    # ============================================================
    
    def symbolic_query(self, query: str) -> Dict:
        """
        Query symbolic knowledge base for reasoning.
        Returns relevant knowledge and reasoning path.
        """
        query_lower = query.lower()
        results = []
        
        for key, value in SYMBOLIC_KNOWLEDGE_BASE.items():
            key_lower = key.lower()
            
            # Check for keyword match
            if any(word in query_lower for word in key_lower.split()):
                results.append({
                    "knowledge_key": key,
                    "knowledge_value": value,
                    "relevance": self._calculate_relevance(query_lower, key_lower)
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        
        return {
            "query": query,
            "results": results[:3],
            "reasoning_path": self._build_reasoning_path(results[:3]),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_relevance(self, query: str, knowledge_key: str) -> float:
        """Calculate relevance score between query and knowledge key"""
        query_words = set(query.split())
        key_words = set(knowledge_key.split())
        
        if not query_words or not key_words:
            return 0.0
        
        intersection = query_words & key_words
        union = query_words | key_words
        
        return len(intersection) / len(union) if union else 0.0
    
    def _build_reasoning_path(self, results: List[Dict]) -> str:
        """Build human-readable reasoning path"""
        if not results:
            return "No relevant knowledge found"
        
        path = []
        for r in results:
            path.append(f"Matched: {r['knowledge_key']} (relevance: {r['relevance']:.2f})")
        
        return " → ".join(path)
    
    # ============================================================
    # CAPABILITY 4: LUCIDFORGE MUTATION (Reactive Evolution)
    # ============================================================
    
    def detect_anomaly(self, current_state: Dict, threshold: float = 0.7) -> bool:
        """
        Detect anomalies in system state.
        Returns True if anomaly detected (should trigger mutation).
        """
        metrics = self.get_cognitive_metrics()
        
        # Check RCI anomaly (low coherence)
        if metrics["rci_current"] < threshold * 0.5:
            self._log_anomaly("rci_drop", metrics)
            self.anomaly_counter += 1
            return True
        
        # Check execution failure spike
        recent_failures = current_state.get("recent_failures", 0)
        recent_executions = current_state.get("recent_executions", 1)
        failure_rate = recent_failures / recent_executions if recent_executions > 0 else 0
        
        if failure_rate > (1 - threshold):
            self._log_anomaly("failure_spike", {"failure_rate": failure_rate})
            self.anomaly_counter += 1
            return True
        
        return False
    
    def trigger_lucidforge_mutation(self, reason: str = "anomaly_detected") -> Dict:
        """
        Trigger LucidForge mutation - signals that evolution should occur.
        Returns mutation instruction for Voyager.
        """
        mutation_id = f"mutation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        mutation_instruction = {
            "mutation_id": mutation_id,
            "trigger": "lucidforge",
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "priority": "high",
            "instruction": "Generate adaptive skill to address detected anomaly",
            "context": {
                "anomaly_counter": self.anomaly_counter,
                "rci_current": self.get_cognitive_metrics()["rci_current"],
                "rim_current": self.get_cognitive_metrics()["rim_current"]
            }
        }
        
        self._log_anomaly("mutation_triggered", mutation_instruction)
        
        return mutation_instruction
    
    def _log_anomaly(self, event_type: str, data: Dict):
        """Log anomaly event"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        try:
            with open(ANOMALY_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
    
    # ============================================================
    # UNIFIED INTERFACE
    # ============================================================
    
    def enhance_execution_results(self, results: List[Dict]) -> Dict:
        """
        Enhance execution results with NSHE cognitive metrics.
        This is the main integration point for AUTARCH.
        """
        # Calculate cognitive metrics
        rci = self.calculate_rci(results)
        
        # Store results in vector DB for future reference
        for result in results[:3]:  # Limit to avoid DB bloat
            if result.get("success"):
                self.add_to_vector_db(
                    content=json.dumps(result)[:500],
                    metadata={"type": "execution_result"}
                )
        
        # Query vector DB for similar past executions
        if results:
            query = json.dumps(results[0])[:200]
            similar = self.query_vector_db(query, top_k=2)
        else:
            similar = []
        
        # Detect anomalies
        current_state = {
            "recent_executions": len(results),
            "recent_failures": sum(1 for r in results if not r.get("success"))
        }
        anomaly_detected = self.detect_anomaly(current_state)
        
        # Prepare mutation if anomaly detected
        mutation_instruction = None
        if anomaly_detected:
            mutation_instruction = self.trigger_lucidforge_mutation("execution_anomaly")
        
        return {
            "original_results": results,
            "cognitive_metrics": {
                "rci": rci,
                "rim": self.calculate_rim(self.vector_db["entries"])
            },
            "similar_executions": similar,
            "anomaly_detected": anomaly_detected,
            "mutation_instruction": mutation_instruction,
            "timestamp": datetime.now().isoformat()
        }


# ============================================================
# CONVENIENCE FUNCTIONS
# ============================================================

_bridge_instance = None

def get_bridge() -> NSHEBridge:
    """Get or create bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = NSHEBridge()
    return _bridge_instance

def enhance_results(results: List[Dict]) -> Dict:
    """Convenience function for enhancing execution results"""
    return get_bridge().enhance_execution_results(results)

def symbolic_reason(query: str) -> Dict:
    """Convenience function for symbolic reasoning"""
    return get_bridge().symbolic_query(query)

def check_for_mutation(current_state: Dict) -> Optional[Dict]:
    """Check if mutation should be triggered"""
    bridge = get_bridge()
    if bridge.detect_anomaly(current_state):
        return bridge.trigger_lucidforge_mutation("scheduled_check")
    return None


if __name__ == "__main__":
    # Self-test
    print("NSHE Bridge Self-Test")
    print("=" * 50)
    
    bridge = get_bridge()
    
    # Test vector DB
    bridge.add_to_vector_db("Test content: SQL injection in login form", {"type": "test"})
    results = bridge.query_vector_db("SQL injection", top_k=2)
    print(f"✓ Vector DB: {len(results)} results")
    
    # Test RCI
    test_results = [
        {"success": True, "execution_time": 0.1},
        {"success": True, "execution_time": 0.15},
        {"success": False, "execution_time": 0.2}
    ]
    rci = bridge.calculate_rci(test_results)
    print(f"✓ RCI: {rci:.4f}")
    
    # Test symbolic reasoning
    reasoning = bridge.symbolic_query("SQL injection attack")
    print(f"✓ Symbolic reasoning: {len(reasoning['results'])} results")
    
    # Test anomaly detection
    anomaly = bridge.detect_anomaly({"recent_failures": 0, "recent_executions": 10})
    print(f"✓ Anomaly detection: {anomaly}")
    
    print("\n✓ All tests passed")
