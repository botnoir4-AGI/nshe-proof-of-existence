#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH System 3: Global Workspace (Control Layer)
Competitive broadcast mechanism for module prioritization (~150MB RAM)

Based on Global Workspace Theory (Baars/Dehaene):
- Modules compete for attention
- Winner gets broadcast to entire system
- Resource arbitration for 8GB constraint
"""

import json
import psutil
import time
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Dict

BROADCAST_LOG = Path(r"C:\UMBRA_CORE\autarch\broadcast_log.jsonl")
STATE_FILE = Path(r"C:\UMBRA_CORE\autarch\global_state.json")

class GlobalWorkspace:
    """System 3: Control Layer - Competitive broadcast"""
    
    def __init__(self):
        self.modules = {
            "threat_response": self.threat_score,
            "goal_progress": self.goal_staleness,
            "skill_gap": self.skill_gap_score,
            "resource_pressure": self.resource_pressure,
            "policy_review": self.policy_queue_score
        }
        self.last_broadcast = None
        self.load_state()
    
    def load_state(self):
        """Load persistent state"""
        if STATE_FILE.exists():
            with open(STATE_FILE, "r") as f:
                self.state = json.load(f)
        else:
            self.state = {
                "last_threat_time": None,
                "goal_staleness": 0,
                "skill_gaps": [],
                "policy_queue": []
            }
    
    def save_state(self):
        """Persist state"""
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def threat_score(self) -> float:
        """Score based on recent honeypot events"""
        honeypot_log = Path(r"C:\UMBRA_CORE\honeypot\blackvault.jsonl")
        if not honeypot_log.exists():
            return 0.0
        
        # Count events in last 5 minutes
        try:
            with open(honeypot_log, "r") as f:
                lines = f.readlines()[-100:]  # Last 100 events
            
            now = time.time()
            recent = 0
            for line in lines:
                try:
                    event = json.loads(line)
                    if "ts" in event:
                        # Simple heuristic: recent events = high score
                        recent += 1
                except:
                    pass
            
            return min(recent / 10.0, 1.0)  # Normalize to 0-1
        except:
            return 0.0
    
    def goal_staleness(self) -> float:
        """Score based on how stale current goals are"""
        return min(self.state.get("goal_staleness", 0) / 100.0, 1.0)
    
    def skill_gap_score(self) -> float:
        """Score based on unmet skill needs"""
        gaps = len(self.state.get("skill_gaps", []))
        return min(gaps / 10.0, 1.0)
    
    def resource_pressure(self) -> float:
        """Score based on RAM/CPU pressure"""
        ram = psutil.virtual_memory().percent / 100.0
        cpu = psutil.cpu_percent() / 100.0
        
        # High pressure = high score (needs attention)
        return max(ram, cpu)
    
    def policy_queue_score(self) -> float:
        """Score based on pending policy decisions"""
        queue_size = len(self.state.get("policy_queue", []))
        return min(queue_size / 5.0, 1.0)
    
    def compete(self) -> Tuple[str, float]:
        """Run competition among modules, return winner"""
        scores = {}
        for module_name, score_fn in self.modules.items():
            try:
                scores[module_name] = score_fn()
            except Exception as e:
                scores[module_name] = 0.0
        
        # Find winner
        winner = max(scores.items(), key=lambda x: x[1])
        return winner
    
    def broadcast(self, winner: str, score: float, context: Dict = None):
        """Broadcast winner to entire system"""
        broadcast = {
            "timestamp": datetime.now().isoformat(),
            "winner": winner,
            "score": score,
            "context": context or {},
            "ram_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent()
        }
        
        # Log broadcast
        with open(BROADCAST_LOG, "a") as f:
            f.write(json.dumps(broadcast) + "\n")
        
        self.last_broadcast = broadcast
        self.save_state()
        
        print(f"[BROADCAST] {winner} (score: {score:.3f})")
        return broadcast
    
    def cycle(self) -> Dict:
        """Run one competition cycle"""
        winner, score = self.compete()
        
        # Build context
        context = {
            "scores": {name: fn() for name, fn in self.modules.items()}
        }
        
        # Broadcast
        broadcast = self.broadcast(winner, score, context)
        
        return broadcast
    
    def get_resource_budget(self) -> Dict:
        """Calculate resource allocation based on current state"""
        ram_available = (100 - psutil.virtual_memory().percent)
        
        budget = {
            "system_1_ops": 200,  # Always-on
            "system_2_coord": 50,  # On-demand
            "system_3_control": 150,  # Every 60s
            "system_4_intel": 300 if ram_available > 30 else 0,  # Sleep if tight
            "system_5_policy": 100,  # Per decision
            "buffer": ram_available * 80  # MB
        }
        
        return budget

# CLI
if __name__ == "__main__":
    import sys
    
    gw = GlobalWorkspace()
    
    if len(sys.argv) < 2:
        print("Usage: python global_workspace.py [cycle|budget|state]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "cycle":
        result = gw.cycle()
        print(json.dumps(result, indent=2))
    
    elif cmd == "budget":
        budget = gw.get_resource_budget()
        print(json.dumps(budget, indent=2))
    
    elif cmd == "state":
        print(json.dumps(gw.state, indent=2))
