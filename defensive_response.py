#!/usr/bin/env python3
"""
Defensive Response Module
Blocks malicious IPs that attack the honeypot.
This is DEFENSIVE only - no counter-attacks.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set

RESPONSE_DB = Path(__file__).parent.parent / "threat_intel" / "response_db.json"

class DefensiveResponse:
    """Block malicious IPs at the firewall (defensive only)"""
    
    def __init__(self):
        self.blocked_ips = self._load_blocked_ips()
    
    def _load_blocked_ips(self) -> Set[str]:
        """Load previously blocked IPs"""
        if RESPONSE_DB.exists():
            try:
                data = json.loads(RESPONSE_DB.read_text(encoding="utf-8"))
                return set(data.get("blocked_ips", []))
            except:
                pass
        return set()
    
    def _save_blocked_ips(self):
        """Save blocked IPs to database"""
        data = {
            "blocked_ips": sorted(list(self.blocked_ips)),
            "last_updated": datetime.now().isoformat(),
            "total_blocked": len(self.blocked_ips)
        }
        RESPONSE_DB.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    def extract_malicious_ips(self, events: List[Dict]) -> Set[str]:
        """Extract IPs that performed malicious actions"""
        malicious_ips = set()
        
        for event in events:
            ip = event.get("source_ip", "")
            event_type = event.get("event_type", "")
            
            # Check for malicious patterns
            if not ip or ip.startswith("127.") or ip.startswith("192.168."):
                continue
            
            # Brute force, command execution, path traversal = malicious
            if event_type in ["ssh_brute_force", "command_execution", "ssh_login_attempt"]:
                malicious_ips.add(ip)
            
            # Check payload for attack patterns
            payload = event.get("payload", "").lower()
            attack_patterns = [
                "etc/passwd", "etc/shadow", "whoami", "cat /etc",
                "or 1=1", "union select", "<script>", "shell.php",
                "cmd=", "exec(", "system(", "eval("
            ]
            
            if any(pattern in payload for pattern in attack_patterns):
                malicious_ips.add(ip)
        
        return malicious_ips
    
    def block_ips_windows(self, ips: Set[str]) -> int:
        """Block IPs using Windows Firewall (defensive only)"""
        blocked_count = 0
        
        for ip in ips:
            if ip in self.blocked_ips:
                continue
            
            try:
                # Add Windows Firewall rule to block inbound from this IP
                rule_name = f"Block_Malicious_{ip.replace('.', '_')}"
                
                result = subprocess.run(
                    [
                        "netsh", "advfirewall", "firewall", "add", "rule",
                        f"name={rule_name}",
                        "dir=in",
                        "action=block",
                        f"remoteip={ip}"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self.blocked_ips.add(ip)
                    blocked_count += 1
                    print(f"  ✓ Blocked: {ip}")
                else:
                    print(f"  ⚠ Failed to block {ip}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                print(f"  ⚠ Timeout blocking {ip}")
            except Exception as e:
                print(f"  ⚠ Error blocking {ip}: {e}")
        
        if blocked_count > 0:
            self._save_blocked_ips()
        
        return blocked_count
    
    def run_defensive_cycle(self, events: List[Dict]) -> Dict:
        """Run defensive response cycle"""
        print("[DEFENSE] Starting defensive response cycle...")
        
        # Extract malicious IPs
        malicious_ips = self.extract_malicious_ips(events)
        
        if not malicious_ips:
            print("[DEFENSE] No malicious IPs detected")
            return {
                "success": True,
                "malicious_ips": 0,
                "blocked_ips": 0,
                "total_blocked": len(self.blocked_ips)
            }
        
        print(f"[DEFENSE] Detected {len(malicious_ips)} malicious IPs")
        
        # Block them (defensive only)
        new_blocked = self.block_ips_windows(malicious_ips)
        
        print(f"[DEFENSE] Blocked {new_blocked} new IPs")
        print(f"[DEFENSE] Total blocked: {len(self.blocked_ips)} IPs")
        
        return {
            "success": True,
            "malicious_ips": len(malicious_ips),
            "blocked_ips": new_blocked,
            "total_blocked": len(self.blocked_ips)
        }


if __name__ == "__main__":
    # Test with sample events
    test_events = [
        {
            "source_ip": "1.2.3.4",
            "event_type": "ssh_brute_force",
            "payload": "Failed password for root"
        },
        {
            "source_ip": "5.6.7.8",
            "event_type": "command_execution",
            "payload": "cat /etc/passwd"
        }
    ]
    
    defense = DefensiveResponse()
    result = defense.run_defensive_cycle(test_events)
    print(f"\nResult: {json.dumps(result, indent=2)}")
