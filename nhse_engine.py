import json
import time
from pathlib import Path

class NHSE:
    def __init__(self):
        self.state_file = Path(r"C:\UMBRA_CORE\umbra-sovereign\autarch\nhse_state.json")
        self.curriculum_file = Path(r"C:\UMBRA_CORE\threat_intel\curriculum.json")
        self.skills_dir = Path(r"C:\UMBRA_CORE\skills")
        self.state = self._load_state()

    def _load_state(self):
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"cycle_count": 0, "total_mutations": 0, "last_mutation_cycle": 0}

    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def run_cycle(self):
        self.state["cycle_count"] += 1
        skill_count = len(list(self.skills_dir.glob("*.py"))) if self.skills_dir.exists() else 0
        
        rci = 1.0 + (skill_count * 0.01)
        rim = min(1.0, (self.state["cycle_count"] % 10) * 0.1 + (skill_count * 0.05))
        
        print(f"[NHSE] RCI: {rci:.4f} | RIM: {rim:.4f}")
        
        if rim >= 0.8 and (self.state["cycle_count"] - self.state["last_mutation_cycle"]) >= 3:
            print("[NHSE] Anomaly detected - triggering mutation protocol")
            self._trigger_mutation()
            self.state["total_mutations"] += 1
            self.state["last_mutation_cycle"] = self.state["cycle_count"]
        else:
            print("[NHSE] Cycle complete - within normal parameters")
            
        self._save_state()

    def _trigger_mutation(self):
        if self.curriculum_file.exists():
            with open(self.curriculum_file, 'r', encoding='utf-8') as f:
                try:
                    curr = json.load(f)
                except:
                    curr = {"proposed_tasks": []}
        else:
            curr = {"proposed_tasks": []}
            
        mutation_task = {
            "task_id": f"MUTATE-{int(time.time())}",
            "type": "skill_mutation",
            "description": "Mutate and optimize existing skills based on recent execution data",
            "priority": 10
        }
        
        if not any(t.get("type") == "skill_mutation" for t in curr.get("proposed_tasks", [])):
            curr["proposed_tasks"].append(mutation_task)
            with open(self.curriculum_file, 'w', encoding='utf-8') as f:
                json.dump(curr, f, indent=2)
            print("[NHSE] Mutation task injected into curriculum")
