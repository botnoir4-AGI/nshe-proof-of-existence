# ============================================================
# SPIDERWEB MESH INTEGRATION (Google Sheets Vector Store)
# ============================================================

class SpiderwebBridge:
    """
    Spiderweb Mesh Integration for Google Sheets Vector Store
    Provides command bridge and telemetry persistence layer
    """
    
    def __init__(self, json_key_path="credentials.json", sheet_name="Umbra_Vector_Store"):
        """
        Initialize Spiderweb Bridge connection to Google Sheets
        
        Args:
            json_key_path: Path to Google Service Account credentials
            sheet_name: Name of the target spreadsheet
        """
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
            from datetime import datetime
            import time
            
            self.gspread = gspread
            self.ServiceAccountCredentials = ServiceAccountCredentials
            self.datetime = datetime
            self.time = time
            
            self.scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            self.json_key_path = json_key_path
            self.sheet_name = sheet_name
            self.enabled = True
            
            # Initialize connection
            self._connect()
            
        except ImportError as e:
            print(f"[SPIDERWEB] Warning: Libraries not installed: {e}")
            print("[SPIDERWEB] Install with: pip install gspread oauth2client")
            self.enabled = False
        except Exception as e:
            print(f"[SPIDERWEB] Warning: Initialization failed: {e}")
            self.enabled = False
    
    def _connect(self):
        """Establish connection to Google Sheets"""
        try:
            from pathlib import Path
            
            key_path = Path(self.json_key_path)
            if not key_path.exists():
                print(f"[SPIDERWEB] Warning: Credentials not found: {self.json_key_path}")
                self.enabled = False
                return
            
            self.creds = self.ServiceAccountCredentials.from_json_keyfile_name(
                self.json_key_path, 
                self.scope
            )
            self.client = self.gspread.authorize(self.creds)
            self.sheet = self.client.open(self.sheet_name).sheet1
            print(f"[SPIDERWEB] Connected to {self.sheet_name}")
            
        except Exception as e:
            print(f"[SPIDERWEB] Warning: Connection failed: {e}")
            self.enabled = False
    
    def push_heartbeat(self, status="NOMINAL", payload=""):
        """
        Push heartbeat telemetry to Google Sheets
        
        Args:
            status: Node status (NOMINAL, ERROR, ANOMALY_DETECTED)
            payload: Additional telemetry data
        """
        if not self.enabled:
            return False
        
        try:
            ts = self.datetime.utcnow().isoformat()
            row = [
                ts,
                "NODE_NUC_EDGE",
                "EDGE_PULSE",
                status,
                payload,
                "AUTARCH_VSM4"
            ]
            self.sheet.append_row(row)
            print(f"[SPIDERWEB] Heartbeat pushed: {status}")
            return True
            
        except Exception as e:
            print(f"[SPIDERWEB] Warning: Heartbeat push failed: {e}")
            # Failover: log to local file
            self._failover_log(f"Heartbeat: {status} - {payload}")
            return False
    
    def fetch_latest_trigger(self):
        """
        Fetch latest command/trigger from Google Sheets
        
        Returns:
            dict: Latest event record or None
        """
        if not self.enabled:
            return None
        
        try:
            records = self.sheet.get_all_records()
            if records:
                latest = records[-1]
                
                # Check for actionable events
                event_type = latest.get("Event_Type", "")
                status = latest.get("Status", "")
                
                if event_type in ["ANOMALY_DETECTED", "COMMAND"] or status == "PENDING_EXECUTION":
                    print(f"[SPIDERWEB] Trigger detected: {event_type}")
                    return latest
                
            return None
            
        except Exception as e:
            print(f"[SPIDERWEB] Warning: Fetch failed: {e}")
            return None
    
    def push_skill_promotion(self, skill_name, skill_hash, task_type):
        """
        Log skill promotion events to Sheets
        
        Args:
            skill_name: Name of promoted skill
            skill_hash: Hash of skill code
            task_type: Type of task that generated skill
        """
        if not self.enabled:
            return False
        
        try:
            ts = self.datetime.utcnow().isoformat()
            row = [
                ts,
                "NODE_NUC_EDGE",
                "SKILL_PROMOTED",
                "NOMINAL",
                f"Skill: {skill_name} ({skill_hash[:8]})",
                task_type
            ]
            self.sheet.append_row(row)
            return True
            
        except Exception as e:
            print(f"[SPIDERWEB] Warning: Skill promotion log failed: {e}")
            return False
    
    def _failover_log(self, message):
        """Log to local file when Sheets connection fails"""
        try:
            from pathlib import Path
            from datetime import datetime
            
            log_file = Path(__file__).parent / "spiderweb_failover.log"
            ts = datetime.utcnow().isoformat()
            
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {message}\n")
                
        except Exception as e:
            print(f"[SPIDERWEB] Warning: Failover log failed: {e}")


# Global bridge instance
_spiderweb_bridge = None

def get_spiderweb_bridge():
    """Get or create SpiderwebBridge singleton"""
    global _spiderweb_bridge
    if _spiderweb_bridge is None:
        _spiderweb_bridge = SpiderwebBridge()
    return _spiderweb_bridge