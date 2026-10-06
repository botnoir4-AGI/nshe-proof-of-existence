#!/usr/bin/env python3
"""
Test Spiderweb Bridge connection to Google Sheets
Run this to verify credentials and connection before starting AUTARCH
"""

import sys
from pathlib import Path

# Add autarch to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from spiderweb_bridge import get_spiderweb_bridge
    print("=" * 72)
    print("SPIDERWEB BRIDGE CONNECTION TEST")
    print("=" * 72)
    
    # Check if credentials exist
    creds_path = Path("credentials.json")
    if not creds_path.exists():
        print()
        print("ERROR: credentials.json not found!")
        print("  Please copy your Google Service Account JSON key to:")
        print(f"  {creds_path.absolute()}")
        print()
        print("  See credentials_template.json for format reference.")
        sys.exit(1)
    
    print(f"Found credentials: {creds_path}")
    
    # Initialize bridge
    print()
    print("[1/3] Initializing Spiderweb Bridge...")
    bridge = get_spiderweb_bridge()
    
    if not bridge.enabled:
        print("ERROR: Bridge initialization failed")
        print("  Check credentials.json format and permissions")
        sys.exit(1)
    
    print("SUCCESS: Bridge initialized successfully")
    
    # Test heartbeat push
    print()
    print("[2/3] Testing heartbeat push...")
    success = bridge.push_heartbeat(
        status="TEST_CONNECTION",
        payload="Spiderweb Bridge test successful"
    )
    
    if success:
        print("SUCCESS: Heartbeat pushed to Google Sheets")
    else:
        print("ERROR: Heartbeat push failed")
        print("  Check if Google Sheet 'Umbra_Vector_Store' exists and is shared")
        sys.exit(1)
    
    # Test fetch (optional)
    print()
    print("[3/3] Testing fetch (reading latest record)...")
    latest = bridge.fetch_latest_trigger()
    
    if latest:
        print(f"SUCCESS: Fetched latest record: {latest}")
    else:
        print("INFO: No records found (this is OK for first test)")
    
    print()
    print("=" * 72)
    print("SUCCESS: Spiderweb Bridge is working correctly!")
    print("=" * 72)
    print()
    print("Next steps:")
    print("  1. Open your Google Sheet 'Umbra_Vector_Store'")
    print("  2. Verify the test heartbeat row was added")
    print("  3. Restart AUTARCH: python orchestrator.py")
    print()
    print("The bridge will now push telemetry every Voyager cycle.")
    
except ImportError as e:
    print(f"ERROR: Import error: {e}")
    print("  Make sure gspread is installed: pip install gspread oauth2client")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)