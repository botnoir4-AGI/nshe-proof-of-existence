#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Multi-Stage Analyzer
parse → classify → context → recommend
Integrates causal reasoning, NSHE symbolic KB, and vector DB.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

AUTARCH_DIR = Path(r"C:\UMBRA_CORE\autarch")


class EnhancedAnalyzer:
    """
    Multi-stage analysis pipeline:
    Stage 1: Parse - Extract structured data from raw input
    Stage 2: Classify - Categorize threat type using patterns + symbolic KB
    Stage 3: Context - Add causal context + related intel
    Stage 4: Recommend - Generate defensive recommendations
    """
    
    def __init__(self):
        self.causal_engine = None
        self.nshe_bridge = None
        self._init_engines()
    
    def _init_engines(self):
        """Initialize sub-engines"""
        try:
            import sys
            sys.path.insert(0, str(AUTARCH_DIR))
            
            from causal_reasoning import CausalReasoningEngine
            self.causal_engine = CausalReasoningEngine()
            
            from nshe_bridge import get_bridge
            self.nshe_bridge = get_bridge()
        except Exception as e:
            print(f"[ANALYZER] Engine init error: {e}")
    
    def analyze(self, task: Dict) -> Dict:
        """Run full multi-stage analysis pipeline"""
        start_time = datetime.now()
        
        # Stage 1: Parse
        parsed = self.parse(task)
        
        # Stage 2: Classify
        classified = self.classify(parsed)
        
        # Stage 3: Context
        contextualized = self.add_context(classified)
        
        # Stage 4: Recommend
        recommendations = self.recommend(contextualized)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "task_type": task.get("type", "unknown"),
            "analysis": recommendations,
            "stages_completed": 4,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
    
    def parse(self, task: Dict) -> Dict:
        """Stage 1: Parse raw task data into structured format"""
        description = task.get("description", "")
        task_type = task.get("type", "unknown")
        
        parsed = {
            "raw_description": description,
            "task_type": task_type,
            "entities": {},
            "keywords": [],
            "severity_indicators": []
        }
        
        # Extract CVE ID
        cve_match = re.search(r'CVE-\d{4}-\d+', description)
        if cve_match:
            parsed["entities"]["cve_id"] = cve_match.group(0)
        
        # Extract TTP ID
        ttp_match = re.search(r'T\d{4}(?:\.\d{3})?', description)
        if ttp_match:
            parsed["entities"]["ttp_id"] = ttp_match.group(0)
        
        # Extract IP addresses
        ip_matches = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', description)
        if ip_matches:
            parsed["entities"]["ip_addresses"] = ip_matches
        
        # Extract threat actor names
        actor_patterns = [
            r'APT\d+', r'FIN\d+', r'TA\d+', r'Lazarus', r'Fancy Bear',
            r'Cozy Bear', r'Salt Typhoon', r'Sandworm', r'Equation Group',
            r'Kimsuky', r'MuddyWater', r'OilRig', r'Charming Kitten'
        ]
        actors = []
        for pattern in actor_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            actors.extend(matches)
        if actors:
            parsed["entities"]["threat_actors"] = list(set(actors))
        
        # Extract severity indicators
        severity_keywords = {
            "critical": ["critical", "cvss 9", "cvss 10", "rce", "remote code execution", "zero-day"],
            "high": ["high", "cvss 7", "cvss 8", "privilege escalation", "authentication bypass"],
            "medium": ["medium", "cvss 4", "cvss 5", "cvss 6", "xss", "information disclosure"],
            "low": ["low", "cvss 1", "cvss 2", "cvss 3", "minor"]
        }
        
        desc_lower = description.lower()
        for severity, keywords in severity_keywords.items():
            if any(kw in desc_lower for kw in keywords):
                parsed["severity_indicators"].append(severity)
        
        # Extract keywords
        words = re.findall(r'\b\w{4,}\b', description.lower())
        parsed["keywords"] = list(set(words))[:20]
        
        return parsed
    
    def classify(self, parsed: Dict) -> Dict:
        """Stage 2: Classify threat type using patterns + symbolic KB"""
        classification = {
            "parsed": parsed,
            "threat_category": "unknown",
            "attack_type": "unknown",
            "confidence": 0.0,
            "symbolic_matches": []
        }
        
        description = parsed.get("raw_description", "").lower()
        keywords = parsed.get("keywords", [])
        
        # Classification patterns
        categories = {
            "vulnerability_exploitation": {
                "patterns": ["cve", "vulnerability", "exploit", "patch", "flaw", "bug"],
                "attack_types": {
                    "rce": ["remote code execution", "rce", "code execution"],
                    "sqli": ["sql injection", "sqli"],
                    "xss": ["cross-site scripting", "xss"],
                    "auth_bypass": ["authentication bypass", "auth bypass", "unauthorized access"],
                    "privilege_escalation": ["privilege escalation", "elevation of privilege"],
                    "dos": ["denial of service", "dos", "ddos"],
                    "ssrf": ["server-side request forgery", "ssrf"],
                    "path_traversal": ["path traversal", "directory traversal"],
                    "file_inclusion": ["file inclusion", "lfi", "rfi"],
                    "deserialization": ["deserialization", "insecure deserialization"]
                }
            },
            "malware_activity": {
                "patterns": ["malware", "ransomware", "trojan", "backdoor", "botnet", "worm"],
                "attack_types": {}
            },
            "phishing_social_engineering": {
                "patterns": ["phishing", "spear phishing", "social engineering", "credential harvesting"],
                "attack_types": {}
            },
            "apt_campaign": {
                "patterns": ["apt", "nation-state", "espionage", "state-sponsored", "campaign"],
                "attack_types": {}
            },
            "supply_chain": {
                "patterns": ["supply chain", "dependency", "package", "npm", "pypi", "maven"],
                "attack_types": {}
            }
        }
        
        best_category = "unknown"
        best_score = 0
        
        for category, info in categories.items():
            score = sum(1 for p in info["patterns"] if p in description)
            if score > best_score:
                best_score = score
                best_category = category
        
        classification["threat_category"] = best_category
        classification["confidence"] = min(0.9, best_score * 0.2) if best_score > 0 else 0.3
        
        # Classify attack type
        if best_category == "vulnerability_exploitation":
            for attack_type, patterns in categories[best_category]["attack_types"].items():
                if any(p in description for p in patterns):
                    classification["attack_type"] = attack_type
                    break
        
        # Query symbolic KB
        if self.nshe_bridge:
            try:
                symbolic_result = self.nshe_bridge.symbolic_query(description[:200])
                classification["symbolic_matches"] = symbolic_result.get("results", [])
            except Exception:
                pass
        
        return classification
    
    def add_context(self, classified: Dict) -> Dict:
        """Stage 3: Add causal context + related intel"""
        context = {
            "classified": classified,
            "causal_context": {},
            "related_intel": [],
            "kill_chain_position": "unknown"
        }
        
        parsed = classified.get("parsed", {})
        ttp_id = parsed.get("entities", {}).get("ttp_id", "")
        
        # Add causal context
        if self.causal_engine and ttp_id:
            try:
                explanation = self.causal_engine.explain(ttp_id)
                context["causal_context"] = explanation
                context["kill_chain_position"] = explanation.get("stage", "unknown")
            except Exception:
                pass
        
        # Query vector DB for related intel
        if self.nshe_bridge:
            try:
                query = parsed.get("raw_description", "")[:200]
                related = self.nshe_bridge.query_vector_db(query, top_k=3)
                context["related_intel"] = related
            except Exception:
                pass
        
        return context
    
    def recommend(self, contextualized: Dict) -> Dict:
        """Stage 4: Generate defensive recommendations"""
        classified = contextualized.get("classified", {})
        category = classified.get("threat_category", "unknown")
        attack_type = classified.get("attack_type", "unknown")
        causal_context = contextualized.get("causal_context", {})
        
        # Recommendation templates by category
        recommendation_templates = {
            "vulnerability_exploitation": {
                "immediate": [
                    "Apply vendor patch if available",
                    "Implement WAF rules to block exploitation attempts",
                    "Monitor for indicators of compromise"
                ],
                "short_term": [
                    "Conduct vulnerability assessment of affected systems",
                    "Review access controls and network segmentation",
                    "Enable enhanced logging for affected components"
                ],
                "long_term": [
                    "Implement continuous vulnerability management program",
                    "Deploy intrusion detection/prevention systems",
                    "Establish patch management SLA"
                ]
            },
            "malware_activity": {
                "immediate": [
                    "Isolate affected systems from network",
                    "Run full antivirus/EDR scan",
                    "Block identified IOCs at firewall"
                ],
                "short_term": [
                    "Analyze malware sample for TTPs",
                    "Review endpoint detection rules",
                    "Scan for lateral movement indicators"
                ],
                "long_term": [
                    "Deploy EDR solution",
                    "Implement application whitelisting",
                    "Establish incident response playbook"
                ]
            },
            "phishing_social_engineering": {
                "immediate": [
                    "Block sender domain/IP",
                    "Reset credentials for targeted users",
                    "Alert all users about the campaign"
                ],
                "short_term": [
                    "Review email filtering rules",
                    "Enable multi-factor authentication",
                    "Conduct security awareness training"
                ],
                "long_term": [
                    "Implement DMARC/DKIM/SPF",
                    "Deploy advanced email security gateway",
                    "Regular phishing simulation exercises"
                ]
            },
            "apt_campaign": {
                "immediate": [
                    "Activate incident response team",
                    "Preserve forensic evidence",
                    "Block identified IOCs"
                ],
                "short_term": [
                    "Conduct threat hunting sweep",
                    "Review privileged account activity",
                    "Enhance network monitoring"
                ],
                "long_term": [
                    "Implement zero trust architecture",
                    "Deploy advanced threat detection",
                    "Establish threat intelligence sharing"
                ]
            },
            "supply_chain": {
                "immediate": [
                    "Remove affected package/version",
                    "Audit dependencies for compromise",
                    "Rotate credentials and keys"
                ],
                "short_term": [
                    "Review CI/CD pipeline security",
                    "Implement dependency scanning",
                    "Verify package integrity"
                ],
                "long_term": [
                    "Establish software bill of materials (SBOM)",
                    "Implement signed package verification",
                    "Continuous dependency monitoring"
                ]
            }
        }
        
        template = recommendation_templates.get(category, recommendation_templates["vulnerability_exploitation"])
        
        # Add causal-based recommendations
        causal_recommendations = []
        predicted_next = causal_context.get("predicted_next", [])
        if predicted_next:
            for prediction in predicted_next[:2]:
                stage = prediction.get("predicted_stage", "")
                causal_recommendations.append(
                    f"Prepare defenses for predicted next stage: {stage} "
                    f"(probability: {prediction.get('probability', 0):.0%})"
                )
        
        return {
            "category": category,
            "attack_type": attack_type,
            "confidence": classified.get("confidence", 0.5),
            "recommendations": {
                "immediate": template["immediate"],
                "short_term": template["short_term"],
                "long_term": template["long_term"],
                "causal_based": causal_recommendations
            },
            "kill_chain_position": contextualized.get("kill_chain_position", "unknown"),
            "symbolic_context": classified.get("symbolic_matches", []),
            "related_intel_count": len(contextualized.get("related_intel", []))
        }


if __name__ == "__main__":
    analyzer = EnhancedAnalyzer()
    
    # Test with sample task
    test_task = {
        "type": "learn_cve",
        "description": "Analyze CVE-2026-85880: Windows Advanced Local Procedure Call (ALPC) Remote Code Execution vulnerability with CVSS 9.8"
    }
    
    result = analyzer.analyze(test_task)
    print(f"Analysis result:")
    print(json.dumps(result, indent=2, default=str)[:2000])
