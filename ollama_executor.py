#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH Ollama Executor (UMBRA V20 Daemon Integration)
Correct daemon format: {"prompt": "...", "reset_context": true}
"""

import requests
import json
import re
from datetime import datetime
from pathlib import Path

DAEMON_URL = "http://localhost:8001"
ENDPOINT = DAEMON_URL + "/v1/chat/completions"
EXECUTOR_LOG = Path(r"C:\UMBRA_CORE\autarch\daemon_execution_log.jsonl")
MEMORY_DIR = Path(r"C:\UMBRA_CORE\memory")


class OllamaExecutor:
    """Functional executor: capture Gemini response, parse insights, store to COALA."""

    def __init__(self, model="gemini-via-cdp"):
        self.model = model
        self.execution_history = []
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    def execute_task(self, task):
        task_type = task.get("type", "unknown")
        task_desc = task.get("description", "")
        task_id = task.get("id", "unknown")

        print("  Executing: " + str(task_type) + " - " + str(task_desc)[:60])

        # CHECK FOR LOCAL SKILL FIRST (Dynamic Import Execution)
        import importlib.util
        from pathlib import Path
        
        skills_dir = Path(r"C:\UMBRA_CORE\skills")
        matched_skill = None
        
        # STRICT MATCHING: Only hijack specific analytical tasks, NOT generic queries
        if task_type in ["learn_ttp", "learn_attribution", "analyze_cve", "execute_skill"]:
            task_keywords = task_desc.lower().replace("-", " ").replace("_", " ").split()
            for sf in skills_dir.glob("*.py"):
                sf_name = sf.stem.lower()
                # Require at least 2 significant keyword matches to prevent false positives
                matches = sum(1 for kw in task_keywords if len(kw) > 3 and kw in sf_name)
                if matches >= 2:
                    matched_skill = sf
                    break
        
        if matched_skill:
            print(f"    [DYNAMIC IMPORT] Executing local skill: {matched_skill.name}")
            try:
                # Dynamically import the skill module
                spec = importlib.util.spec_from_file_location("dynamic_skill", matched_skill)
                skill_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(skill_module)
                
                # Call the execute function with the task dict as context
                result_data = skill_module.execute(task)
                
                # Convert result dict to string for logging and storage
                content = json.dumps(result_data, indent=2)
                print("    OK Captured " + str(len(content)) + " chars")
                print("    Preview: " + content[:150] + "...")
                
                self._log_execution(task_id, task_type, content, ["Executed via dynamic import"], success=result_data.get("success", True))
                return {
                    "success": result_data.get("success", True),
                    "task_id": task_id,
                    "task_type": task_type,
                    "task_description": task_desc,
                    "content": content,
                    "insights": ["Dynamic skill execution"],
                    "length": len(content)
                }
            except Exception as e:
                print(f"    [WARNING] Dynamic skill execution failed: {e}. Falling back to LLM.")
                # Fall through to LLM execution if dynamic import fails

        # FALLBACK TO LLM
        prompt = (
            "You are AUTARCH Intelligence Layer (VSM System 4).\n\n"
            "TASK EXECUTION REQUEST:\n"
            "- Task ID: " + str(task_id) + "\n"
            "- Task Type: " + str(task_type) + "\n"
            "- Description: " + str(task_desc) + "\n"
            "- Context: Sovereign threat intelligence and autonomous analysis\n\n"
            "EXECUTION REQUIREMENTS:\n"
            "Provide detailed, actionable analysis. Include:\n"
            "1. Key findings or insights (3-5 bullet points)\n"
            "2. Recommended actions or next steps\n"
            "3. Relevant data points or evidence\n"
            "4. Code snippets if applicable (Python preferred)\n\n"
            "Be specific, technical, and actionable. Avoid generic advice."
        )

        try:
            response = requests.post(
                ENDPOINT,
                json={"prompt": prompt, "reset_context": True},
                timeout=300
            )

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                if content and len(content) > 50:
                    insights = self._parse_insights(content, task_type)

                    print("    OK Captured " + str(len(content)) + " chars")
                    print("    Insights: " + str(len(insights)) + " key points")
                    print("    Preview: " + content[:150] + "...")

                    self._log_execution(task_id, task_type, content, insights, success=True)

                    return {
                        "success": True,
                        "task_id": task_id,
                        "task_type": task_type,
                        "task_description": task_desc,
                        "content": content,
                        "insights": insights,
                        "length": len(content)
                    }
                else:
                    print("    X Empty or too short response")
                    self._log_execution(task_id, task_type, "", [], success=False, error="Empty response")
                    return {"success": False, "task_id": task_id, "task_type": task_type, "error": "Empty response"}
            else:
                error_msg = "HTTP " + str(response.status_code) + ": " + response.text[:150]
                print("    X " + error_msg)
                self._log_execution(task_id, task_type, "", [], success=False, error=error_msg)
                return {"success": False, "task_id": task_id, "task_type": task_type, "error": error_msg}

        except Exception as e:
            error_msg = str(e)[:200]
            print("    X Exception: " + error_msg)
            self._log_execution(task_id, task_type, "", [], success=False, error=error_msg)
            return {"success": False, "task_id": task_id, "task_type": task_type, "error": error_msg}

    def _parse_insights(self, content, task_type):
        insights = []
        bullets = re.findall(r"[-*]\s+([^\n]+)", content)
        insights.extend([b.strip()[:200] for b in bullets[:5]])
        numbered = re.findall(r"\d+\.\s+([^\n]+)", content)
        insights.extend([n.strip()[:200] for n in numbered[:5]])
        if not insights:
            sentences = re.split(r"[.!?]+", content)
            insights = [s.strip()[:200] for s in sentences[:3] if len(s.strip()) > 20]
        return insights[:10]

    def _log_execution(self, task_id, task_type, content, insights, success=True, error=None):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "task_type": task_type,
            "success": success,
            "content_length": len(content) if content else 0,
            "insights_count": len(insights),
            "insights": insights[:5],
            "error": error
        }
        try:
            with open(EXECUTOR_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print("[LOG] Write error: " + str(e))
        self.execution_history.append(log_entry)

    def execute_batch(self, tasks, max_tasks=3):
        n = min(max_tasks, len(tasks))
        print("[DAEMON] Executing " + str(n) + " tasks...")
        results = []
        for i, task in enumerate(tasks[:max_tasks]):
            print("  [" + str(i+1) + "/" + str(n) + "] " + str(task.get("type", "unknown")))
            result = self.execute_task(task)
            results.append(result)
            if result.get("success"):
                print("    OK Success (" + str(result.get("length", 0)) + " chars)")
            else:
                print("    X Failed: " + str(result.get("error", "Unknown"))[:80])
        successful = sum(1 for r in results if r.get("success"))
        print("[DAEMON] Execution complete: " + str(successful) + "/" + str(len(results)) + " successful")
        return results

    def store_to_memory(self, results):
        if not results:
            return
        successful = [r for r in results if r.get("success")]
        if not successful:
            return

        episodic_file = MEMORY_DIR / "episodic.jsonl"
        for result in successful:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "type": "daemon_execution",
                "task_id": result.get("task_id"),
                "task_type": result.get("task_type"),
                "content_length": result.get("length", 0),
                "insights": result.get("insights", [])[:5]
            }
            try:
                with open(episodic_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception as e:
                print("[MEMORY] Episodic write error: " + str(e))

        semantic_file = MEMORY_DIR / "semantic.json"
        try:
            if semantic_file.exists():
                with open(semantic_file, "r", encoding="utf-8") as f:
                    semantic = json.load(f)
            else:
                semantic = {"version": "1.0.0", "learned_patterns": [], "insights": []}
        except Exception:
            semantic = {"version": "1.0.0", "learned_patterns": [], "insights": []}

        semantic.setdefault("learned_patterns", [])
        for result in successful:
            semantic["learned_patterns"].append({
                "task_type": result.get("task_type"),
                "timestamp": datetime.now().isoformat(),
                "insights": result.get("insights", [])[:3]
            })
        semantic["learned_patterns"] = semantic["learned_patterns"][-100:]
        semantic["last_updated"] = datetime.now().isoformat()

        try:
            with open(semantic_file, "w", encoding="utf-8") as f:
                json.dump(semantic, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print("[MEMORY] Semantic write error: " + str(e))

        print("[MEMORY] Stored " + str(len(successful)) + " executions to COALA")
        print("[MEMORY] Semantic memory: " + str(len(semantic["learned_patterns"])) + " patterns")


if __name__ == "__main__":
    executor = OllamaExecutor()
    test_task = {
        "id": "test_001",
        "type": "threat_analysis",
        "description": "Test daemon connection and response format"
    }
    result = executor.execute_task(test_task)
    print("")
    print("=" * 60)
    print("TEST RESULT:")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
    if result.get("success"):
        executor.store_to_memory([result])
        print("OK Stored to memory")
