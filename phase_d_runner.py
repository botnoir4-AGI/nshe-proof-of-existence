#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase D Runner
Generates public reports and dashboard for deterent visibility.
Called by orchestrator every 100 cycles.
"""

import json
from datetime import datetime


def run_phase_d(cycle_count: int) -> dict:
    """
    Run Phase D components:
    1. Generate weekly threat intel report (every 100 cycles)
    2. Update public dashboard (every 100 cycles)
    
    Args:
        cycle_count: Current orchestrator cycle count
    
    Returns:
        dict with results from all Phase D components
    """
    results = {
        "report": None,
        "dashboard": None,
        "timestamp": datetime.now().isoformat()
    }
    
    # Generate report every 100 cycles
    if cycle_count % 10 == 0:
        try:
            from report_generator import ReportGenerator
            
            generator = ReportGenerator()
            report_result = generator.generate_and_save()
            results["report"] = report_result
            
            print(f"[PHASE D] Report generated: {report_result.get('report_file', 'unknown')}")
        
        except ImportError as e:
            print(f"[PHASE D] Report generator import error: {e}")
        except Exception as e:
            print(f"[PHASE D] Report generator error: {e}")
    else:
        print(f"[PHASE D] Report generation skipped (cycle {cycle_count}, next at {((cycle_count // 10) + 1) * 10})")
    
    # Update dashboard every 100 cycles
    if cycle_count % 10 == 0:
        try:
            from public_dashboard import PublicDashboard
            
            dashboard = PublicDashboard()
            dashboard_result = dashboard.update_dashboard()
            results["dashboard"] = dashboard_result
            
            print(f"[PHASE D] Dashboard updated: {dashboard_result.get('html_file', 'unknown')}")
        
        except ImportError as e:
            print(f"[PHASE D] Dashboard import error: {e}")
        except Exception as e:
            print(f"[PHASE D] Dashboard error: {e}")
    else:
        print(f"[PHASE D] Dashboard update skipped (cycle {cycle_count})")
    
    return results


if __name__ == "__main__":
    # Self-test
    print("Phase D Runner Self-Test")
    print("=" * 50)
    
    # Test with cycle 100 (should generate both)
    print("\nTesting cycle 100 (should generate report + dashboard)...")
    results = run_phase_d(100)
    print(f"\nResults: {json.dumps(results, indent=2, default=str)[:1000]}")
    
    # Test with cycle 50 (should skip both)
    print("\n\nTesting cycle 50 (should skip both)...")
    results = run_phase_d(50)
    print(f"\nResults: {json.dumps(results, indent=2, default=str)[:500]}")
