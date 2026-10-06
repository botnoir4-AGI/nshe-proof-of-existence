#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AUTARCH Skill Verifier - Darwin Godel safety gates"""

import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from datetime import datetime

AUTARCH_DIR = Path(__file__).parent
SKILLS_DIR = AUTARCH_DIR.parent / "skills"
QUARANTINE_DIR = AUTARCH_DIR / "skills_quarantine"
REVIEW_DIR = AUTARCH_DIR / "skills_review"
LOG_FILE = AUTARCH_DIR / "skill_verify_log.jsonl"

SKILLS_DIR.mkdir(parents=True, exist_ok=True)
QUARANTINE_DIR.mkdir(exist_ok=True)
REVIEW_DIR.mkdir(exist_ok=True)

FORBIDDEN_CALLS = {"eval", "exec", "__import__", "compile", "execfile"}
DANGEROUS_IMPORTS = {"subprocess", "shutil", "ctypes"}


class SkillVerifier:
    """Verifies generated skills for safety and correctness"""

    def verify(self, code, name):
        result = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "verdict": "REJECT",
            "reason": "",
            "issues": []
        }

        # 1. Syntax check
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            result["reason"] = f"Syntax error: {e}"
            result["issues"].append("syntax")
            self._log(result)
            return result

        # 2. Forbidden calls
        forbidden = self._check_forbidden(tree)
        if forbidden:
            result["reason"] = f"Forbidden: {forbidden}"
            result["issues"].append("forbidden_calls")
            self._quarantine(code, name, result)
            self._log(result)
            return result

        # 3. Required elements
        if not self._has_required(code):
            result["reason"] = "Missing SKILL_NAME/SKILL_DESCRIPTION/execute()"
            result["issues"].append("missing_elements")
            self._log(result)
            return result

        # 4. Sandbox execution
        sandbox = self._sandbox_execute(code)
        if not sandbox["success"]:
            result["reason"] = f"Sandbox: {sandbox['error']}"
            result["issues"].append("sandbox_failed")
            self._quarantine(code, name, result)
            self._log(result)
            return result

        # 5. Valid return
        if not self._valid_return(sandbox["output"]):
            result["verdict"] = "REVIEW"
            result["reason"] = "Return needs review"
            self._review(code, name, result)
            self._log(result)
            return result

        # 6. PROMOTE
        result["verdict"] = "PROMOTE"
        result["reason"] = "All checks passed"
        self._promote(code, name)
        self._log(result)
        return result

    def _check_forbidden(self, tree):
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    found.append(node.func.id)
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name in DANGEROUS_IMPORTS:
                        found.append(f"import {a.name}")
            if isinstance(node, ast.ImportFrom):
                if node.module in DANGEROUS_IMPORTS:
                    found.append(f"from {node.module}")
        return found

    def _has_required(self, code):
        return ("SKILL_NAME" in code and
                "SKILL_DESCRIPTION" in code and
                ("def execute(" in code or "def execute (" in code))

    def _sandbox_execute(self, code):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            skill_file = tmp / "skill.py"
            test_file = tmp / "test.py"

            skill_file.write_text(code, encoding="utf-8")

            test_code = (
                "import sys, json\n"
                f"sys.path.insert(0, r'{tmp}')\n"
                "try:\n"
                "    import skill\n"
                "    if not hasattr(skill, 'execute'):\n"
                '        print(json.dumps({"error": "no execute"}))\n'
                "        sys.exit(1)\n"
                '    result = skill.execute({"test": True})\n'
                '    print(json.dumps({"success": True, "output": result}))\n'
                "except Exception as e:\n"
                '    print(json.dumps({"success": False, "error": str(e)}))\n'
            )
            test_file.write_text(test_code, encoding="utf-8")

            try:
                proc = subprocess.run(
                    [sys.executable, str(test_file)],
                    capture_output=True, text=True, timeout=10, cwd=str(tmp)
                )
                if proc.returncode != 0:
                    return {"success": False, "error": proc.stderr[:200]}
                try:
                    return json.loads(proc.stdout.strip())
                except:
                    return {"success": False, "error": f"Bad JSON: {proc.stdout[:100]}"}
            except subprocess.TimeoutExpired:
                return {"success": False, "error": "Timeout (>10s)"}
            except Exception as e:
                return {"success": False, "error": str(e)}

    def _valid_return(self, output):
        return isinstance(output, dict) and "success" in output

    def _promote(self, code, name):
        dest = SKILLS_DIR / f"{name}.py"
        dest.write_text(code, encoding="utf-8")
        print(f"  OK PROMOTED: {dest}")

    def _quarantine(self, code, name, result):
        dest = QUARANTINE_DIR / f"{name}_rejected.py"
        header = f"# REJECTED: {result['reason']}\n"
        dest.write_text(header + code, encoding="utf-8")

    def _review(self, code, name, result):
        dest = REVIEW_DIR / f"{name}_review.py"
        header = f"# REVIEW: {result['reason']}\n"
        dest.write_text(header + code, encoding="utf-8")

    def _log(self, result):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")


def verify_skill(code, name):
    return SkillVerifier().verify(code, name)


if __name__ == "__main__":
    test = '''
SKILL_NAME = "test_skill"
SKILL_DESCRIPTION = "Test skill"

def execute(context):
    return {"success": True, "data": "hello"}
'''
    print(json.dumps(verify_skill(test, "test_skill"), indent=2))
