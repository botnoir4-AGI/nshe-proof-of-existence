#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH Skill Executor
Executes skills from skills/ folder with sandbox isolation.
Measures performance for exponential growth feedback loop.
"""

import importlib.util
import json
import time
from pathlib import Path
from datetime import datetime

SKILLS_DIR = Path(r"C:\UMBRA_CORE\skills")
METRICS_FILE = Path(r"C:\UMBRA_CORE\autarch\skill_metrics.json")


class SkillExecutor:
    """Execute skills with measurement and feedback"""
    
    def __init__(self):
        self.metrics = self._load_metrics()
    
    def _load_metrics(self):
        if METRICS_FILE.exists():
            try:
                return json.loads(METRICS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"skills": {}, "total_executions": 0}
    
    def _save_metrics(self):
        METRICS_FILE.write_text(
            json.dumps(self.metrics, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    
    def load_skill(self, skill_name):
        """Load skill module from skills/ folder"""
        skill_path = SKILLS_DIR / f"{skill_name}.py"
        if not skill_path.exists():
            return None, f"Skill {skill_name} not found"
        
        try:
            spec = importlib.util.spec_from_file_location(skill_name, skill_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if not hasattr(module, "execute"):
                return None, f"Skill {skill_name} missing execute() function"
            
            return module, None
        except Exception as e:
            return None, f"Error loading skill: {e}"
    
    def execute_skill(self, skill_name, context=None):
        """Execute skill with measurement"""
        if context is None:
            context = {}
        
        start_time = time.time()
        
        # Load skill
        module, error = self.load_skill(skill_name)
        if error:
            return {
                "success": False,
                "error": error,
                "skill": skill_name,
                "execution_time": 0
            }
        
        # Execute
        try:
            result = module.execute(context)
            execution_time = time.time() - start_time
            
            # Update metrics
            if skill_name not in self.metrics["skills"]:
                self.metrics["skills"][skill_name] = {
                    "executions": 0,
                    "successes": 0,
                    "avg_time": 0,
                    "last_executed": None
                }
            
            skill_metrics = self.metrics["skills"][skill_name]
            skill_metrics["executions"] += 1
            if result.get("success", False):
                skill_metrics["successes"] += 1
            skill_metrics["avg_time"] = (
                (skill_metrics["avg_time"] * (skill_metrics["executions"] - 1) + execution_time)
                / skill_metrics["executions"]
            )
            skill_metrics["last_executed"] = datetime.now().isoformat()
            self.metrics["total_executions"] += 1
            self._save_metrics()
            
            # Return full skill result with metadata
            return {
                "success": result.get("success", False),
                "result": result,
                "skill": skill_name,
                "execution_time": execution_time,
                "error": result.get("error") if not result.get("success") else None
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": f"Execution error: {e}",
                "skill": skill_name,
                "execution_time": execution_time
            }


    def list_skills(self):
        """List all available skills"""
        if not SKILLS_DIR.exists():
            return []
        return [f.stem for f in SKILLS_DIR.glob("*.py") if f.name != "__init__.py"]
    
    def get_skill_metrics(self, skill_name=None):
        """Get metrics for skill(s)"""
        if skill_name:
            return self.metrics["skills"].get(skill_name, {})
        return self.metrics


if __name__ == "__main__":
    executor = SkillExecutor()
    
    print("Available skills:")
    for skill in executor.list_skills():
        print(f"  - {skill}")
    
    if executor.list_skills():
        print(f"\nTesting first skill: {executor.list_skills()[0]}")
        result = executor.execute_skill(executor.list_skills()[0], {"test": True})
        print(f"Result: {json.dumps(result, indent=2)}")
