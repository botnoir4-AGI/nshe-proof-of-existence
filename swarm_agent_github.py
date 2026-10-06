#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH Swarm Agent - GitHub Ephemeral Version
Runs on GitHub Actions every 15 minutes.
Spawns, computes, commits, dies.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
import hashlib

# Add autarch to path
sys.path.insert(0, str(Path(__file__).parent))

THREAT_INTEL_DIR = Path("threat_intel")
SWARM_LOG = THREAT_INTEL_DIR / "swarm_log.jsonl"

def run_ephemeral_cycle():
    """Run one intelligence cycle and commit results"""
    
    print("=" * 80)
    print("AUTARCH EPHEMERAL AGENT - GitHub Actions")
    print("=" * 80)
    
    timestamp = datetime.now().isoformat()
    
    # 1. Pull latest state (stigmergic observation)
    print("\n[STEP 1] Observing swarm state...")
    THREAT_INTEL_DIR.mkdir(exist_ok=True)
    
    # Read existing curriculum (if any)
    curriculum_file = THREAT_INTEL_DIR / "curriculum.json"
    if curriculum_file.exists():
        with open(curriculum_file, "r") as f:
            curriculum = json.load(f)
        print(f"  ✓ Observed {len(curriculum.get('proposed_tasks', []))} tasks from swarm")
    else:
        curriculum = {"proposed_tasks": [], "completed_tasks": []}
        print("  ℹ No existing curriculum, starting fresh")
    
    # 2. Propose new tasks (stigmergic contribution)
    print("\n[STEP 2] Proposing learning tasks...")
    new_tasks = [
        {
            "id": hashlib.sha256(f"{timestamp}-{i}".encode()).hexdigest()[:8],
            "type": "threat_analysis",
            "priority": "medium",
            "description": f"Analyze TTP pattern #{i+1}",
            "proposed_by": "github-ephemeral",
            "timestamp": timestamp
        }
        for i in range(3)  # Propose 3 tasks per cycle
    ]
    
    curriculum["proposed_tasks"].extend(new_tasks)
    print(f"  ✓ Proposed {len(new_tasks)} new tasks")
    
    # 3. Commit to swarm (stigmergic coordination)
    print("\n[STEP 3] Committing to swarm...")
    
    # Save curriculum
    with open(curriculum_file, "w") as f:

                    # SWARM BLACKLIST FILTER - Remove stuck tasks permanently
                    _desc = task.get('description', '').lower()
                    if any(kw in _desc for kw in ["token harvesting", "vendor-oauth", "iran-linked", "ssh_connect"]):
                        continue

        json.dump(curriculum, f, indent=2)
    
    # Log swarm activity
    swarm_entry = {
        "timestamp": timestamp,
        "agent": "github-ephemeral",
        "action": "intelligence_cycle",
        "tasks_proposed": len(new_tasks),
        "total_tasks": len(curriculum["proposed_tasks"])
    }
    
    with open(SWARM_LOG, "a") as f:
        f.write(json.dumps(swarm_entry) + "\n")
    
    print(f"  ✓ Committed to swarm memory")
    
    # 4. Summary
    print("\n" + "=" * 80)
    print("EPHEMERAL CYCLE COMPLETE")
    print("=" * 80)
    print(f"Tasks proposed: {len(new_tasks)}")
    print(f"Total tasks in swarm: {len(curriculum['proposed_tasks'])}")
    print(f"Agent will now terminate (ephemeral lifecycle)")
    print("=" * 80)

if __name__ == "__main__":
    run_ephemeral_cycle()
