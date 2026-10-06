#!/usr/bin/env python3
"""
MUS (Maximal Utility State) Calculator
Teleological compass untuk AUTARCH - mengukur apakah setiap cycle
membawa sistem lebih dekat ke tujuan final: Maximal Utility untuk RootKey.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

MUS_HISTORY_FILE = Path(__file__).parent.parent / "threat_intel" / "mus_history.json"

class MUSCalculator:
    """Menghitung utility state setiap cycle"""
    
    def __init__(self):
        self.history = self._load_history()
        self.previous_mus = self.history[-1]["mus"] if self.history else 0
    
    def _load_history(self) -> list:
        """Load MUS history dari file"""
        if MUS_HISTORY_FILE.exists():
            try:
                return json.loads(MUS_HISTORY_FILE.read_text(encoding="utf-8"))
            except:
                pass
        return []
    
    def _save_history(self):
        """Save MUS history (keep last 100 entries)"""
        self.history = self.history[-100:]
        MUS_HISTORY_FILE.write_text(json.dumps(self.history, indent=2), encoding="utf-8")
    
    def calculate_cycle_mus(self, cycle_data: Dict) -> float:
        """
        Hitung utility untuk satu cycle.
        
        Args:
            cycle_data: Dict dengan metrics cycle
                - tasks_executed: int
                - tasks_failed: int
                - ips_blocked: int
                - skills_promoted: int
                - skills_rejected: int
                - honeypot_events: int
                - correlations_found: int
                - campaigns_detected: int
                - vector_db_growth: int
                - errors: int
                
        Returns:
            float: MUS score
        """
        utility = 0.0
        
        # Positive utility (actions that serve RootKey)
        utility += cycle_data.get("tasks_executed", 0) * 10
        utility += cycle_data.get("ips_blocked", 0) * 50      # Defensive actuation
        utility += cycle_data.get("skills_promoted", 0) * 100  # Autopoiesis
        utility += cycle_data.get("honeypot_events", 0) * 5    # Intelligence gathering
        utility += cycle_data.get("correlations_found", 0) * 20
        utility += cycle_data.get("campaigns_detected", 0) * 75
        utility += cycle_data.get("vector_db_growth", 0) * 15  # NSHE learning
        
        # Negative utility (failures)
        utility -= cycle_data.get("tasks_failed", 0) * 20
        utility -= cycle_data.get("skills_rejected", 0) * 30
        utility -= cycle_data.get("errors", 0) * 25
        
        return max(0, utility)  # MUS tidak boleh negatif
    
    def evaluate_cycle(self, cycle_data: Dict, cycle_number: int) -> Dict:
        """
        Evaluasi cycle dan simpan ke history.
        
        Returns:
            Dict dengan hasil evaluasi:
                - mus: float
                - delta: float (perubahan dari cycle sebelumnya)
                - trend: str ("improving", "stable", "declining")
                - alert: bool (True jika perlu intervensi)
        """
        mus = self.calculate_cycle_mus(cycle_data)
        delta = mus - self.previous_mus
        
        # Determine trend
        if delta > 10:
            trend = "improving"
        elif delta < -10:
            trend = "declining"
        else:
            trend = "stable"
        
        # Alert jika declining 3 cycles berturut-turut
        recent_trends = [h.get("trend") for h in self.history[-3:]]
        alert = len(recent_trends) == 3 and all(t == "declining" for t in recent_trends)
        
        # Save to history
        entry = {
            "cycle": cycle_number,
            "timestamp": datetime.now().isoformat(),
            "mus": mus,
            "delta": delta,
            "trend": trend,
            "cycle_data": cycle_data
        }
        self.history.append(entry)
        self._save_history()
        
        # Update previous
        self.previous_mus = mus
        
        return {
            "mus": mus,
            "delta": delta,
            "trend": trend,
            "alert": alert,
            "cycle_number": cycle_number
        }
    
    def get_mus_summary(self) -> str:
        """Generate summary untuk logging"""
        if not self.history:
            return "[MUS] No data yet"
        
        latest = self.history[-1]
        return f"[MUS] Score: {latest['mus']:.1f} | Delta: {latest['delta']:+.1f} | Trend: {latest['trend']}"


if __name__ == "__main__":
    # Test MUS calculator
    calc = MUSCalculator()
    
    test_data = {
        "tasks_executed": 3,
        "tasks_failed": 0,
        "ips_blocked": 2,
        "skills_promoted": 1,
        "skills_rejected": 0,
        "honeypot_events": 15,
        "correlations_found": 18,
        "campaigns_detected": 1,
        "vector_db_growth": 3,
        "errors": 0
    }
    
    result = calc.evaluate_cycle(test_data, cycle_number=1)
    print(f"MUS Score: {result['mus']}")
    print(f"Delta: {result['delta']}")
    print(f"Trend: {result['trend']}")
    print(f"Alert: {result['alert']}")
