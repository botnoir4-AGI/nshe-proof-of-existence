#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH System 4: Intelligence Layer v2
- Gemini real-time intel THROTTLED (every 3 cycles)
- RSS feeds as emergency fallback (every 10 cycles)
- HoneypotPipeline + ThreatCorrelation run every cycle
- Curriculum pipeline: Gemini/RSS/Honeypot -> tasks -> curriculum -> daemon execution
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

try:
    from honeypot_pipeline import HoneypotPipeline
except ImportError:
    HoneypotPipeline = None

INTEL_DIR = Path(r"C:\UMBRA_CORE\umbra-sovereign\threat_intel")
CURRICULUM_FILE = INTEL_DIR / "curriculum.json"
TTP_DB = INTEL_DIR / "ttp_database.json"
ATTACKER_DB = INTEL_DIR / "attacker_database.json"
INTEL_LOG = INTEL_DIR / "intelligence_log.jsonl"
FP_FILE = INTEL_DIR / "executed_fingerprints.json"
SUPPLEMENT_FILE = INTEL_DIR / "mitre_supplement.json"


def fingerprint(task):
    """Generate stable fingerprint for task"""
    # Use task ID if available (most stable)
    if task.get("id"):
        return hashlib.sha256(str(task.get("id")).encode("utf-8")).hexdigest()[:16]
    
    # Fallback to type + description
    task_type = task.get("type", "")
    description = task.get("description", "")
    
    # Normalize description: remove extra whitespace
    description = " ".join(description.split())
    
    key = "{}|{}".format(task_type, description).lower().strip()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


class IntelligenceLayer:
    """System 4: Intelligence - Future scanning + curriculum"""

    def __init__(self):
        INTEL_DIR.mkdir(parents=True, exist_ok=True)
        self.curriculum = self.load_curriculum()
        self.ttp_db = self.load_ttp_db()
        self.attacker_db = self.load_attacker_db()
        self.executed_fps = self._load_fingerprints()
        self.rss_scan_cycle = 0

    def _load_fingerprints(self):
        if FP_FILE.exists():
            try:
                return set(json.loads(FP_FILE.read_text(encoding="utf-8")))
            except Exception:
                pass
        return set()

    def load_curriculum(self) -> Dict:
        if CURRICULUM_FILE.exists():
            try:
                with open(CURRICULUM_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"active_goals": [], "completed_goals": [], "proposed_tasks": [], "last_update": None}

    def save_curriculum(self):
        self.curriculum["last_update"] = datetime.now().isoformat()
        with open(CURRICULUM_FILE, "w", encoding="utf-8") as f:
            json.dump(self.curriculum, f, indent=2, ensure_ascii=False)

    def load_ttp_db(self) -> Dict:
        if TTP_DB.exists():
            try:
                with open(TTP_DB, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def load_attacker_db(self) -> Dict:
        if ATTACKER_DB.exists():
            try:
                with open(ATTACKER_DB, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def propose_tasks(self) -> List[Dict]:
        """Propose learning tasks. Priority order:
        1. Unlearned supplement TTPs (MITRE database)
        2. Honeypot-derived tasks (new TTPs seen in attacks)
        3. System optimization tasks
        All filtered against executed fingerprints.
        """
        tasks = []

        # 1. Supplement: unlearned MITRE TTPs
        if SUPPLEMENT_FILE.exists():
            try:
                with open(SUPPLEMENT_FILE, "r", encoding="utf-8") as f:
                    sup = json.load(f)
                for t in sup.get("tasks", []):
                    fp = fingerprint(t)
                    if fp not in self.executed_fps:
                        tasks.append(t)
                        if len(tasks) >= 15:
                            break
            except Exception as e:
                print(f"[INTEL] Supplement error: {e}")

        # 2. Honeypot-derived tasks
        honeypot_log = Path(r"C:\UMBRA_CORE\honeypot\blackvault.jsonl")
        if honeypot_log.exists():
            try:
                with open(honeypot_log, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-100:]
                for line in lines:
                    try:
                        event = json.loads(line)
                    except Exception:
                        continue
                    ttp = event.get("kind", "unknown")
                    if ttp and ttp not in self.ttp_db:
                        t = {
                            "type": "learn_ttp",
                            "ttp": ttp,
                            "priority": "high",
                            "description": f"Learn about TTP: {ttp}"
                        }
                        fp = fingerprint(t)
                        if fp not in self.executed_fps:
                            tasks.append(t)
            except Exception:
                pass

        # 3. System tasks
        try:
            import psutil
            ram = psutil.virtual_memory().percent
            if ram > 85:
                tasks.append({
                    "type": "optimize",
                    "priority": "high",
                    "description": f"Optimize memory usage (current: {ram:.0f}%)"
                })
        except Exception:
            pass

        return tasks

    def correlate_attacks(self) -> Dict:
        honeypot_log = Path(r"C:\UMBRA_CORE\honeypot\blackvault.jsonl")
        if not honeypot_log.exists():
            return {"correlations": 0}

        try:
            with open(honeypot_log, "r", encoding="utf-8") as f:
                lines = f.readlines()[-50:]
            events = []
            for line in lines:
                try:
                    events.append(json.loads(line))
                except Exception:
                    continue
        except Exception:
            return {"correlations": 0}

        correlations = 0
        for event in events:
            src_ip = event.get("src", "unknown")
            if src_ip in self.attacker_db:
                self.attacker_db[src_ip]["last_seen"] = event.get("ts")
                self.attacker_db[src_ip]["event_count"] = self.attacker_db[src_ip].get("event_count", 0) + 1
                correlations += 1
            else:
                self.attacker_db[src_ip] = {
                    "first_seen": event.get("ts"),
                    "last_seen": event.get("ts"),
                    "event_count": 1,
                    "ttps": [event.get("kind")],
                    "threat_level": "unknown"
                }

        try:
            with open(ATTACKER_DB, "w", encoding="utf-8") as f:
                json.dump(self.attacker_db, f, indent=2)
        except Exception:
            pass

        return {"correlations": correlations, "unique_attackers": len(self.attacker_db)}

    def calculate_efe_attacker(self, attacker_ip: str) -> float:
        if attacker_ip not in self.attacker_db:
            return 0.0
        attacker = self.attacker_db[attacker_ip]
        event_count = attacker.get("event_count", 0)
        ttp_diversity = len(attacker.get("ttps", []))
        return min((event_count + ttp_diversity) / 20.0, 1.0)

    def scan_intelligence(self) -> Dict:
        """
        Primary: Gemini real-time intelligence (port 8001) - THROTTLED every 3 cycles
        Fallback: RSS feeds (every 10 cycles)
        Always: HoneypotPipeline + ThreatCorrelation
        """
        self.rss_scan_cycle += 1
        
        # PRIORITY 1: Gemini real-time intel (THROTTLED: every 3 cycles)
        if self.rss_scan_cycle % 3 == 0:
            try:
                sys.path.insert(0, str(Path(__file__).parent))
                from gemini_feeder import GeminiFeeder
                
                # Rotate focus areas: comprehensive -> cve_focus -> campaign_focus
                focus_areas = ["comprehensive", "cve_focus", "campaign_focus"]
                focus = focus_areas[self.rss_scan_cycle % len(focus_areas)]
                
                feeder = GeminiFeeder()
                result = feeder.run_feed_cycle(focus_area=focus)
                
                if result.get("success"):
                    gemini_tasks = result.get("tasks", [])
                    
                    # Add to curriculum (dedup)
                    existing_fps = {fingerprint(t) for t in self.curriculum.get("proposed_tasks", [])}
                    new_tasks = [t for t in gemini_tasks if fingerprint(t) not in existing_fps and fingerprint(t) not in self.executed_fps]
                    
                    if new_tasks:
                        self.curriculum.setdefault("proposed_tasks", []).extend(new_tasks)
                        self.save_curriculum()
                        print(f"[INTEL] Gemini ({focus}): {len(new_tasks)} new tasks added")
                    
                    # Log strategic insights
                    insights = result.get("intel_data", {}).get("strategic_insights", "")
                    if insights:
                        print(f"[INTEL] Strategic insight: {insights[:200]}")
                    
                    # Continue to Honeypot/Correlation instead of returning
                else:
                    print(f"[INTEL] Gemini query failed: {result.get('error', 'unknown')}")
            
            except Exception as e:
                print(f"[INTEL] Gemini feeder error: {e}")
        
        else:
            print(f"[INTEL] Gemini feeder THROTTLED (cycle {self.rss_scan_cycle})")
        
        # FALLBACK: RSS only every 10 cycles (emergency, heavy)
        if self.rss_scan_cycle % 10 == 0:
            print("[INTEL] Checking RSS fallback (rare event)")
            try:
                from rss_scanner import RSSScanner
                scanner = RSSScanner()
                result = scanner.run_scan()
                
                rss_tasks = result.get("tasks", [])
                if rss_tasks:
                    existing_fps = {fingerprint(t) for t in self.curriculum.get("proposed_tasks", [])}
                    new_tasks = [t for t in rss_tasks if fingerprint(t) not in existing_fps and fingerprint(t) not in self.executed_fps]
                    if new_tasks:
                        self.curriculum.setdefault("proposed_tasks", []).extend(new_tasks)
                        self.save_curriculum()
                        print(f"[INTEL] RSS fallback: {len(new_tasks)} tasks added")
            except Exception as e:
                print(f"[INTEL] RSS fallback also failed: {e}")
        
        # HONEYPOT PIPELINE: Process Black Vault events (always run)
        try:
            if HoneypotPipeline is not None:
                honeypot = HoneypotPipeline()
                hp_result = honeypot.run_pipeline()
                
                if hp_result.get("success") and hp_result.get("tasks"):
                    hp_tasks = hp_result["tasks"]
                    existing_fps = {fingerprint(t) for t in self.curriculum.get("proposed_tasks", [])}
                    new_hp_tasks = [t for t in hp_tasks if fingerprint(t) not in existing_fps and fingerprint(t) not in self.executed_fps]
                    
                    if new_hp_tasks:
                        self.curriculum.setdefault("proposed_tasks", []).extend(new_hp_tasks)
                        self.save_curriculum()
                        print(f"[HONEYPOT] Added {len(new_hp_tasks)} honeypot tasks to curriculum")
            else:
                print("[HONEYPOT] HoneypotPipeline not available (import failed)")
        except Exception as e:
            print(f"[HONEYPOT] Pipeline error: {e}")
        
        # THREAT CORRELATION: Run correlation cycle (always run)
        try:
            from threat_correlation import ThreatCorrelationEngine
            correlator = ThreatCorrelationEngine()
            
            # Add current intel entities
            for task in self.curriculum.get("proposed_tasks", [])[-10:]:
                entity_type = "cve" if task.get("type") == "learn_cve" else "ttp"
                correlator.add_entity(entity_type, task)
            
            corr_result = correlator.run_correlation_cycle()
            if corr_result.get("campaigns_detected", 0) > 0:
                print(f"[CORRELATION] {corr_result['campaigns_detected']} campaign(s) detected")
        except Exception as e:
            print(f"[CORRELATION] Error: {e}")

        return {
            "timestamp": datetime.now().isoformat(),
            "source": "gemini_throttled" if self.rss_scan_cycle % 3 != 0 else "gemini",
            "tasks_generated": 0,
            "cycle": self.rss_scan_cycle
        }

    def run_cycle(self) -> Dict:
        """Run full intelligence cycle"""
        print("[INTEL] Running intelligence cycle...")

        # 1. Scan intelligence (Gemini throttled + Honeypot + Correlation)
        scan = self.scan_intelligence()
        print(f"[INTEL] Scanned {scan.get('sources_scanned', 0)} sources")

        # 2. Propose tasks
        tasks = self.propose_tasks()
        print(f"[INTEL] Proposed {len(tasks)} tasks")

        # 3. Correlate attacks
        correlations = self.correlate_attacks()
        print(f"[INTEL] Correlated {correlations['correlations']} events")

        # 4. Calculate EFE for top attackers
        top_attackers = sorted(
            self.attacker_db.items(),
            key=lambda x: x[1].get("event_count", 0),
            reverse=True
        )[:5]

        efe_scores = {}
        for ip, profile in top_attackers:
            efe = self.calculate_efe_attacker(ip)
            efe_scores[ip] = efe
            print(f"[INTEL] EFE({ip}) = {efe:.3f}")

        return {
            "timestamp": datetime.now().isoformat(),
            "tasks_proposed": len(tasks),
            "correlations": correlations,
            "scan_result": scan,
            "efe_scores": efe_scores
        }

    def run_honeypot_pipeline(self):
        """Run Black Vault honeypot → intelligence pipeline"""
        try:
            if HoneypotPipeline is None:
                print("[HONEYPOT] HoneypotPipeline not available (import failed)")
                return {"success": False, "error": "import_failed"}
                
            honeypot = HoneypotPipeline()
            hp_result = honeypot.run_pipeline()
            
            if hp_result.get("success") and hp_result.get("tasks"):
                hp_tasks = hp_result["tasks"]
                existing_fps = {fingerprint(t) for t in self.curriculum.get("proposed_tasks", [])}
                new_hp_tasks = [t for t in hp_tasks 
                               if fingerprint(t) not in existing_fps 
                               and fingerprint(t) not in self.executed_fps]
                
                if new_hp_tasks:
                    self.curriculum.setdefault("proposed_tasks", []).extend(new_hp_tasks)
                    self.save_curriculum()
                    print(f"[HONEYPOT] Added {len(new_hp_tasks)} honeypot tasks to curriculum")
                
                return hp_result
            else:
                print(f"[HONEYPOT] Pipeline: {hp_result.get('message', 'no events')}")
                return hp_result
        except Exception as e:
            print(f"[HONEYPOT] Pipeline error: {e}")
            return {"success": False, "error": str(e)}
    
    def run_correlation(self):
        """Run threat correlation engine"""
        try:
            from threat_correlation import ThreatCorrelationEngine
            correlator = ThreatCorrelationEngine()
            
            # Feed current curriculum tasks as entities
            for task in self.curriculum.get("proposed_tasks", [])[-15:]:
                task_type = task.get("type", "unknown")
                entity_type = "cve" if task_type == "learn_cve" else "ttp"
                correlator.add_entity(entity_type, task)
            
            corr_result = correlator.run_correlation_cycle()
            
            if corr_result.get("campaigns_detected", 0) > 0:
                print(f"[CORRELATION] {corr_result['campaigns_detected']} campaign(s) detected!")
            
            return corr_result
        except Exception as e:
            print(f"[CORRELATION] Error: {e}")
            return {"success": False, "error": str(e)}


if __name__ == "__main__":
    intel = IntelligenceLayer()
    if len(sys.argv) > 1 and sys.argv[1] == "cycle":
        result = intel.run_cycle()
        print(json.dumps(result, indent=2, default=str))
    elif len(sys.argv) > 1 and sys.argv[1] == "propose":
        tasks = intel.propose_tasks()
        print(json.dumps(tasks[:10], indent=2))
    else:
        result = intel.run_cycle()
        print(json.dumps(result, indent=2, default=str))