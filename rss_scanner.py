#!/usr/bin/env python3
"""
AUTARCH RSS Scanner - Final Version with NVD API
Scans threat intelligence and generates actionable tasks
"""

import requests
import json
from datetime import datetime
from pathlib import Path

THREAT_INTEL_DIR = Path(r"C:\UMBRA_CORE\umbra-sovereign\threat_intel")
RSS_LOG = THREAT_INTEL_DIR / "rss_scan_log.jsonl"

class RSSScanner:
    def __init__(self):
        self.nvd_url = "https://services.nvd.nist.gov/rest/json/cves/2.0?resultsPerPage=10"
    
    def scan_nvd(self):
        """Fetch recent CVEs from NVD API"""
        try:
            r = requests.get(self.nvd_url, timeout=10, headers={"User-Agent": "AUTARCH/1.0"})
            if r.status_code == 200:
                data = r.json()
                vulns = data.get("vulnerabilities", [])
                
                cves = []
                for vuln in vulns:
                    cve_data = vuln.get("cve", {})
                    cves.append({
                        "id": cve_data.get("id", "UNKNOWN"),
                        "description": cve_data.get("descriptions", [{}])[0].get("value", "")[:200],
                        "severity": self._get_severity(vuln),
                        "published": cve_data.get("published", ""),
                        "timestamp": datetime.now().isoformat()
                    })
                
                return cves
            return []
        except Exception as e:
            print(f"[RSS] NVD error: {e}")
            return []
    
    def _get_severity(self, vuln):
        metrics = vuln.get("cve", {}).get("metrics", {})
        if "cvssMetricV31" in metrics:
            return metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseSeverity", "UNKNOWN")
        return "UNKNOWN"
    
    def scan_all(self):
        """Scan and generate tasks"""
        print("[RSS] Scanning NVD for recent CVEs...")
        cves = self.scan_nvd()
        print(f"[RSS] Found {len(cves)} CVEs")
        
        if not cves:
            return []
        
        # Generate tasks based on CVEs
        tasks = []
        
        # Task 1: Analyze critical CVEs
        critical_cves = [c for c in cves if c["severity"] in ["CRITICAL", "HIGH"]]
        if critical_cves:
            tasks.append({
                "id": f"cve_critical_{int(datetime.now().timestamp())}",
                "type": "cve_analysis",
                "priority": "high",
                "description": f"Analyze {len(critical_cves)} critical/high severity CVEs",
                "proposed_by": "rss-scanner",
                "cves": [c["id"] for c in critical_cves[:5]],
                "timestamp": datetime.now().isoformat()
            })
        
        # Task 2: Generate general CVE summary
        tasks.append({
            "id": f"cve_summary_{int(datetime.now().timestamp())}",
            "type": "threat_intelligence",
            "priority": "medium",
            "description": f"Summarize {len(cves)} recent CVEs from NVD",
            "proposed_by": "rss-scanner",
            "timestamp": datetime.now().isoformat()
        })
        
        # Log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "cves_scanned": len(cves),
            "critical_cves": len(critical_cves) if critical_cves else 0,
            "tasks_proposed": len(tasks)
        }
        
        with open(RSS_LOG, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        print(f"[RSS] Proposed {len(tasks)} tasks")
        return tasks

if __name__ == "__main__":
    scanner = RSSScanner()
    tasks = scanner.scan_all()
    print(f"\nGenerated {len(tasks)} tasks:")
    for task in tasks:
        print(f"  - {task['type']}: {task['description']}")
