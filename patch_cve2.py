
from pathlib import Path

ORCH = Path("orchestrator.py")
code = ORCH.read_text(encoding="utf-8")

marker = "                self._commit_to_swarm(successful_results)"

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
                            executed_fps.add("cve:" + cid)
                # Save fingerprints with CVE keys
                FP_FILE.write_text(json.dumps(sorted(list(executed_fps))), encoding="utf-8")"""

if marker in code and "Save CVE IDs" not in code:
    code = code.replace(marker, marker + cve_save, 1)
    print("  CVE save logic added after _commit_to_swarm")
else:
    print("  Skipped (already present or marker not found)")

try:
    compile(code, "orchestrator.py", "exec")
    ORCH.write_text(code, encoding="utf-8")
    print("  OK: Syntax valid, file saved")
except SyntaxError as e:
    print(f"  ERROR: line {e.lineno}: {e.msg}")
