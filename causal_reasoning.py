#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Causal Reasoning Layer
Graph-based causal inference with NSHE symbolic KB integration.
Provides "why" and "what next" reasoning for threat intelligence.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict

NSHE_BRIDGE_DIR = Path(r"C:\UMBRA_CORE\autarch")

# MITRE ATT&CK Kill Chain causal patterns
# Each stage "enables" subsequent stages
CAUSAL_PATTERNS = {
    "reconnaissance": {
        "enables": ["initial_access", "credential_access"],
        "indicators": ["port_scan", "directory_traversal", "reconnaissance"],
        "ttps": ["T1595", "T1592", "T1589"],
        "confidence": 0.7
    },
    "initial_access": {
        "enables": ["execution", "persistence"],
        "indicators": ["ssh_brute_force", "sql_injection", "xss_attempt", "http_auth_bypass"],
        "ttps": ["T1190", "T1078", "T1566"],
        "confidence": 0.8
    },
    "execution": {
        "enables": ["persistence", "privilege_escalation", "discovery"],
        "indicators": ["command_execution", "command_injection", "malware_download"],
        "ttps": ["T1059", "T1203", "T1106"],
        "confidence": 0.8
    },
    "persistence": {
        "enables": ["lateral_movement", "collection"],
        "indicators": ["persistence", "file_upload"],
        "ttps": ["T1547", "T1543", "T1546"],
        "confidence": 0.7
    },
    "privilege_escalation": {
        "enables": ["lateral_movement", "collection", "exfiltration"],
        "indicators": ["privilege_escalation"],
        "ttps": ["T1548", "T1068", "T1574"],
        "confidence": 0.7
    },
    "credential_access": {
        "enables": ["lateral_movement", "persistence"],
        "indicators": ["credential_harvesting", "ssh_brute_force"],
        "ttps": ["T1003", "T1110", "T1056"],
        "confidence": 0.8
    },
    "discovery": {
        "enables": ["lateral_movement", "collection"],
        "indicators": ["port_scan", "directory_traversal", "reconnaissance"],
        "ttps": ["T1046", "T1083", "T1082"],
        "confidence": 0.7
    },
    "lateral_movement": {
        "enables": ["collection", "exfiltration", "impact"],
        "indicators": ["lateral_movement"],
        "ttps": ["T1021", "T1570", "T1563"],
        "confidence": 0.7
    },
    "collection": {
        "enables": ["exfiltration"],
        "indicators": ["data_exfiltration", "credential_harvesting"],
        "ttps": ["T1005", "T1039", "T1056"],
        "confidence": 0.7
    },
    "exfiltration": {
        "enables": ["impact"],
        "indicators": ["data_exfiltration", "dns_tunneling"],
        "ttps": ["T1041", "T1048", "T1567"],
        "confidence": 0.8
    },
    "impact": {
        "enables": [],
        "indicators": [],
        "ttps": ["T1486", "T1490", "T1499"],
        "confidence": 0.9
    }
}


class CausalReasoningEngine:
    """
    Graph-based causal reasoning for threat intelligence.
    Integrates with NSHE symbolic KB for domain knowledge.
    """
    
    def __init__(self):
        self.causal_graph = defaultdict(list)  # node -> [(target, confidence)]
        self.reverse_graph = defaultdict(list)  # node -> [(source, confidence)]
        self.symbolic_kb = self._load_symbolic_kb()
        self._build_base_graph()
    
    def _load_symbolic_kb(self) -> Dict:
        """Load NSHE symbolic knowledge base"""
        try:
            import sys
            sys.path.insert(0, str(NSHE_BRIDGE_DIR))
            from nshe_bridge import SYMBOLIC_KNOWLEDGE_BASE
            return SYMBOLIC_KNOWLEDGE_BASE
        except Exception:
            return {}
    
    def _build_base_graph(self):
        """Build causal graph from kill chain patterns"""
        for stage, info in CAUSAL_PATTERNS.items():
            for enabled_stage in info["enables"]:
                confidence = info["confidence"]
                self.causal_graph[stage].append((enabled_stage, confidence))
                self.reverse_graph[enabled_stage].append((stage, confidence))
    
    def add_causal_edge(self, cause: str, effect: str, confidence: float = 0.5):
        """Add a causal relationship"""
        self.causal_graph[cause].append((effect, confidence))
        self.reverse_graph[effect].append((cause, confidence))
    
    def ttp_to_stage(self, ttp_id: str) -> Optional[str]:
        """Map TTP ID to kill chain stage"""
        for stage, info in CAUSAL_PATTERNS.items():
            if ttp_id in info["ttps"]:
                return stage
        return None
    
    def infer_effects(self, observed_ttp: str) -> List[Dict]:
        """Forward inference: what could happen because of this TTP"""
        stage = self.ttp_to_stage(observed_ttp)
        if not stage:
            return []
        
        effects = []
        visited = set()
        queue = [(stage, 1.0, [stage])]
        
        while queue:
            current, confidence, path = queue.pop(0)
            
            if current in visited:
                continue
            visited.add(current)
            
            for target, edge_confidence in self.causal_graph.get(current, []):
                new_confidence = confidence * edge_confidence
                new_path = path + [target]
                
                effects.append({
                    "effect": target,
                    "confidence": round(new_confidence, 3),
                    "causal_path": " → ".join(new_path),
                    "path_length": len(new_path)
                })
                
                if len(new_path) < 5:  # Limit depth
                    queue.append((target, new_confidence, new_path))
        
        effects.sort(key=lambda x: x["confidence"], reverse=True)
        return effects
    
    def infer_causes(self, observed_ttp: str) -> List[Dict]:
        """Backward inference: what could have caused this TTP"""
        stage = self.ttp_to_stage(observed_ttp)
        if not stage:
            return []
        
        causes = []
        visited = set()
        queue = [(stage, 1.0, [stage])]
        
        while queue:
            current, confidence, path = queue.pop(0)
            
            if current in visited:
                continue
            visited.add(current)
            
            for source, edge_confidence in self.reverse_graph.get(current, []):
                new_confidence = confidence * edge_confidence
                new_path = [source] + path
                
                causes.append({
                    "cause": source,
                    "confidence": round(new_confidence, 3),
                    "causal_path": " → ".join(new_path),
                    "path_length": len(new_path)
                })
                
                if len(new_path) < 5:
                    queue.append((source, new_confidence, new_path))
        
        causes.sort(key=lambda x: x["confidence"], reverse=True)
        return causes
    
    def predict_next_stages(self, observed_ttps: List[str]) -> List[Dict]:
        """Predict likely next attack stages based on observed TTPs"""
        predictions = defaultdict(float)
        
        for ttp in observed_ttps:
            effects = self.infer_effects(ttp)
            for effect in effects:
                predictions[effect["effect"]] += effect["confidence"]
        
        # Normalize
        total = sum(predictions.values()) or 1.0
        
        results = []
        for stage, score in sorted(predictions.items(), key=lambda x: x[1], reverse=True):
            results.append({
                "predicted_stage": stage,
                "probability": round(score / total, 3),
                "associated_ttps": CAUSAL_PATTERNS.get(stage, {}).get("ttps", []),
                "indicators": CAUSAL_PATTERNS.get(stage, {}).get("indicators", [])
            })
        
        return results
    
    def explain(self, ttp_id: str, source_ip: str = "") -> Dict:
        """Generate causal explanation for an observed TTP"""
        stage = self.ttp_to_stage(ttp_id)
        
        if not stage:
            return {
                "ttp": ttp_id,
                "explanation": f"TTP {ttp_id} not mapped to kill chain stage",
                "causes": [],
                "effects": []
            }
        
        causes = self.infer_causes(ttp_id)
        effects = self.infer_effects(ttp_id)
        predictions = self.predict_next_stages([ttp_id])
        
        # Query symbolic KB for additional context
        symbolic_context = self._query_symbolic_kb(ttp_id)
        
        explanation = f"Observed {CAUSAL_PATTERNS.get(stage, {}).get('ttps', [])} ({stage} stage)."
        if causes:
            explanation += f" Likely preceded by: {causes[0]['causal_path']}."
        if effects:
            explanation += f" May lead to: {effects[0]['causal_path']}."
        
        return {
            "ttp": ttp_id,
            "stage": stage,
            "explanation": explanation,
            "likely_causes": causes[:3],
            "likely_effects": effects[:3],
            "predicted_next": predictions[:3],
            "symbolic_context": symbolic_context,
            "source_ip": source_ip,
            "timestamp": datetime.now().isoformat()
        }
    
    def _query_symbolic_kb(self, query: str) -> List[Dict]:
        """Query NSHE symbolic knowledge base"""
        if not self.symbolic_kb:
            return []
        
        results = []
        query_lower = query.lower()
        
        for key, value in self.symbolic_kb.items():
            if any(word in query_lower for word in key.lower().split()):
                results.append({
                    "key": key,
                    "value": value,
                    "relevance": "matched"
                })
        
        return results[:3]


if __name__ == "__main__":
    engine = CausalReasoningEngine()
    
    # Test causal reasoning
    print("Testing causal reasoning...")
    
    # Forward inference
    effects = engine.infer_effects("T1110.001")  # SSH brute force
    print(f"\nEffects of T1110.001 (Brute Force):")
    for e in effects[:5]:
        print(f"  {e['effect']} (confidence: {e['confidence']}) via {e['causal_path']}")
    
    # Backward inference
    causes = engine.infer_causes("T1059")  # Command execution
    print(f"\nCauses of T1059 (Command Execution):")
    for c in causes[:5]:
        print(f"  {c['cause']} (confidence: {c['confidence']}) via {c['causal_path']}")
    
    # Prediction
    predictions = engine.predict_next_stages(["T1046", "T1110.001"])
    print(f"\nPredicted next stages after recon + brute force:")
    for p in predictions[:3]:
        print(f"  {p['predicted_stage']} (probability: {p['probability']})")
    
    # Explanation
    explanation = engine.explain("T1190", "45.33.1.1")
    print(f"\nExplanation: {explanation['explanation']}")
    
    print("\nCausal reasoning engine OK")
