#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH System 2: Skill Library
Lightweight executable skills with TF-IDF retrieval (~50MB RAM footprint)

Based on Voyager pattern: skills as executable .py files
- Self-verification after execution
- Feedback tracking (success/failure)
- Semantic retrieval via TF-IDF (no heavy embeddings)
"""

import os
import sys
import json
import subprocess
import hashlib
from datetime import datetime
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

SKILLS_DIR = Path(r"C:\UMBRA_CORE\skills")
FEEDBACK_LOG = Path(r"C:\UMBRA_CORE\skills\feedback.jsonl")
SKILL_INDEX = Path(r"C:\UMBRA_CORE\skills\skill_index.json")

class SkillLibrary:
    """System 2: Coordination Layer - Executable skill management"""

    def __init__(self):
        SKILLS_DIR.mkdir(exist_ok=True)
        self.vectorizer = None
        self.skill_vectors = None
        self.skill_metadata = {}
        self.load_index()

    def load_index(self):
        """Load skill metadata and build index"""
        if SKILL_INDEX.exists():
            with open(SKILL_INDEX, "r", encoding="utf-8") as f:
                self.skill_metadata = json.load(f)
        else:
            self.skill_metadata = {}

        # Rebuild from actual files
        self.rebuild_index()

    def rebuild_index(self):
        """Scan skills directory and build TF-IDF index"""
        # Support multiple skill naming patterns (FIX: detect build_skill_*.py and learn_ttp_*.py)
        skill_files = []
        for pattern in ["skill_*.py", "build_skill_*.py", "learn_ttp_*.py", "analyze_*.py"]:
            skill_files.extend(SKILLS_DIR.glob(pattern))
        # Remove duplicates while preserving order
        seen = set()
        skill_files = [f for f in skill_files if not (f in seen or seen.add(f))]

        if not skill_files:
            print("No skills found. Creating example skill...")
            self.create_example_skill()
            # Support multiple skill naming patterns (FIX: detect build_skill_*.py and learn_ttp_*.py)
        skill_files = []
        for pattern in ["skill_*.py", "build_skill_*.py", "learn_ttp_*.py", "analyze_*.py"]:
            skill_files.extend(SKILLS_DIR.glob(pattern))
        # Remove duplicates while preserving order
        seen = set()
        skill_files = [f for f in skill_files if not (f in seen or seen.add(f))]

        # Build metadata
        for skill_file in skill_files:
            skill_name = skill_file.stem
            if skill_name not in self.skill_metadata:
                # Extract docstring as description
                with open(skill_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Simple docstring extraction
                docstring = ""
                if content.strip().startswith('"""'):
                    end = content.find('"""', 3)
                    if end != -1:
                        docstring = content[3:end].strip()

                self.skill_metadata[skill_name] = {
                    "path": str(skill_file),
                    "description": docstring,
                    "created": datetime.now().isoformat(),
                    "success_count": 0,
                    "failure_count": 0,
                    "last_used": None
                }

        # Build TF-IDF vectors
        descriptions = [meta["description"] for meta in self.skill_metadata.values()]
        if descriptions:
            self.vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
            try:
                self.skill_vectors = self.vectorizer.fit_transform(descriptions)
            except ValueError:
                # Handle case where all descriptions are stop words
                print("Warning: Empty vocabulary, using fallback")
                self.skill_vectors = None

        self.save_index()
        print(f"Indexed {len(self.skill_metadata)} skills")

    def create_example_skill(self):
        """Create example skill to demonstrate pattern"""
        example = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan system health: check disk usage, RAM, CPU, and network connectivity.
Use when: system feels slow, need baseline metrics, pre-task health check.
"""
import psutil
import subprocess
import json
from datetime import datetime

def execute():
    """Execute system health scan"""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "network_ok": check_network()
    }

    print(json.dumps(metrics, indent=2))
    return metrics

def check_network():
    """Check internet connectivity"""
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "8.8.8.8"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

if __name__ == "__main__":
    execute()
'''

        skill_path = SKILLS_DIR / "skill_system_health.py"
        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(example)

        print(f"Created example skill: {skill_path}")

    def retrieve(self, query: str, top_k: int = 3):
        """Retrieve most relevant skills for query"""
        if not self.vectorizer or self.skill_vectors is None:
            return []

        # Vectorize query
        query_vec = self.vectorizer.transform([query])

        # Compute similarity
        similarities = cosine_similarity(query_vec, self.skill_vectors).flatten()

        # Get top-k
        top_indices = similarities.argsort()[-top_k:][::-1]

        results = []
        skill_names = list(self.skill_metadata.keys())
        for idx in top_indices:
            if similarities[idx] > 0.1:  # threshold
                skill_name = skill_names[idx]
                results.append({
                    "name": skill_name,
                    "score": float(similarities[idx]),
                    "metadata": self.skill_metadata[skill_name]
                })

        return results

    def execute_skill(self, skill_name: str, timeout: int = 120):
        """Execute a skill and track outcome"""
        if skill_name not in self.skill_metadata:
            return {"error": f"Skill {skill_name} not found"}

        skill_path = self.skill_metadata[skill_name]["path"]

        try:
            result = subprocess.run(
                [sys.executable, skill_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(SKILLS_DIR)
            )

            success = result.returncode == 0
            output = result.stdout + "\n" + result.stderr

            # Update metadata
            self.skill_metadata[skill_name]["last_used"] = datetime.now().isoformat()
            if success:
                self.skill_metadata[skill_name]["success_count"] += 1
            else:
                self.skill_metadata[skill_name]["failure_count"] += 1

            # Log feedback
            self.log_feedback(skill_name, success, output)

            return {
                "skill": skill_name,
                "success": success,
                "output": output,
                "returncode": result.returncode
            }

        except subprocess.TimeoutExpired:
            self.log_feedback(skill_name, False, "Timeout")
            return {"error": "Timeout", "skill": skill_name}
        except Exception as e:
            self.log_feedback(skill_name, False, str(e))
            return {"error": str(e), "skill": skill_name}

    def log_feedback(self, skill_name: str, success: bool, output: str):
        """Log execution feedback"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "skill": skill_name,
            "success": success,
            "output_preview": output[:500]
        }

        with open(FEEDBACK_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def save_index(self):
        """Save skill metadata"""
        with open(SKILL_INDEX, "w", encoding="utf-8") as f:
            json.dump(self.skill_metadata, f, indent=2)

    def add_skill(self, name: str, description: str = "Auto-generated skill", code: str = "pass"):
        """Add new skill to library"""
        skill_name = f"skill_{name}"
        skill_path = SKILLS_DIR / f"{skill_name}.py"

        full_code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{description}
"""
{code}
'''

        with open(skill_path, "w", encoding="utf-8") as f:
            f.write(full_code)

        self.skill_metadata[skill_name] = {
            "path": str(skill_path),
            "description": description,
            "created": datetime.now().isoformat(),
            "success_count": 0,
            "failure_count": 0,
            "last_used": None
        }

        self.rebuild_index()
        return skill_path

    def stats(self):
        """Get library statistics"""
        total = len(self.skill_metadata)
        total_success = sum(m["success_count"] for m in self.skill_metadata.values())
        total_failure = sum(m["failure_count"] for m in self.skill_metadata.values())

        return {
            "total_skills": total,
            "total_executions": total_success + total_failure,
            "success_rate": total_success / (total_success + total_failure) if (total_success + total_failure) > 0 else 0
        }

# CLI interface for testing
if __name__ == "__main__":
    lib = SkillLibrary()

    if len(sys.argv) < 2:
        print("Usage: python skill_library.py [retrieve|execute|stats] [args]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "retrieve":
        query = " ".join(sys.argv[2:])
        results = lib.retrieve(query)
        print(f"Top skills for query: {query}")
        for r in results:
            print(f"  - {r['name']} (score: {r['score']:.3f})")

    elif cmd == "execute":
        skill_name = sys.argv[2]
        result = lib.execute_skill(skill_name)
        print(json.dumps(result, indent=2))

    elif cmd == "stats":
        stats = lib.stats()
        print(json.dumps(stats, indent=2))

    elif cmd == "list":
        for name, meta in lib.skill_metadata.items():
            print(f"{name}: {meta['description'][:50]}")