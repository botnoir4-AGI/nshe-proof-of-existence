#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH Execution Framework
Autonomous execution cycles: match tasks → execute skills → feedback → improve
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from skill_executor import SkillExecutor
from nshe_bridge import enhance_results
from enhanced_analyzer import EnhancedAnalyzer

REPO = Path(r"C:\UMBRA_CORE\umbra-sovereign")
CURRICULUM_FILE = REPO / "threat_intel" / "curriculum.json"


class ExecutionFramework:
    """Autonomous execution framework"""
    
    def __init__(self):
        self.executor = SkillExecutor()
        self.curriculum = self._load_curriculum()
    
    def _load_curriculum(self):
        if CURRICULUM_FILE.exists():
            try:
                return json.loads(CURRICULUM_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"proposed_tasks": [], "completed_tasks": []}
    
    def _save_curriculum(self):
        CURRICULUM_FILE.write_text(
            json.dumps(self.curriculum, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def match_task_to_skill(self, task: Dict) -> str:
        """Match task to best available skill"""
        task_type = task.get("type", "")
        available_skills = self.executor.list_skills()
        
        # Priority matching based on task type
        skill_mapping = {
            "learn_cve": ["cve_analyzer", "skill_cve_analyzer", "skill_vulnerability_parser"],
            "learn_ttp": ["skill_ttp_analyzer", "skill_attack_pattern"],
            "learn_vulnerability": ["cve_analyzer", "skill_vulnerability_parser", "skill_cve_analyzer"],
            "learn_detection": ["skill_detection_rule", "skill_log_analyzer"],
            "learn_threat_intel": ["skill_threat_analyzer", "skill_log_analyzer"],
            "learn_cloud_threat": ["skill_cloud_analyzer", "skill_log_analyzer"],
        }
        
        # Try specific mappings first
        for skill_name in skill_mapping.get(task_type, []):
            if skill_name in available_skills:
                return skill_name
        
        # Fallback: use first available skill
        if available_skills:
            return available_skills[0]
        
        return None
    
    def execute_task(self, task: Dict) -> Dict:
        """Execute task using matched skill"""
        skill_name = self.match_task_to_skill(task)
        if not skill_name:
            return {
                "success": False,
                "error": "No matching skill found",
                "task": task
            }
        
        # Prepare context from task
        context = {
            "task_type": task.get("type"),
            "description": task.get("description", ""),
            "ttp": task.get("ttp"),
            "cve_id": task.get("cve_id"),
            "source": task.get("source"),
            "test": False
        }
        
        # Execute skill
        result = self.executor.execute_skill(skill_name, context)
        result["task"] = task
        return result
    
    def execute_tasks(self, tasks: List[Dict], max_tasks=5) -> List[Dict]:
        """Execute provided tasks directly (no file loading)"""
        print(f"[EXECUTION] Starting execution cycle...")
        
        if not tasks:
            print("[EXECUTION] No tasks provided")
            return []
        
        # Select tasks with variety (rotate through available tasks)
        import random
        
        high_priority = [t for t in tasks if t.get("priority") == "high"]
        other_priority = [t for t in tasks if t.get("priority") != "high"]
        
        # Shuffle to ensure variety across cycles
        random.shuffle(high_priority)
        random.shuffle(other_priority)
        
        # Take high priority first, then fill remaining slots with others
        selected = high_priority[:max_tasks]
        remaining_slots = max_tasks - len(selected)
        if remaining_slots > 0:
            selected.extend(other_priority[:remaining_slots])
        
        tasks = selected[:max_tasks]
        
        print(f"[EXECUTION] Selected {len(tasks)} tasks")
        
        # Execute tasks
        results = []
        for i, task in enumerate(tasks):
            print(f"[EXECUTION] Executing [{i+1}/{len(tasks)}] {task.get('type')}: {task.get('description', '')[:60]}")
            result = self.execute_task(task)
            results.append(result)
            
            if result["success"]:
                print(f"  ✓ Success ({result['execution_time']:.2f}s)")
            else:
                print(f"  ✗ Failed: {result.get('error', 'Unknown')[:80]}")
        
        # Update curriculum (remove executed tasks, add to completed)
        executed_descs = {r["task"]["description"] for r in results if r["success"]}
        self.curriculum["proposed_tasks"] = [
            t for t in self.curriculum.get("proposed_tasks", [])
            if t["description"] not in executed_descs
        ]
        
        self.curriculum.setdefault("completed_tasks", []).extend([
            {
                "task_type": r["task"]["type"],
                "description": r["task"]["description"],
                "skill_used": r.get("skill"),
                "success": r["success"],
                "execution_time": r.get("execution_time", 0),
                "timestamp": datetime.now().isoformat()
            }
            for r in results
        ])
        
        self._save_curriculum()
        
        print(f"[EXECUTION] Cycle complete: {len([r for r in results if r['success']])}/{len(results)} successful")
        
        # Enhance results with NSHE cognitive metrics
        try:
            enhanced = enhance_results(results)
            
            # Log cognitive metrics
            cognitive = enhanced.get("cognitive_metrics", {})
            rci = cognitive.get("rci", 0)
            rim = cognitive.get("rim", 0)
            print(f"[NHSE] RCI: {rci:.4f} | RIM: {rim:.4f}")
            
            # Check for mutation trigger
            if enhanced.get("anomaly_detected"):
                print(f"[NHSE] Anomaly detected - mutation recommended")
            
            # Attach enhanced data to results
            for r in results:
                r["nshe_rci"] = rci
                r["nshe_rim"] = rim
        
        except Exception as e:
            print(f"[NHSE] Enhancement error: {e}")
        
        return results


if __name__ == "__main__":
    framework = ExecutionFramework()
    results = framework.run_execution_cycle(max_tasks=3)
    print(f"\nExecution results: {len(results)} tasks")
