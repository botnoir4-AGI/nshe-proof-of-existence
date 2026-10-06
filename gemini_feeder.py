#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH Gemini Feeder
Uses Gemini (port 8001) as primary intelligence source.
Real-time world knowledge, zero RSS overhead.
"""

import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict

THREAT_INTEL_DIR = Path(r"C:\UMBRA_CORE\umbra-sovereign\threat_intel")
FEEDER_LOG = THREAT_INTEL_DIR / "gemini_feeder_log.jsonl"
FP_FILE = THREAT_INTEL_DIR / "executed_fingerprints.json"


def fingerprint(task):
    key = "{}|{}".format(task.get("type", ""), task.get("description", "")).lower().strip()
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


class GeminiFeeder:
    """
    Primary threat intelligence source via Gemini (port 8001).
    Replaces heavy RSS scanners with real-time LLM queries.
    """
    
    def __init__(self):
        self.executed_fps = self._load_fingerprints()
    
    def _load_fingerprints(self):
        if FP_FILE.exists():
            try:
                return set(json.loads(FP_FILE.read_text(encoding="utf-8")))
            except Exception:
                pass
        return set()
    
    def build_intel_prompt(self, focus_area="comprehensive"):
        """Build structured prompt for threat intelligence gathering"""
        
        prompts = {
            "comprehensive": """You are a sovereign threat intelligence analyst.

Provide a structured report on the MOST CRITICAL cybersecurity developments in the last 24-48 hours:

1. **CRITICAL CVEs** (top 3-5):
   - CVE ID
   - Affected system/component
   - Severity (Critical/High)
   - Brief description of vulnerability
   - Why it matters

2. **EMERGING ATTACK PATTERNS** (top 2-3):
   - Attack technique name/description
   - Observed in the wild or theoretical
   - MITRE ATT&CK mapping if applicable
   - Detection indicators

3. **ACTIVE THREAT CAMPAIGNS** (top 2-3):
   - Threat actor (named if known, or attributed type)
   - Target sectors/regions
   - Primary techniques used
   - Timeline/activity window

4. **SUPPLY CHAIN / NOVEL THREATS** (1-2):
   - New classes of attacks
   - Zero-days or novel exploits
   - Unusual threat actor behavior

Format your response as valid JSON with this exact structure:
{
  "timestamp": "ISO-8601 timestamp",
  "critical_cves": [
    {
      "cve_id": "CVE-YYYY-XXXXX",
      "system": "string",
      "severity": "Critical|High",
      "description": "string",
      "significance": "string"
    }
  ],
  "emerging_attacks": [
    {
      "name": "string",
      "description": "string",
      "mitre_id": "T1234 or null",
      "indicators": "string"
    }
  ],
  "active_campaigns": [
    {
      "actor": "string",
      "targets": "string",
      "techniques": "string",
      "timeline": "string"
    }
  ],
  "novel_threats": [
    {
      "category": "string",
      "description": "string",
      "urgency": "string"
    }
  ],
  "strategic_insights": "string (1-2 sentences on overall threat landscape)"
}

Be SPECIFIC with CVE IDs, ACTOR NAMES, and TECHNICAL DETAILS.
Focus on what's actionable for defensive intelligence.
Reply ONLY with the JSON, no markdown or explanation.""",

            "cve_focus": """Provide TOP 5 CRITICAL CVEs from last 7 days in JSON format:

{
  "timestamp": "ISO-8601",
  "cves": [
    {
      "cve_id": "CVE-YYYY-XXXXX",
      "cvss": 9.5,
      "software": "component name",
      "vuln_class": "RCE|SQLi|XSS|auth bypass",
      "exploit_status": "public_poc|in_the_wild|theoretical",
      "impact": "brief impact summary",
      "mitigation": "patch status"
    }
  ],
  "summary": "1-2 sentence analysis"
}

Focus on most critical only (CVSS 9.0+). Reply ONLY with JSON.""",

            "campaign_focus": """Provide TOP 3 ACTIVE THREAT CAMPAIGNS (last 30 days) in JSON:

{
  "timestamp": "ISO-8601",
  "campaigns": [
    {
      "actor": "group name",
      "targets": "sector/region",
      "techniques": ["T1234"],
      "status": "active"
    }
  ],
  "trends": "1-2 sentence trends"
}

Focus on most active campaigns only. Reply ONLY with JSON."""
        }
        
        return prompts.get(focus_area, prompts["comprehensive"])
    
    def query_gemini(self, prompt):
        """Query Gemini via Ollama executor (port 8001)"""
        # Import here to avoid circular imports
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from ollama_executor import OllamaExecutor
        
        try:
            executor = OllamaExecutor()
            # Use execute_single method if available, otherwise construct task
            task = {
                "type": "threat_intel_query",
                "description": prompt,
                "priority": "high"
            }
            results = executor.execute_batch([task], 1)
            if results and results[0].get("success"):
                return results[0].get("content", "")
            else:
                print(f"[GEMINI FEEDER] Query failed: {results[0].get('error', 'unknown')}")
                return None
        except Exception as e:
            print(f"[GEMINI FEEDER] Exception: {e}")
            return None
    
    def parse_response(self, response):
        """Parse Gemini response into structured data (robust, handles truncation)"""
        if not response:
            return None
        
        # Try to find JSON in response
        # Remove markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to extract JSON directly
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
            json_str = self._clean_json(json_str)
          #  else:
           #     print("[GEMINI FEEDER] No JSON found in response")
           #     return None
        
        # Try to parse JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"[GEMINI FEEDER] JSON parse error: {e}")
            
            # RECOVERY ATTEMPT: Try to fix common truncation issues
            print("[GEMINI FEEDER] Attempting JSON recovery...")
            
            # Strategy 1: Close unclosed arrays/objects
            recovered = self._try_recover_json(json_str)
            if recovered:
                print("[GEMINI FEEDER] JSON recovered successfully")
                return recovered
            
            # Strategy 2: Extract partial valid JSON (best effort)
            partial = self._extract_partial_json(json_str)
            if partial:
                print(f"[GEMINI FEEDER] Partial JSON extracted: {len(partial)} items")
                return partial
            
            print("[GEMINI FEEDER] JSON recovery failed")
            return None
    
    def _clean_json(self, json_str):
        "Aggressive pre-processing to fix common LLM JSON errors (no regex)"
        if not json_str:
            return json_str
        
        # Strip markdown code blocks
        json_str = json_str.replace("```json", "").replace("```JSON", "").replace("```", "")
        json_str = json_str.strip()
        
        # Remove trailing commas before } or ]
        while ",]" in json_str:
            json_str = json_str.replace(",]", "]")
        while ",}" in json_str:
            json_str = json_str.replace(",}", "}")
        while ", ]" in json_str:
            json_str = json_str.replace(", ]", "]")
        while ", }" in json_str:
            json_str = json_str.replace(", }", "}")
        
        # Fix invalid escape sequences
        try:
            json.loads(json_str, strict=False)
        except json.JSONDecodeError:
            result = []
            i = 0
            valid_escapes = set('"/\\bfnrtu')
            while i < len(json_str):
                if json_str[i] == '\\' and i + 1 < len(json_str):
                    next_char = json_str[i + 1]
                    if next_char in valid_escapes:
                        result.append(json_str[i:i+2])
                        i += 2
                        continue
                    else:
                        result.append('\\\\')
                        i += 1
                        continue
                result.append(json_str[i])
                i += 1
            json_str = ''.join(result)
        
        return json_str
    
    def _try_recover_json(self, json_str):
        """Try to recover truncated JSON by closing open structures"""
        json_str = self._clean_json(json_str)
        # Count open/close brackets
        open_braces = json_str.count('{') - json_str.count('}')
        open_brackets = json_str.count('[') - json_str.count(']')
        
        # Try to close them
        suffix = ''
        for _ in range(open_brackets):
            suffix += ']'
        for _ in range(open_braces):
            suffix += '}'
        
        recovered_str = json_str + suffix
        
        try:
            return json.loads(recovered_str)
        except json.JSONDecodeError:
            return None
    
    def _extract_partial_json(self, json_str):
        """Extract partial valid JSON objects/arrays"""
        # Try to extract individual items from arrays
        items = []
        
        # Look for array items like {"cve_id": ...}
        pattern = r'\{[^{}]*"cve_id"[^{}]*\}'
        matches = re.findall(pattern, json_str, re.DOTALL)
        
        for match in matches:
            try:
                item = json.loads(match)
                items.append(item)
            except json.JSONDecodeError:
                continue
        
        if items:
            # Return as structured dict
            return {
                "cves": items,
                "timestamp": datetime.now().isoformat(),
                "partial_recovery": True
            }
        
        return None
    
    def generate_tasks(self, intel_data, focus_area="comprehensive"):
        """Generate curriculum tasks from structured intel"""
        tasks = []
        timestamp = datetime.now().isoformat()
        
        if not intel_data:
            return tasks
        
        # Process CVEs
        for cve in intel_data.get("critical_cves", []) or intel_data.get("cves", []):
            cve_id = cve.get("cve_id", "")
            if not cve_id:
                continue
            
            task = {
                "type": "learn_cve",
                "priority": "high",
                "description": f"Deep analysis: {cve_id} - {cve.get('system', 'Unknown')}: {cve.get('description', '')[:150]}",
                "cve_id": cve_id,
                "severity": cve.get("severity") or cve.get("cvss"),
                "source": "gemini_feeder",
                "timestamp": timestamp
            }
            
            fp = fingerprint(task)
            if fp not in self.executed_fps:
                tasks.append(task)
        
        # Process emerging attacks
        for attack in intel_data.get("emerging_attacks", []):
            task = {
                "type": "learn_ttp",
                "priority": "high",
                "description": f"Emerging attack: {attack.get('name', 'Unknown')} - {attack.get('description', '')[:120]}",
                "ttp": attack.get("mitre_id"),
                "source": "gemini_feeder",
                "timestamp": timestamp
            }
            fp = fingerprint(task)
            if fp not in self.executed_fps:
                tasks.append(task)
        
        # Process active campaigns
        for campaign in intel_data.get("active_campaigns", []) or intel_data.get("campaigns", []):
            task = {
                "type": "learn_attribution",
                "priority": "high",
                "description": f"Campaign analysis: {campaign.get('actor', 'Unknown')} targeting {campaign.get('targets', 'unknown')} - {campaign.get('techniques', '')[:100]}",
                "actor": campaign.get("actor"),
                "source": "gemini_feeder",
                "timestamp": timestamp
            }
            fp = fingerprint(task)
            if fp not in self.executed_fps:
                tasks.append(task)
        
        # Process novel threats
        for threat in intel_data.get("novel_threats", []):
            task = {
                "type": "learn_threat_intel",
                "priority": "high",
                "description": f"Novel threat: {threat.get('category', 'Unknown')} - {threat.get('description', '')[:120]}",
                "source": "gemini_feeder",
                "timestamp": timestamp
            }
            fp = fingerprint(task)
            if fp not in self.executed_fps:
                tasks.append(task)
        
        return tasks
    
    def run_feed_cycle(self, focus_area="comprehensive"):
        """Run full intelligence gathering cycle via Gemini"""
        print(f"[GEMINI FEEDER] Starting intelligence cycle (focus: {focus_area})...")
        start_time = datetime.now()
        
        # Query Gemini
        prompt = self.build_intel_prompt(focus_area)
        response = self.query_gemini(prompt)
        
        if not response:
            return {
                "success": False,
                "error": "Gemini query failed",
                "tasks_generated": 0
            }
        
        # Parse response
        intel_data = self.parse_response(response)
        
        if not intel_data:
            return {
                "success": False,
                "error": "Response parse failed",
                "raw_response": response[:500],
                "tasks_generated": 0
            }
        
        # Generate tasks
        tasks = self.generate_tasks(intel_data, focus_area)
        
        # Log
        log_entry = {
            "timestamp": start_time.isoformat(),
            "focus_area": focus_area,
            "response_length": len(response),
            "tasks_generated": len(tasks),
            "cves": len(intel_data.get("critical_cves", []) or intel_data.get("cves", [])),
            "attacks": len(intel_data.get("emerging_attacks", [])),
            "campaigns": len(intel_data.get("active_campaigns", []) or intel_data.get("campaigns", [])),
            "novel_threats": len(intel_data.get("novel_threats", [])),
            "strategic_insights": intel_data.get("strategic_insights", intel_data.get("summary", intel_data.get("trends", "")))[:200],
            "duration": (datetime.now() - start_time).total_seconds()
        }
        
        try:
            with open(FEEDER_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception:
            pass
        
        print(f"[GEMINI FEEDER] Cycle complete: {len(tasks)} tasks generated in {log_entry['duration']:.1f}s")
        
        return {
            "success": True,
            "tasks": tasks,
            "intel_data": intel_data,
            "duration": log_entry["duration"]
        }


if __name__ == "__main__":
    feeder = GeminiFeeder()
    result = feeder.run_feed_cycle("comprehensive")
    print(f"\nResult: {json.dumps(result, indent=2, default=str)[:2000]}")
