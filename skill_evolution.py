#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH Skill Evolution Loop
Execute skill → Measure performance → Generate improvement task → Voyager v2 → Execute v2
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from skill_executor import SkillExecutor
from nshe_bridge import get_bridge

REPO = Path(r"C:\UMBRA_CORE\umbra-sovereign")
CURRICULUM_FILE = REPO / "threat_intel" / "curriculum.json"
EVOLUTION_LOG = Path(r"C:\UMBRA_CORE\autarch\skill_evolution_log.jsonl")


class SkillEvolutionEngine:
    """Feedback loop for exponential skill improvement"""
    
    def __init__(self):
        self.executor = SkillExecutor()
    
    # Skills to exclude from evolution evaluation (broken or deprecated)
    EXCLUDED_SKILLS = {"ssh_connect", "skill_system_health"}
    
    def evaluate_skill_performance(self, skill_name: str) -> Dict:
        """Evaluate skill performance based on metrics + NSHE cognitive metrics"""
        # Skip excluded skills
        if skill_name in self.EXCLUDED_SKILLS:
            return {"needs_improvement": False, "reason": "Excluded skill"}
        
        metrics = self.executor.get_skill_metrics(skill_name)
        
        # Get NSHE cognitive metrics for enhanced evaluation
        try:
            bridge = get_bridge()
            cognitive_metrics = bridge.get_cognitive_metrics()
            rci = cognitive_metrics.get("rci_current", 0.5)
            
            # If system-wide RCI is low, be more aggressive about improvement
            if rci < 0.5:
                metrics["rci_penalty"] = True
        except Exception:
            rci = 0.5
        
        if not metrics:
            return {"needs_improvement": False, "reason": "No metrics yet"}
        
        executions = metrics.get("executions", 0)
        successes = metrics.get("successes", 0)
        avg_time = metrics.get("avg_time", 0)
        
        # Success rate
        success_rate = successes / executions if executions > 0 else 0
        
        # Determine if improvement needed
        needs_improvement = False
        reasons = []
        
        if success_rate < 0.7:  # < 70% success
            needs_improvement = True
            reasons.append(f"Low success rate: {success_rate:.2f}")
        
        if avg_time > 5.0:  # > 5 seconds average
            needs_improvement = True
            reasons.append(f"Slow execution: {avg_time:.2f}s")
        
        return {
            "needs_improvement": needs_improvement,
            "reasons": reasons,
            "metrics": metrics
        }
    
    def generate_improvement_tasks(self) -> List[Dict]:
        """Generate improvement tasks for underperforming skills"""
        tasks = []
        
        for skill_name in self.executor.list_skills():
            evaluation = self.evaluate_skill_performance(skill_name)
            
            if evaluation["needs_improvement"]:
                # Generate improvement task
                task = {
                    "type": "skill_improvement",
                    "priority": "high",
                    "description": f"Improve {skill_name}: {', '.join(evaluation['reasons'])}",
                    "skill_name": skill_name,
                    "current_metrics": evaluation["metrics"],
                    "proposed_by": "skill_evolution_engine",
                    "timestamp": datetime.now().isoformat()
                }
                tasks.append(task)
                
                print(f"[EVOLUTION] Generated improvement task for {skill_name}")
        
        return tasks
    
    def run_evolution_cycle(self) -> int:
        """Run skill evolution cycle"""
        print("[EVOLUTION] Starting skill evolution cycle...")
        
        # Evaluate all skills
        improvement_tasks = self.generate_improvement_tasks()
        
        if not improvement_tasks:
            print("[EVOLUTION] All skills performing well, no improvements needed")
            return 0
        
        # Add to curriculum
        curriculum_file = CURRICULUM_FILE
        if curriculum_file.exists():
            try:
                curriculum = json.loads(curriculum_file.read_text(encoding="utf-8"))
            except Exception:
                curriculum = {"proposed_tasks": []}
            
            # Dedup
            existing_descs = {t.get("description") for t in curriculum.get("proposed_tasks", [])}
            new_tasks = [t for t in improvement_tasks if t["description"] not in existing_descs]
            
            curriculum.setdefault("proposed_tasks", []).extend(new_tasks)
            curriculum_file.write_text(
                json.dumps(curriculum, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            
            print(f"[EVOLUTION] Added {len(new_tasks)} improvement tasks to curriculum")
            
            # Log evolution
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "skills_evaluated": len(self.executor.list_skills()),
                "improvement_tasks_generated": len(new_tasks),
                "tasks": [t["skill_name"] for t in new_tasks]
            }
            
            with open(EVOLUTION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            return len(new_tasks)
        
        return 0


if __name__ == "__main__":
    engine = SkillEvolutionEngine()
    tasks_generated = engine.run_evolution_cycle()
    print(f"\nEvolution cycle complete: {tasks_generated} improvement tasks generated")
