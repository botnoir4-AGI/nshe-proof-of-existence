#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Threat Correlation Engine
Connects CVEs + TTPs + actors = campaigns.
Temporal, infrastructure, and behavioral correlation.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

THREAT_INTEL_DIR = Path(r"C:\UMBRA_CORE\umbra-sovereign\threat_intel")
CORRELATION_DB = THREAT_INTEL_DIR / "correlation_db.json"
CAMPAIGN_DB = THREAT_INTEL_DIR / "campaign_db.json"


class ThreatCorrelationEngine:
    """
    Correlates threat intelligence entities:
    - CVEs (vulnerabilities)
    - TTPs (techniques)
    - Actors (threat groups)
    - Infrastructure (IPs, domains)
    """
    
    def __init__(self):
        self.correlation_db = self._load_db(CORRELATION_DB)
        self.campaign_db = self._load_db(CAMPAIGN_DB)
    
    def _load_db(self, path: Path) -> Dict:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"entities": [], "correlations": [], "campaigns": []}
    
    def _save_db(self, path: Path, data: Dict):
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    def add_entity(self, entity_type: str, data: Dict):
        """Add entity to correlation database"""
        entity = {
            "type": entity_type,  # cve, ttp, actor, infrastructure
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "id": hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()[:12]
        }
        
        self.correlation_db["entities"].append(entity)
        
        # Keep last 500 entities
        if len(self.correlation_db["entities"]) > 500:
            self.correlation_db["entities"] = self.correlation_db["entities"][-500:]
        
        self._save_db(CORRELATION_DB, self.correlation_db)
    
    def correlate_temporal(self, window_minutes: int = 60) -> List[Dict]:
        """Correlate events by time window"""
        correlations = []
        entities = self.correlation_db["entities"]
        
        # Sort by timestamp
        sorted_entities = sorted(
            entities,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        
        # Find entities within time window
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        recent_entities = []
        for entity in sorted_entities:
            try:
                ts = datetime.fromisoformat(entity.get("timestamp", now.isoformat()))
                if ts >= window_start:
                    recent_entities.append(entity)
            except Exception:
                continue
        
        # Group by time proximity
        if len(recent_entities) >= 2:
            correlation = {
                "type": "temporal",
                "window_minutes": window_minutes,
                "entities": recent_entities[:10],
                "entity_count": len(recent_entities),
                "confidence": min(0.9, len(recent_entities) * 0.1),
                "timestamp": datetime.now().isoformat()
            }
            correlations.append(correlation)
        
        return correlations
    
    def correlate_infrastructure(self) -> List[Dict]:
        """Correlate by shared infrastructure (IPs, subnets)"""
        correlations = []
        
        # Extract all IPs from entities
        ip_entities = defaultdict(list)
        for entity in self.correlation_db["entities"]:
            data = entity.get("data", {})
            
            # Check for IP addresses
            for key in ["source_ip", "ip", "infrastructure", "target"]:
                ip = data.get(key, "")
                if ip and self._is_ip(ip):
                    ip_entities[ip].append(entity)
            
            # Check for source_ip in data
            source_ip = data.get("source_ip", "")
            if source_ip and self._is_ip(source_ip):
                ip_entities[source_ip].append(entity)
        
        # Find IPs with multiple entities
        for ip, entities in ip_entities.items():
            if len(entities) >= 2:
                correlation = {
                    "type": "infrastructure",
                    "shared_ip": ip,
                    "entities": entities[:5],
                    "entity_count": len(entities),
                    "confidence": min(0.9, len(entities) * 0.15),
                    "timestamp": datetime.now().isoformat()
                }
                correlations.append(correlation)
        
        # Correlate by subnet (/24)
        subnet_entities = defaultdict(list)
        for ip in ip_entities:
            parts = ip.split(".")
            if len(parts) == 4:
                subnet = ".".join(parts[:3]) + ".0/24"
                subnet_entities[subnet].extend(ip_entities[ip])
        
        for subnet, entities in subnet_entities.items():
            if len(entities) >= 3:
                correlation = {
                    "type": "infrastructure_subnet",
                    "subnet": subnet,
                    "entity_count": len(entities),
                    "confidence": min(0.8, len(entities) * 0.1),
                    "timestamp": datetime.now().isoformat()
                }
                correlations.append(correlation)
        
        return correlations
    
    def correlate_behavior(self) -> List[Dict]:
        """Correlate by TTP patterns (similar technique sequences)"""
        correlations = []
        
        # Extract all TTPs
        ttp_entities = defaultdict(list)
        for entity in self.correlation_db["entities"]:
            data = entity.get("data", {})
            ttp = data.get("ttp") or data.get("ttp_id") or ""
            if ttp:
                ttp_entities[ttp].append(entity)
        
        # Find TTPs with multiple entities
        for ttp, entities in ttp_entities.items():
            if len(entities) >= 2:
                correlation = {
                    "type": "behavioral",
                    "shared_ttp": ttp,
                    "entities": entities[:5],
                    "entity_count": len(entities),
                    "confidence": min(0.85, len(entities) * 0.12),
                    "timestamp": datetime.now().isoformat()
                }
                correlations.append(correlation)
        
        return correlations
    
    def detect_campaigns(self, min_correlations: int = 3) -> List[Dict]:
        """Detect coordinated campaigns from correlations"""
        campaigns = []
        
        # Run all correlation types
        temporal = self.correlate_temporal()
        infrastructure = self.correlate_infrastructure()
        behavioral = self.correlate_behavior()
        
        all_correlations = temporal + infrastructure + behavioral
        
        # Count correlations per entity
        entity_correlation_count = defaultdict(int)
        for corr in all_correlations:
            for entity in corr.get("entities", []):
                entity_id = entity.get("id", "")
                if entity_id:
                    entity_correlation_count[entity_id] += 1
        
        # Identify highly correlated entities (potential campaigns)
        if len(all_correlations) >= min_correlations:
            campaign = {
                "campaign_id": hashlib.md5(
                    json.dumps([c["type"] for c in all_correlations]).encode()
                ).hexdigest()[:12],
                "detected_at": datetime.now().isoformat(),
                "correlation_count": len(all_correlations),
                "correlation_types": list(set(c["type"] for c in all_correlations)),
                "highly_correlated_entities": [
                    eid for eid, count in entity_correlation_count.items()
                    if count >= 2
                ][:10],
                "confidence": min(0.95, len(all_correlations) * 0.08),
                "status": "active"
            }
            campaigns.append(campaign)
            
            self.campaign_db["campaigns"].append(campaign)
            self._save_db(CAMPAIGN_DB, self.campaign_db)
        
        return campaigns
    
    def run_correlation_cycle(self) -> Dict:
        """Run full correlation cycle"""
        print("[CORRELATION] Starting correlation cycle...")
        start_time = datetime.now()
        
        # Run correlations
        temporal = self.correlate_temporal()
        infrastructure = self.correlate_infrastructure()
        behavioral = self.correlate_behavior()
        
        all_correlations = temporal + infrastructure + behavioral
        
        # Detect campaigns
        campaigns = self.detect_campaigns()
        
        # Store correlations
        self.correlation_db["correlations"] = all_correlations[-50:]  # Keep last 50
        self._save_db(CORRELATION_DB, self.correlation_db)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"[CORRELATION] Cycle complete: {len(all_correlations)} correlations, {len(campaigns)} campaigns ({duration:.1f}s)")
        
        return {
            "success": True,
            "temporal_correlations": len(temporal),
            "infrastructure_correlations": len(infrastructure),
            "behavioral_correlations": len(behavioral),
            "campaigns_detected": len(campaigns),
            "campaigns": campaigns,
            "duration": duration
        }
    
    def _is_ip(self, text: str) -> bool:
        """Check if text looks like an IP address"""
        import re
        return bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', str(text)))


if __name__ == "__main__":
    engine = ThreatCorrelationEngine()
    
    # Add test entities
    engine.add_entity("ttp", {"ttp": "T1110.001", "source_ip": "45.33.1.1", "description": "SSH brute force"})
    engine.add_entity("ttp", {"ttp": "T1059", "source_ip": "45.33.1.1", "description": "Command execution"})
    engine.add_entity("cve", {"cve_id": "CVE-2026-85880", "source_ip": "45.33.1.1"})
    
    # Run correlation
    result = engine.run_correlation_cycle()
    print(f"\nResult: {json.dumps(result, indent=2)[:1500]}")
