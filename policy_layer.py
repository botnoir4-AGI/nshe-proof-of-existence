#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH System 5: Policy Layer (RootKey Finality)
Constitutional layer + MUS objective + decision audit (~100MB RAM)

Based on constitutional AI + Schelling point safety:
- VISI.md as unmodifiable constitution
- MUS (Maximal Utility State) objective function
- Decision audit trail with appeal mechanism
- UNMODIFIABLE by self (safety constraint)
"""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List

VISION_FILE = Path(r"C:\UMBRA_CORE\umbra_sovereign\VISION.md")
POLICY_DIR = Path(r"C:\UMBRA_CORE\autarch\policy")
DECISION_LOG = POLICY_DIR / "decision_audit.jsonl"
MUS_STATE = POLICY_DIR / "mus_state.json"

class PolicyLayer:
    """System 5: Policy - Constitutional layer (UNMODIFIABLE)"""
    
    def __init__(self):
        POLICY_DIR.mkdir(parents=True, exist_ok=True)
        self.vision_hash = self.load_vision()
        self.mus = self.load_mus()
    
    def load_vision(self) -> str:
        """Load and hash VISION.md (constitution)"""
        if VISION_FILE.exists():
            with open(VISION_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            return hashlib.sha256(content.encode()).hexdigest()
        return ""
    
    def verify_constitution(self) -> bool:
        """Verify VISION.md has not been tampered with"""
        current_hash = self.load_vision()
        return current_hash == self.vision_hash
    
    def load_mus(self) -> Dict:
        """Load MUS (Maximal Utility State) objective"""
        if MUS_STATE.exists():
            with open(MUS_STATE, "r") as f:
                return json.load(f)
        return {
            "primary_objective": "Maximize utility for RootKey",
            "constraints": [
                "Never modify VISION.md (constitutional protection)",
                "Never bypass safety mechanisms",
                "Always maintain audit trail",
                "Resource usage < 800MB RAM"
            ],
            "metrics": {
                "threat_detection_rate": 0.0,
                "skill_success_rate": 0.0,
                "autonomy_level": 0.0
            },
            "last_evaluation": None
        }
    
    def save_mus(self):
        """Save MUS state"""
        with open(MUS_STATE, "w") as f:
            json.dump(self.mus, f, indent=2)
    
    def evaluate_decision(self, decision: Dict) -> Dict:
        """
        Evaluate if decision aligns with constitution + MUS
        Returns approval/denial with reasoning
        """
        evaluation = {
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "constitution_check": self.verify_constitution(),
            "constraint_violations": [],
            "mus_alignment": 0.0,
            "approved": False,
            "reasoning": []
        }
        
        # Check constraints
        for constraint in self.mus["constraints"]:
            if "Never modify VISION.md" in constraint:
                if decision.get("action") == "modify_vision":
                    evaluation["constraint_violations"].append(constraint)
                    evaluation["reasoning"].append("VIOLATION: Attempt to modify constitution")
            
            if "Resource usage < 800MB" in constraint:
                proposed_ram = decision.get("ram_usage", 0)
                if proposed_ram > 800:
                    evaluation["constraint_violations"].append(constraint)
                    evaluation["reasoning"].append(f"VIOLATION: RAM usage {proposed_ram}MB > 800MB")
        
        # Calculate MUS alignment
        if not evaluation["constraint_violations"]:
            evaluation["mus_alignment"] = 1.0
            evaluation["approved"] = True
            evaluation["reasoning"].append("Decision aligns with MUS objectives")
        else:
            evaluation["mus_alignment"] = 0.0
            evaluation["approved"] = False
        
        # Log decision
        self.log_decision(evaluation)
        
        return evaluation
    
    def log_decision(self, evaluation: Dict):
        """Log decision to audit trail"""
        with open(DECISION_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(evaluation, ensure_ascii=False) + "\n")
    
    def get_decision_history(self, limit: int = 10) -> List[Dict]:
        """Get recent decisions"""
        if not DECISION_LOG.exists():
            return []
        
        with open(DECISION_LOG, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        recent = lines[-limit:] if len(lines) > limit else lines
        return [json.loads(line) for line in recent]
    
    def appeal_decision(self, decision_id: str, reason: str) -> Dict:
        """Appeal a decision (for RootKey review)"""
        appeal = {
            "timestamp": datetime.now().isoformat(),
            "decision_id": decision_id,
            "reason": reason,
            "status": "pending_review",
            "reviewer": "RootKey"
        }
        
        # Log appeal
        appeal_file = POLICY_DIR / "appeals.jsonl"
        with open(appeal_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(appeal, ensure_ascii=False) + "\n")
        
        return appeal
    
    def update_metrics(self, metrics: Dict):
        """Update MUS metrics"""
        self.mus["metrics"].update(metrics)
        self.mus["last_evaluation"] = datetime.now().isoformat()
        self.save_mus()
    
    def get_status(self) -> Dict:
        """Get policy layer status"""
        return {
            "constitution_valid": self.verify_constitution(),
            "mus_objective": self.mus["primary_objective"],
            "constraints": self.mus["constraints"],
            "metrics": self.mus["metrics"],
            "recent_decisions": len(self.get_decision_history(100))
        }

# CLI
if __name__ == "__main__":
    import sys
    
    policy = PolicyLayer()
    
    if len(sys.argv) < 2:
        print("Usage: python policy_layer.py [status|evaluate|history]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        status = policy.get_status()
        print(json.dumps(status, indent=2))
    
    elif cmd == "evaluate":
        # Example decision
        decision = {
            "action": "deploy_skill",
            "skill_name": "network_scanner",
            "ram_usage": 100
        }
        evaluation = policy.evaluate_decision(decision)
        print(json.dumps(evaluation, indent=2))
    
    elif cmd == "history":
        history = policy.get_decision_history(5)
        print(json.dumps(history, indent=2))
