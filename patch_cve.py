
import json
from pathlib import Path

ORCH = Path("orchestrator.py")
code = ORCH.read_text(encoding="utf-8")

# ============================================================
# PATCH 1: Add CVE dedup filter before fingerprint filter
# ============================================================
marker1 = "        # Filter out already-executed tasks"

cve_filter = """        # CVE DEDUP: Filter already-executed CVEs by stable key
        cve_filtered = []
        for task in tasks:
            if task.get("type") == "learn_cve":
                cve_id = task.get("cve_id", "")
                if not cve_id:
                    desc = task.get("description", "")
                    if "CVE-" in desc:
                        idx = desc.find("CVE-")
                        cve_part = desc[idx:idx+20].split()[0].split(":")[0].rstrip(",")
                        cve_id = cve_part
                if cve_id and ("cve:" + cve_id) in executed_fps:
                    continue
            cve_filtered.append(task)
        tasks = cve_filtered

"""

if marker1 in code and "CVE DEDUP" not in code:
    code = code.replace(marker1, cve_filter + marker1, 1)
    print("  [1/2] CVE dedup filter added")
else:
    print("  [1/2] Skipped (already present or marker not found)")

# ============================================================
# PATCH 2: Save CVE IDs after successful execution
# ============================================================
marker2 = "                self._update_curriculum(successful_results)"

cve_save = """
                # Save CVE IDs to fingerprints (stable dedup key)
                for r in successful_results:
                    t = r.get("task", {})
                    if t.get("type") == "learn_cve":
                        cid = t.get("cve_id", "")
                        if not cid:
                            d = t.get("description", "")
                            if "CVE-" in d:
                                ii = d.find("CVE-")
                                cid = d[ii:ii+20].split()[0].split(":")[0].rstrip(",")
                        if cid:
                            executed_fps.add("cve:" + cid)"""

if marker2 in code and "Save CVE IDs" not in code:
    code = code.replace(marker2, marker2 + cve_save, 1)
    print("  [2/2] CVE save logic added")
else:
    print("  [2/2] Skipped (already present or marker not found)")

# Verify and save
try:
    compile(code, "orchestrator.py", "exec")
    ORCH.write_text(code, encoding="utf-8")
    print("\n  OK: Syntax valid, file saved")
except SyntaxError as e:
    print(f"\n  ERROR: Syntax error at line {e.lineno}: {e.msg}")
    print("  File NOT saved")
