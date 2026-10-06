#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Public Dashboard
Sanitized system statistics for public viewing.
Establishes transparency and credibility.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

REPO = Path(r"C:\UMBRA_CORE\umbra-sovereign")
AUTARCH_DIR = Path(r"C:\UMBRA_CORE\autarch")
DASHBOARD_FILE = REPO / "public" / "dashboard.json"
DASHBOARD_HTML = REPO / "public" / "index.html"

# Ensure directories exist
DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)


class PublicDashboard:
    """
    Generates sanitized public dashboard data.
    No sensitive information exposed.
    """
    
    def __init__(self):
        self.curriculum = self._load_json(REPO / "threat_intel" / "curriculum.json")
        self.attacker_db = self._load_json(REPO / "threat_intel" / "attacker_db.json")
        self.response_db = self._load_json(REPO / "threat_intel" / "response_db.json")
        self.campaign_db = self._load_json(REPO / "threat_intel" / "campaign_db.json")
        self.skill_metrics = self._load_json(AUTARCH_DIR / "skill_metrics.json")
    
    def _load_json(self, path: Path) -> Dict:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}
    
    def generate_dashboard_data(self) -> Dict:
        """Generate sanitized dashboard data"""
        # Handle both formats: nested {"attackers": {...}} or flat {...}
        attackers = self.attacker_db.get("attackers", {})
        if not attackers and self.attacker_db:
            # Top-level format: dict of IP -> data
            attackers = {k: v for k, v in self.attacker_db.items() if isinstance(v, dict)}
        responses = self.response_db.get("responses", [])
        blocked_ips = self.response_db.get("blocked_ips", [])
        campaigns = self.campaign_db.get("campaigns", [])
        skills = self.skill_metrics.get("skills", {})
        completed_tasks = self.curriculum.get("completed_tasks", [])
        
        # Calculate metrics
        total_attackers = len(attackers)
        high_threats = len([ip for ip, data in attackers.items() if data.get("threat_level") == "high"])
        medium_threats = len([ip for ip, data in attackers.items() if data.get("threat_level") == "medium"])
        
        total_responses = len(responses)
        blocked_count = len(blocked_ips)
        
        campaigns_detected = len(campaigns)
        
        skills_count = len(skills)
        total_skill_executions = sum(s.get("executions", 0) for s in skills.values())
        
        tasks_completed = len(completed_tasks)
        
        # Recent activity (last 24 hours)
        now = datetime.now()
        yesterday = now - timedelta(hours=24)
        
        recent_attackers = len([
            ip for ip, data in attackers.items()
            if data.get("last_seen", "") > yesterday.isoformat()
        ])
        
        recent_responses = len([
            r for r in responses
            if r.get("executed_at", "") > yesterday.isoformat()
        ])
        
        # Generate dashboard
        dashboard = {
            "timestamp": now.isoformat(),
            "system_status": "operational",
            "uptime_hours": 24,  # Placeholder, would track actual uptime
            
            "threat_intelligence": {
                "total_attackers_profiled": total_attackers,
                "active_threats_24h": recent_attackers,
                "high_threat_actors": high_threats,
                "medium_threat_actors": medium_threats,
                "campaigns_detected": campaigns_detected
            },
            
            "defensive_operations": {
                "total_responses": total_responses,
                "responses_24h": recent_responses,
                "ips_blocked": blocked_count,
                "defense_rules_active": len(self.response_db.get("defense_rules", []))
            },
            
            "autonomous_learning": {
                "skills_generated": skills_count,
                "total_skill_executions": total_skill_executions,
                "tasks_completed": tasks_completed,
                "cognitive_coherence": "stable"
            },
            
            "infrastructure": {
                "nodes": 4,
                "coordination": "git-based stigmergy",
                "cognitive_layer": "NSHE (Neuro-Symbolic Homodynamic Engine)",
                "reasoning": "Causal + symbolic"
            },
            
            "last_updated": now.isoformat()
        }
        
        return dashboard
    
    def generate_html_dashboard(self, dashboard_data: Dict) -> str:
        """Generate HTML dashboard"""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AUTARCH — Public Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #00ff88;
            border-bottom: 2px solid #00ff88;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #00cc66;
            margin-top: 30px;
        }}
        .status {{
            background: #1a1a1a;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #00ff88;
            margin-bottom: 20px;
        }}
        .metric {{
            background: #1a1a1a;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #00ff88;
        }}
        .metric-label {{
            color: #888;
            font-size: 0.9em;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #333;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ AUTARCH — Autonomous Threat Intelligence System</h1>
        
        <div class="status">
            <strong>System Status:</strong> {dashboard_data['system_status'].upper()}<br>
            <strong>Uptime:</strong> {dashboard_data['uptime_hours']} hours<br>
            <strong>Last Updated:</strong> {dashboard_data['timestamp']}
        </div>
        
        <h2>Threat Intelligence</h2>
        <div class="grid">
            <div class="metric">
                <div class="metric-value">{dashboard_data['threat_intelligence']['total_attackers_profiled']}</div>
                <div class="metric-label">Total Attackers Profiled</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dashboard_data['threat_intelligence']['active_threats_24h']}</div>
                <div class="metric-label">Active Threats (24h)</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dashboard_data['threat_intelligence']['high_threat_actors']}</div>
                <div class="metric-label">High-Threat Actors</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dashboard_data['threat_intelligence']['campaigns_detected']}</div>
                <div class="metric-label">Campaigns Detected</div>
            </div>
        </div>
        
        <h2>Defensive Operations</h2>
        <div class="grid">
            <div class="metric">
                <div class="metric-value">{dashboard_data['defensive_operations']['total_responses']}</div>
                <div class="metric-label">Total Responses</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dashboard_data['defensive_operations']['responses_24h']}</div>
                <div class="metric-label">Responses (24h)</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dashboard_data['defensive_operations']['ips_blocked']}</div>
                <div class="metric-label">IPs Blocked</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dashboard_data['defensive_operations']['defense_rules_active']}</div>
                <div class="metric-label">Defense Rules Active</div>
            </div>
        </div>
        
        <h2>Autonomous Learning</h2>
        <div class="grid">
            <div class="metric">
                <div class="metric-value">{dashboard_data['autonomous_learning']['skills_generated']}</div>
                <div class="metric-label">Skills Generated</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dashboard_data['autonomous_learning']['total_skill_executions']}</div>
                <div class="metric-label">Total Skill Executions</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dashboard_data['autonomous_learning']['tasks_completed']}</div>
                <div class="metric-label">Tasks Completed</div>
            </div>
            <div class="metric">
                <div class="metric-value">{dashboard_data['autonomous_learning']['cognitive_coherence'].upper()}</div>
                <div class="metric-label">Cognitive Coherence</div>
            </div>
        </div>
        
        <h2>Infrastructure</h2>
        <div class="metric">
            <p><strong>Nodes:</strong> {dashboard_data['infrastructure']['nodes']}</p>
            <p><strong>Coordination:</strong> {dashboard_data['infrastructure']['coordination']}</p>
            <p><strong>Cognitive Layer:</strong> {dashboard_data['infrastructure']['cognitive_layer']}</p>
            <p><strong>Reasoning:</strong> {dashboard_data['infrastructure']['reasoning']}</p>
        </div>
        
        <div class="footer">
            <p><strong>About AUTARCH:</strong> An autonomous threat intelligence and defensive response system. Operates continuously, learns from observed threats, generates detection capabilities, and executes defensive responses in real-time.</p>
            <p><strong>Architecture:</strong> Neuro-symbolic cognitive layer + causal reasoning + swarm coordination</p>
            <p><strong>Philosophy:</strong> Sovereign digital defense through autonomous intelligence</p>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def save_dashboard(self, dashboard_data: Dict) -> None:
        """Save dashboard data to JSON and HTML"""
        # Save JSON
        DASHBOARD_FILE.write_text(json.dumps(dashboard_data, indent=2), encoding="utf-8")
        
        # Save HTML
        html_content = self.generate_html_dashboard(dashboard_data)
        DASHBOARD_HTML.write_text(html_content, encoding="utf-8")
    
    def update_dashboard(self) -> Dict:
        """Generate and save dashboard"""
        print("[DASHBOARD] Generating public dashboard...")
        start_time = datetime.now()
        
        dashboard_data = self.generate_dashboard_data()
        self.save_dashboard(dashboard_data)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print(f"[DASHBOARD] Dashboard updated ({duration:.1f}s)")
        
        return {
            "success": True,
            "dashboard_file": str(DASHBOARD_FILE),
            "html_file": str(DASHBOARD_HTML),
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    dashboard = PublicDashboard()
    result = dashboard.update_dashboard()
    print(f"\nResult: {json.dumps(result, indent=2)}")
