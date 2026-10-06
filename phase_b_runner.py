#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase B Runner: Standalone execution of all Phase B components.
Called by orchestrator after SYS4 intelligence cycle.
"""

import json
from datetime import datetime
from pathlib import Path


def run_phase_b(intel_layer):
    """
    Run all Phase B components:
    1. Honeypot Pipeline (Black Vault → TTP extraction)
    2. Threat Correlation (CVE + TTP + actor = campaigns)
    3. Enhanced Analysis (causal reasoning + recommendations)
    
    Args:
        intel_layer: IntelligenceLayer instance (for curriculum access)
    
    Returns:
        dict with results from all Phase B components
    """
    results = {
        "honeypot": None,
        "correlation": None,
        "enhanced_analysis": None,
        "timestamp": datetime.now().isoformat()
    }
    
    # ---- PHASE B.1: HONEYPOT PIPELINE ----
    try:
        from honeypot_pipeline import HoneypotPipeline
        
        honeypot = HoneypotPipeline()
        hp_result = honeypot.run_pipeline()
        results["honeypot"] = hp_result
        
        if hp_result.get("success"):
            hp_tasks = hp_result.get("tasks", [])
            
            if hp_tasks and intel_layer is not None:
                # Add honeypot tasks to curriculum
                try:
                    from intelligence_layer import fingerprint
                    
                    existing_fps = {fingerprint(t) for t in intel_layer.curriculum.get("proposed_tasks", [])}
                    executed_fps = intel_layer.executed_fps if hasattr(intel_layer, 'executed_fps') else set()
                    
                    new_hp_tasks = [t for t in hp_tasks 
                                   if fingerprint(t) not in existing_fps 
                                   and fingerprint(t) not in executed_fps]
                    
                    if new_hp_tasks:
                        intel_layer.curriculum.setdefault("proposed_tasks", []).extend(new_hp_tasks)
                        intel_layer.save_curriculum()
                        print(f"[HONEYPOT] Added {len(new_hp_tasks)} honeypot tasks to curriculum")
                    else:
                        print(f"[HONEYPOT] {len(hp_tasks)} tasks generated (all duplicates)")
                except Exception as e:
                    print(f"[HONEYPOT] Curriculum update error: {e}")
            
            tasks_gen = hp_result.get("tasks_generated", 0)
            events = hp_result.get("events_processed", 0)
            ttps = hp_result.get("ttps_extracted", 0)
            print(f"[PHASE B] Honeypot: {events} events → {ttps} TTPs → {tasks_gen} tasks")
        else:
            print(f"[HONEYPOT] Pipeline: {hp_result.get('message', 'no events')}")
    
    except ImportError as e:
        print(f"[PHASE B] Honeypot import error: {e}")
    except Exception as e:
        print(f"[PHASE B] Honeypot error: {e}")
    
    # ---- PHASE B.2: THREAT CORRELATION ----
    try:
        from threat_correlation import ThreatCorrelationEngine
        
        correlator = ThreatCorrelationEngine()
        
        # Feed curriculum tasks as entities for correlation
        if intel_layer is not None:
            for task in intel_layer.curriculum.get("proposed_tasks", [])[-15:]:
                task_type = task.get("type", "unknown")
                entity_type = "cve" if task_type == "learn_cve" else "ttp"
                correlator.add_entity(entity_type, task)
        
        corr_result = correlator.run_correlation_cycle()
        results["correlation"] = corr_result
        
        campaigns = corr_result.get("campaigns_detected", 0)
        if campaigns > 0:
            print(f"[PHASE B] Correlation: {campaigns} campaign(s) DETECTED")
        else:
            temporal = corr_result.get("temporal_correlations", 0)
            infra = corr_result.get("infrastructure_correlations", 0)
            behavioral = corr_result.get("behavioral_correlations", 0)
            print(f"[PHASE B] Correlation: {temporal} temporal, {infra} infra, {behavioral} behavioral")
    
    except ImportError as e:
        print(f"[PHASE B] Correlation import error: {e}")
    except Exception as e:
        print(f"[PHASE B] Correlation error: {e}")
    
    # ---- PHASE B.3: CAUSAL REASONING (on recent TTPs) ----
    try:
        from causal_reasoning import CausalReasoningEngine
        
        causal = CausalReasoningEngine()
        
        # Get recent TTPs from honeypot or curriculum
        recent_ttps = []
        if results.get("honeypot") and results["honeypot"].get("ttps"):
            recent_ttps = [t.get("ttp_id", "") for t in results["honeypot"]["ttps"][:5] if t.get("ttp_id")]
        
        if recent_ttps:
            predictions = causal.predict_next_stages(recent_ttps)
            if predictions:
                top_prediction = predictions[0]
                print(f"[PHASE B] Causal prediction: next likely stage = {top_prediction['predicted_stage']} "
                      f"(probability: {top_prediction['probability']:.0%})")
                results["causal_predictions"] = predictions[:3]
    
    except ImportError as e:
        print(f"[PHASE B] Causal reasoning import error: {e}")
    except Exception as e:
        print(f"[PHASE B] Causal reasoning error: {e}")
    

    # ---- PHASE C: DEFENSIVE RESPONSE ----
    try:
        from defensive_response import DefensiveResponseEngine
        
        # Get honeypot events if available
        honeypot_events = []
        if results.get("honeypot") and results["honeypot"].get("ttps"):
            honeypot_events = results["honeypot"].get("ttps", [])
        
        # Run defensive response if we have events
        if honeypot_events:
            defense = DefensiveResponseEngine()
            defense_result = defense.run_defensive_cycle(honeypot_events)
            results["defensive_response"] = defense_result
            
            attacks = defense_result.get("attacks_detected", 0)
            if attacks > 0:
                blocked = len([r for r in defense_result.get("responses", []) if "BLOCK" in str(r.get("steps", []))])
                print(f"[PHASE C] Defense: {attacks} attacks → {blocked} blocked")
                
                # Show threat summary
                summary = defense.get_threat_summary()
                print(f"[PHASE C] Threat level: {len(summary['high_threats'])} high, {len(summary['medium_threats'])} medium, {summary['blocked_ips']} blocked")
        else:
            print("[PHASE C] Defense: No events to process")
    
    except ImportError as e:
        print(f"[PHASE C] Defensive response import error: {e}")
    except Exception as e:
        print(f"[PHASE C] Defensive response error: {e}")

    return results


if __name__ == "__main__":
    # Self-test without orchestrator
    print("Phase B Runner Self-Test")
    print("=" * 50)
    results = run_phase_b(None)
    print(f"\nResults: {json.dumps(results, indent=2, default=str)[:1000]}")
