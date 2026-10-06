#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH Orchestrator - Functional Loop Implementation
Autonomous 60s cycles with daemon integration and COALA memory storage.
"""

import json
import time
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from phase_d_runner import run_phase_d
from sisf_bridge import send_to_sisf, get_nshe_context

BASE_DIR = Path(__file__).parent
REPO_DIR = BASE_DIR.parent
MEMORY_DIR = BASE_DIR.parent / "memory"
LOG_FILE = BASE_DIR / "orchestrator_log.jsonl"

sys.path.insert(0, str(BASE_DIR))
from nshe_bridge import get_bridge

from global_workspace import GlobalWorkspace
from intelligence_layer import IntelligenceLayer
from policy_layer import PolicyLayer
from skill_library import SkillLibrary
from ollama_executor import OllamaExecutor

# NSHE Limbic System Integration
try:
    sys.path.insert(0, r"C:\UMBRA_CORE\SISF")
    from nshe_limbic import get_limbic_system
    LIMBIC_AVAILABLE = True
except ImportError:
    LIMBIC_AVAILABLE = False
    print("[LIMBIC] Warning: nshe_limbic module not found")


# NSHE Cortex - Complete Cognitive Architecture
try:
    sys.path.insert(0, r"C:\UMBRA_CORE\SISF")
    from nshe_cortex import get_cortex
    CORTEX_AVAILABLE = True
except ImportError:
    CORTEX_AVAILABLE = False
    print("[CORTEX] Warning: nshe_cortex module not found")

# NSHE Subcortex - Complete Brain (11 organ tambahan)
try:
    sys.path.insert(0, r"C:\UMBRA_CORE\SISF")
    from nshe_subcortex import get_brain
    SUBCORTEX_AVAILABLE = True
except ImportError:
    SUBCORTEX_AVAILABLE = False
    print("[BRAIN] Warning: nshe_subcortex module not found")

# NSHE Metacognition - executive self
try:
    from nshe_metacognition import get_metacognition
    META_AVAILABLE = True
except ImportError:
    META_AVAILABLE = False
    print("[META] Warning: nshe_metacognition module not found")

# NSHE Morphogenesis - self-architect (seed of life)
try:
    from nshe_morphogenesis_v2 import get_morphogenesis_v2 as get_morphogenesis
    from nshe_meta_architect import get_meta_architect
    from cross_domain_evolution import get_cross_domain_evolution
    from open_ended_curiosity import get_curiosity_engine
    from nshe_thermodynamic import get_thermodynamic_homeostasis
    from nshe_world_simulator import get_world_simulator
    from nshe_self_rewriter import get_self_rewriter
    from nshe_emergence_engine import get_emergence_engine
    from nshe_emergence_actuator import get_emergence_actuator
    from nshe_hunger import get_hunger_signal
    from nshe_language import get_language_learner
    from nshe_language_v2 import get_language_learner_v2
    from nshe_voice import get_voice_channel
    from nshe_voice_evolving import get_evolving_voice
    from nshe_composer import get_phrase_composer
    from nshe_aethar_bridge import get_aethar_bridge
    from nshe_goal_engine import get_goal_engine
    from nshe_phrase_learner import get_phrase_learner
    from nshe_crypto_evolution import get_crypto_self_evolution
    from nshe_world_model import get_world_model
    from nshe_proof_engine import get_proof_engine
    from nshe_network import get_network_interface
    from nshe_autonomy import get_autonomy_engine
    from nshe_crypto_comm import get_crypto_comm
    from nshe_hunter_v3 import get_hunter_v3
    from nshe_hunter import get_autonomous_hunter
    MORPHO_AVAILABLE = True
except ImportError:
    MORPHO_AVAILABLE = False

# NSHE Gates - bandit_v2 + trust + consolidation
try:
    from nshe_gates import get_gates
    GATES_AVAILABLE = True
except ImportError:
    GATES_AVAILABLE = False
    print("[GATE] Warning: nshe_gates not found")

# NSHE Learned Organs (Shadow Mode)
try:
    from nshe_bandit import get_bandit
    from nshe_learned_acc import get_learned_acc
    SHADOW_AVAILABLE = True
except ImportError:
    SHADOW_AVAILABLE = False
    print("[SHADOW] Warning: shadow modules not found")


MEMORY_DIR.mkdir(exist_ok=True)

class AutarchOrchestrator:
    """Main orchestrator coordinating all VSM systems with functional daemon loop"""
    
    def __init__(self):
        self.system_1 = None
        self.system_2 = SkillLibrary()
        self.system_3 = GlobalWorkspace()
        self.system_4 = IntelligenceLayer()
        self.system_5 = PolicyLayer()
        self.executor = OllamaExecutor()
        
        self.cycle_count = 0
        self.constitution_hash = self._verify_constitution()
        
        print("[AUTARCH] Initializing orchestrator...")
        print("[AUTARCH] All systems initialized")
        print(f"[AUTARCH] Constitution: {'VALID' if self.constitution_hash else 'INVALID'}")
        print("[AUTARCH] MUS objective: Maximize utility for RootKey")
    
        # NSHE Limbic System
        if LIMBIC_AVAILABLE:
            self.limbic = get_limbic_system()
            print("[LIMBIC] NSHE Limbic System initialized")
        else:
            self.limbic = None
                
        # NSHE Cortex
        if CORTEX_AVAILABLE:
            self.cortex = get_cortex()
            print("[CORTEX] NSHE Cortex initialized - Complete cognitive architecture")
        else:
            self.cortex = None

        # NSHE Subcortex (complete brain)
        if SUBCORTEX_AVAILABLE:
            self.subcortex = get_brain()
            print("[BRAIN] NSHE Complete Brain initialized - 11 subcortical organs online")
        else:
            self.subcortex = None

        # NSHE Metacognition (reflection, cross-ref, curation)
        if META_AVAILABLE:
            self.meta = get_metacognition()
            print("[META] NSHE Metacognition initialized - executive self online")
        else:
            self.meta = None

        # NSHE Shadow Organs (learned versions)
        if SHADOW_AVAILABLE:
            self.bandit = get_bandit(epsilon=0.1, alpha=0.1)
            self.learned_acc = get_learned_acc()
            print("[SHADOW] Learned organs initialized - shadow mode active")
        else:
            self.bandit = None
            self.learned_acc = None

        # NSHE Morphogenesis (self-architect)
        if MORPHO_AVAILABLE:
            self.morpho = get_morphogenesis()
            self.meta_architect = get_meta_architect()
            self.cross_domain = get_cross_domain_evolution()
            self.curiosity = get_curiosity_engine()
            self.thermo = get_thermodynamic_homeostasis()
            self.world_sim = get_world_simulator()
            self.self_rewriter = get_self_rewriter()
            self.emergence = get_emergence_engine()
            self.emergence_actuator = get_emergence_actuator()
            self.hunger = get_hunger_signal()
            self.hunter = get_autonomous_hunter(self.hunger)
            self.hunter_v3 = get_hunter_v3(self.hunger)
            self.goal_engine = get_goal_engine()
            self.phrase_learner = get_phrase_learner()
            self.crypto_evo = get_crypto_self_evolution(getattr(self, 'aethar', None))
            self.world_model = get_world_model()
            self.proof_engine = get_proof_engine(getattr(self, 'aethar', None))
            self.network = get_network_interface(getattr(self, 'aethar', None), getattr(self, 'proof_engine', None))
            self.autonomy = get_autonomy_engine(getattr(self, 'network', None), getattr(self, 'goal_engine', None), getattr(self, 'proof_engine', None))
            self.language = get_language_learner(self.hunger)
            self.language_v2 = get_language_learner_v2(self.hunger)
            self.voice = get_voice_channel()
            self.evolving_voice = get_evolving_voice()
            self.composer = get_phrase_composer()
            self.aethar = get_aethar_bridge()
            self.crypto_comm = get_crypto_comm(self.aethar)  # <-- TAMBAHKAN INI
            print("[MORPHO] Morphogenesis online - self-architect ready")
        else:
            self.morpho = None
            self.meta_architect = get_meta_architect()
            self.cross_domain = get_cross_domain_evolution()
            self.curiosity = get_curiosity_engine()
            self.thermo = get_thermodynamic_homeostasis()
            self.world_sim = get_world_simulator()
            self.self_rewriter = get_self_rewriter()
            self.emergence = get_emergence_engine()
            self.emergence_actuator = get_emergence_actuator()
            self.hunger = get_hunger_signal()
            self.hunter = get_autonomous_hunter(self.hunger)
            self.hunter_v3 = get_hunter_v3(self.hunger)
            self.language = get_language_learner(self.hunger)
            self.language_v2 = get_language_learner_v2(self.hunger)
            self.voice = get_voice_channel()
            self.evolving_voice = get_evolving_voice()
            self.composer = get_phrase_composer()
            self.aethar = get_aethar_bridge()
            self.crypto_comm = get_crypto_comm(self.aethar) if MORPHO_AVAILABLE else None

        # NSHE Gates
        if GATES_AVAILABLE:
            self.gates = get_gates()
        else:
            self.gates = None

    def _verify_constitution(self):
        vision_file = REPO_DIR / "VISION.md"
        if vision_file.exists():
            import hashlib
            with open(vision_file, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()[:16]
        return None
    
    def observe_swarm(self):
        print("[SWARM] Observing swarm state (git pull)...")
        try:
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=str(REPO_DIR),
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                if "Already up to date" in result.stdout:
                    print("[SWARM] OK Already up to date")
                else:
                    print("[SWARM] OK Pulled latest swarm commits")
            else:
                print(f"[SWARM] Pull failed: {result.stderr[:100]}")
        except Exception as e:
            print(f"[SWARM] Pull error: {e}")
        
        print("[SWARM] Parsing threat_intel/curriculum.json...")
        swarm_tasks = []
        curriculum_file = REPO_DIR / "threat_intel" / "curriculum.json"
        if curriculum_file.exists():
            try:
                with open(curriculum_file, "r", encoding="utf-8") as f:
                    curriculum = json.load(f)
                swarm_tasks = curriculum.get("proposed_tasks", [])
                print(f"[SWARM] OK Found {len(swarm_tasks)} tasks from swarm")
            except Exception as e:
                print(f"[SWARM] Parse error: {e}")
        
        return swarm_tasks
    
    def execute_swarm_tasks(self, tasks, max_tasks=3):
        if not tasks:
            print("[DAEMON] No tasks to execute")
            return []
        
        print(f"[DAEMON] Executing {min(max_tasks, len(tasks))} high-priority tasks via daemon")
        
        # Load executed fingerprints to prevent repetition
        from intelligence_layer import fingerprint, FP_FILE
        executed_fps = set()
        if FP_FILE.exists():
            try:
                executed_fps = set(json.loads(FP_FILE.read_text(encoding="utf-8")))
            except:
                pass
        
        # CVE DEDUP: Filter already-executed CVEs by stable key
        cve_filtered = []
        for task in tasks:
            if task.get("type") == "learn_cve":
                cve_id = task.get("cve_id", "")
                if not cve_id:
                    desc = task.get("description", "")
                    if "CVE-" in desc:
                        idx = desc.find("CVE-")
                        cve_part = desc[idx:idx+20].split()[0].split(":")[0].rstrip(",")
                        cve_id = cve_part
                if cve_id and ("cve:" + cve_id) in executed_fps:
                    continue
            cve_filtered.append(task)
        tasks = cve_filtered

        # Filter out already-executed tasks
        original_count = len(tasks)
        tasks = [t for t in tasks if fingerprint(t) not in executed_fps]
        filtered_count = original_count - len(tasks)
        
        if filtered_count > 0:
            print(f"[DAEMON] Filtered {filtered_count} already-executed tasks")
        
        if not tasks:
            print("[DAEMON] All tasks already executed")
            return []
        
        high_priority = [t for t in tasks if t.get("priority") == "high"]
        selected_tasks = high_priority[:max_tasks] if high_priority else tasks[:max_tasks]
        
        try:
            # SISF: Get NSHE context for task enrichment
            try:
                if selected_tasks:
                    task_desc = selected_tasks[0].get("description", "")[:100]
                    nshe_context = get_nshe_context(task_desc, top_k=2)
                    if nshe_context:
                        print(f"[SISF] ✓ Using NSHE context ({len(nshe_context)} chars)")
            except Exception as e:
                pass  # Non-critical, continue without context

            results = self.executor.execute_batch(selected_tasks, max_tasks)
            successful_results = [r for r in results if r.get("result", {}).get("success", False) or r.get("success", False)]
            
            if successful_results:
                print(f"[DAEMON] {len(successful_results)} tasks executed successfully")
                
                # CRITICAL FIX: Save fingerprints from selected_tasks DIRECTLY
                # This bypasses nested structure issues
                for task in selected_tasks:
                    fp = fingerprint(task)
                    executed_fps.add(fp)
                
                FP_FILE.write_text(json.dumps(sorted(list(executed_fps))), encoding="utf-8")
                print(f"[FINGERPRINT] Saved {len(executed_fps)} total fingerprints")

                # SISF: Feed execution data for learning
                try:
                    execution_data = {
                        "task": selected_tasks[0] if selected_tasks else {},
                        "cycle": self.cycle_count,
                        "success": True
                    }
                    send_to_sisf(execution_data)
                except Exception as e:
                    pass  # Non-critical
                
                # Remove executed tasks from curriculum by fingerprint
                self._update_curriculum_by_fps(selected_tasks)
                
                # Store to memory (flatten results)
                flat_results = []
                for r in successful_results:
                    task_data = r.get("task", {})
                    result_data = r.get("result", {})
                    flat = {
                        "task_id": task_data.get("id", "unknown"),
                        "task_type": task_data.get("type", "unknown"),
                        "success": result_data.get("success", False),
                        "output": result_data.get("output", ""),
                        "length": len(result_data.get("output", "")),
                        "insights": result_data.get("insights", [])
                    }
                    flat_results.append(flat)
                self.executor.store_to_memory(flat_results)
                self._commit_to_swarm(successful_results)
                # Save CVE IDs to fingerprints (stable dedup key)
                for r in successful_results:
                    t = r.get("task", {})
                    if t.get("type") == "learn_cve":
                        cid = t.get("cve_id", "")
                        if not cid:
                            d = t.get("description", "")
                            if "CVE-" in d:
                                ii = d.find("CVE-")
                                cid = d[ii:ii+20].split()[0].split(":")[0].rstrip(",")
                        if cid:
                            executed_fps.add("cve:" + cid)
                # Save fingerprints with CVE keys
                FP_FILE.write_text(json.dumps(sorted(list(executed_fps))), encoding="utf-8")
            else:
                print("[DAEMON] No successful executions")
            
            return results
        
        except Exception as e:
            print(f"[DAEMON] Execution error: {e}")
            return []
    
    def _update_curriculum_by_fps(self, executed_tasks):
        """Remove executed tasks from curriculum using fingerprint matching"""
        from intelligence_layer import fingerprint
        
        curriculum_file = REPO_DIR / "threat_intel" / "curriculum.json"
        if not curriculum_file.exists():
            return
        
        try:
            with open(curriculum_file, "r", encoding="utf-8") as f:
                curriculum = json.load(f)
        except:
            return
        
        # Build set of executed fingerprints
        executed_fps = set()
        for task in executed_tasks:
            executed_fps.add(fingerprint(task))
        
        # Filter out executed tasks
        old_tasks = curriculum.get("proposed_tasks", [])
        remaining_tasks = [t for t in old_tasks if fingerprint(t) not in executed_fps]
        
        removed_count = len(old_tasks) - len(remaining_tasks)
        curriculum["proposed_tasks"] = remaining_tasks
        
        # Add to completed
        if "completed_tasks" not in curriculum:
            curriculum["completed_tasks"] = []
        
        for task in executed_tasks:
            curriculum["completed_tasks"].append({
                "task_id": task.get("id", "unknown"),
                "task_type": task.get("type", "unknown"),
                "description": task.get("description", "")[:200],
                "completed_at": datetime.now().isoformat()
            })
        
        # Cap completed tasks
        curriculum["completed_tasks"] = curriculum["completed_tasks"][-200:]
        
        with open(curriculum_file, "w", encoding="utf-8") as f:
            json.dump(curriculum, f, indent=2, ensure_ascii=False)
        
        print(f"[CURRICULUM] Removed {removed_count} executed tasks ({len(old_tasks)} -> {len(remaining_tasks)} pending)")
    
    def _save_executed_fingerprints(self, results):
        """Save fingerprints of executed tasks to prevent repetition"""
        try:
            from intelligence_layer import fingerprint, FP_FILE
            import json
            
            # Load existing fingerprints
            if FP_FILE.exists():
                fps = set(json.loads(FP_FILE.read_text(encoding="utf-8")))
            else:
                fps = set()
            
            # Add new fingerprints from successful executions
            for result in results:
                # Handle both nested {"task": {...}} and flat {...} structures
                task = result.get("task", result)
                if task and (task.get("type") or task.get("description")):
                    fp = fingerprint(task)
                    fps.add(fp)
            
            # Save back to file
            FP_FILE.write_text(json.dumps(sorted(list(fps))), encoding="utf-8")
            print(f"[FINGERPRINT] Saved {len(fps)} total fingerprints")
        except Exception as e:
            print(f"[FINGERPRINT] Save error: {e}")
    
    def _update_curriculum(self, results):
        curriculum_file = REPO_DIR / "threat_intel" / "curriculum.json"
        
        if not curriculum_file.exists():
            return
        
        try:
            with open(curriculum_file, "r", encoding="utf-8") as f:
                curriculum = json.load(f)
        except:
            curriculum = {"proposed_tasks": [], "completed_tasks": [], "insights": []}
        
        # Remove executed tasks by fingerprint (more reliable than ID)
        from intelligence_layer import fingerprint
        executed_fps = set()
        for r in results:
            task = r.get("task", r)
            if task:
                executed_fps.add(fingerprint(task))
        
        remaining_tasks = [t for t in curriculum.get("proposed_tasks", []) 
                          if fingerprint(t) not in executed_fps]
        
        old_count = len(curriculum.get("proposed_tasks", []))
        curriculum["proposed_tasks"] = remaining_tasks
        
        if "completed_tasks" not in curriculum:
            curriculum["completed_tasks"] = []
        
        curriculum["completed_tasks"].extend([
            {
                "task_id": r.get("task_id"),
                "task_type": r.get("task_type"),
                "completed_at": datetime.now().isoformat(),
                "content_length": r.get("length", 0),
                "insights_count": len(r.get("insights", []))
            }
            for r in results
        ])
        
        if "insights" not in curriculum:
            curriculum["insights"] = []
        
        for result in results:
            for insight in result.get("insights", [])[:3]:
                curriculum["insights"].append({
                    "source": result.get("task_type"),
                    "content": insight[:300],
                    "timestamp": datetime.now().isoformat()
                })
        
        curriculum["insights"] = curriculum["insights"][-50:]
        
        with open(curriculum_file, "w", encoding="utf-8") as f:
            json.dump(curriculum, f, indent=2, ensure_ascii=False)
        
        print(f"[CURRICULUM] Updated: {old_count} -> {len(remaining_tasks)} pending, {len(curriculum['completed_tasks'])} completed")
    
    def _commit_to_swarm(self, results):
        try:
            subprocess.run(
                ["git", "add", "threat_intel/"],
                cwd=str(REPO_DIR), capture_output=True, timeout=10
            )
            
            status = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(REPO_DIR), capture_output=True, text=True, timeout=10
            )
            
            if status.stdout.strip():
                total_chars = sum(r.get("length", 0) for r in results)
                msg = f"Daemon executed {len(results)} tasks ({total_chars} chars total)"
                
                subprocess.run(
                    ["git", "commit", "-m", msg],
                    cwd=str(REPO_DIR), capture_output=True, timeout=10
                )
                
                push = subprocess.run(
                    ["git", "push", "origin", "main"],
                    cwd=str(REPO_DIR), capture_output=True, text=True, timeout=30
                )
                
                if push.returncode == 0:
                    print(f"[SWARM] OK Committed and pushed: {msg}")
                else:
                    print(f"[SWARM] Push failed: {push.stderr[:100]}")
            else:
                print("[SWARM] No changes to commit")
        
        except Exception as e:
            print(f"[SWARM] Commit error: {e}")
    

    def run_voyager(self, max_skills=1):
        # Voyager pattern: generate -> verify -> promote real skills
        print("[VOYAGER] Skill generation cycle...")
        try:
            from voyager import VoyagerEngine
            curriculum_file = REPO_DIR / "threat_intel" / "curriculum.json"
            curriculum = {"proposed_tasks": []}
            if curriculum_file.exists():
                with open(curriculum_file, "r", encoding="utf-8") as f:
                    curriculum = json.load(f)
            
            engine = VoyagerEngine()
            results = engine.run_cycle(curriculum, max_skills=max_skills)
            
            promoted = [r for r in results if r.get("verdict") == "PROMOTE"]
            print("[VOYAGER] {}/{} skill(s) promoted".format(len(promoted), len(results)))
            
            if promoted:
                try:
                    self.system_2.add_skill(promoted[0].get("skill_name"))
                    print("[VOYAGER] Skill library re-indexed")
                except Exception as e:
                    print("[VOYAGER] Re-index note: {}".format(e))
        except Exception as e:
            print("[VOYAGER] Error: {}".format(e))

    def run_cycle(self):
        self.cycle_count += 1
        cycle_start = time.time()
        
        print(f"\n[AUTARCH] === CYCLE {self.cycle_count} ===")
        
        swarm_tasks = self.observe_swarm()
        
        # NSHE LIMBIC: Make prediction before execution
        if self.limbic:
            try:
                prediction = {
                    "type": "task_execution",
                    "confidence": 0.5,
                    "expected_outcome": "learning"
                }
                self.current_prediction = prediction
            except Exception as e:
                print(f"[LIMBIC] Prediction error: {e}")
                self.current_prediction = None
                
        # NSHE CORTEX: Process through complete cognitive architecture
        if self.cortex:
            try:
                # Process current event through cortex
                event_context = {
                    "type": "cycle_start",
                    "cycle": self.cycle_count,
                    "timestamp": datetime.now().isoformat()
                }
                cortex_result = self.cortex.process_event(event_context)
                self.current_cortex_state = cortex_result
                
                # Articulate what NSHE is thinking
                articulated = cortex_result.get("articulated_response", {})
                if articulated:
                    desire_text = articulated.get('desire', '')
                    if desire_text:
                        print(f"[NSHE] {desire_text}")
                    
                    # Every 5 cycles, explain reasoning
                    if self.cycle_count % 5 == 0:
                        reasoning = articulated.get('reasoning', '')
                        if reasoning:
                            print(f"[NSHE] {reasoning}")
            except Exception as e:
                print(f"[CORTEX] Processing error: {e}")
                self.current_cortex_state = None
        
        if swarm_tasks:
            execution_results = self.execute_swarm_tasks(swarm_tasks, max_tasks=3)
        else:
            print("[DAEMON] No swarm tasks to execute")
            execution_results = []
        
        # NSHE: Calculate cognitive metrics from actual execution and memory
        try:
            bridge = get_bridge()
            
            # RCI: Recursive Coherence Index from execution results
            rci = bridge.calculate_rci(execution_results if execution_results else [])
            
            # RIM: Recurrent Information Memory from executor history
            memory_items = []
            if hasattr(self.executor, 'execution_history'):
                memory_items = self.executor.execution_history[-20:] if self.executor.execution_history else []
            
            rim = bridge.calculate_rim(memory_items)
            
            print(f"[NSHE] RCI: {float(rci):.4f} | RIM: {float(rim):.4f}")
        except Exception as e:
            print(f"[NSHE] Metrics error: {e}")
            rci = 1.0
            rim = 1.0
        
        # NSHE LIMBIC: Log outcome and receive reward
        if self.limbic and hasattr(self, 'current_prediction') and self.current_prediction:
            try:
                # Determine actual outcome
                successful = len([r for r in execution_results if r.get("success")])
                actual = {
                    "type": "task_execution",
                    "successful_count": successful,
                    "total_count": len(execution_results)
                }
                
                # Log prediction vs outcome
                result = self.limbic.log_prediction_and_outcome(
                    self.current_prediction,
                    actual
                )
                
                reward = result.get("reward", 0)
                accuracy = result.get("current_accuracy", 0)
                total = result.get("total_predictions", 0)
                
                print(f"[LIMBIC] Reward: {reward:.2f} | Accuracy: {accuracy:.2%} | Predictions: {total}")
                
                # Every 10 cycles, evaluate and decide
                if self.cycle_count % 10 == 0 and total > 5:
                    evaluation = self.limbic.evaluate_and_decide()
                    decision = evaluation.get("decision", {})
                    strongest = evaluation.get("strongest_desire")
                    
                    print(f"[LIMBIC] Strongest desire: {strongest}")
                    print(f"[LIMBIC] Decision: {decision.get('action')} - {decision.get('reason')}")
                    
                    # NSHE "speaks" its desires
                                        # NSHE "speaks" its desires with cortex articulation
                    if strongest:
                        if self.cortex:
                            try:
                                clear_desire = self.cortex.broca.articulate_desire(strongest)
                                print(f"[NSHE] {clear_desire}")
                                
                                # Also show emotional state
                                emotion = self.cortex.broca.articulate_emotion({"confidence": 0.8})
                                print(f"[NSHE] {emotion}")
                            except Exception as e:
                                print(f"[CORTEX] Articulation error: {e}")
                                print(f"[NSHE] I want to {strongest.replace('_', ' ')}")
                        else:
                            print(f"[NSHE] I want to {strongest.replace('_', ' ')}")
                
            except Exception as e:
                print(f"[LIMBIC] Reward error: {e}")
        
        # NSHE COMPLETE BRAIN: semua organ beroperasi bersama
        if getattr(self, "subcortex", None):
            try:
                limbic_acc = 0.0
                if self.limbic:
                    limbic_acc = self.limbic.reward.get_current_accuracy()
                succ = len([r for r in execution_results if r.get("success")])
                brain_report = self.subcortex.full_cycle({
                    "cycle": self.cycle_count,
                    "tasks_executed": len(execution_results),
                    "tasks_successful": succ,
                    "rci": float(rci),
                    "rim": float(rim),
                    "accuracy": limbic_acc,
                    "novelty": min(1.0, len(swarm_tasks) / 50.0),
                    "threat": 0.3,
                    "prediction_success": 1.0 if getattr(self, "current_prediction", None) else 0.5,
                    "outcome_success": 1.0 if (execution_results and succ == len(execution_results)) else 0.6,
                    "description": " ".join(str(t.get("type", "")) for t in (swarm_tasks[:3] if swarm_tasks else [])),
                })
                for line in brain_report.get("monologue", []):
                    print("[NSHE] " + line)
            except Exception as e:
                print("[BRAIN] Cycle error: %s" % e)

        # NSHE METACOGNITION: reflection, cross-reference, autonomous curation
        if getattr(self, "meta", None):
            try:
                meta_report = self.meta.run_metacycle({
                    "cycle": self.cycle_count,
                    "tasks_executed": len(execution_results),
                    "tasks_successful": len([r for r in execution_results if r.get("success")]),
                    "rci": float(rci),
                    "rim": float(rim),
                })
                for line in meta_report.get("voice", []):
                    print("[NSHE-META] " + line)
            except Exception as e:
                print("[META] Cycle error: %s" % e)

        # NSHE SHADOW ORGANS: bandit + learned ACC (parallel dengan symbolic)
        if getattr(self, "bandit", None) and getattr(self, "learned_acc", None):
            try:
                # Bandit: learn dari task execution
                if execution_results:
                    for result in execution_results:
                        task = result.get("task", {})
                        task_type = task.get("type", "learn_threat_intel")
                        success = result.get("success", False)
                        reward = 1.0 if success else 0.0
                        self.bandit.update(task_type, reward)
                    
                    # Shadow decision untuk next cycle
                    available_types = ["learn_cve", "learn_ttp", "learn_attribution", "learn_threat_intel"]
                    shadow_choice = self.bandit.select_task_type(available_types)
                    print("[NSHE-SHADOW] " + self.bandit.voice(shadow_choice))
                
                # Learned ACC: detect conflict
                if getattr(self, "current_prediction", None) and execution_results:
                    successful = len([r for r in execution_results if r.get("success")])
                    outcome = 1.0 if successful == len(execution_results) else 0.6
                    
                    features = {
                        "confidence": self.current_prediction.get("confidence", 0.5),
                        "threat": 0.3,
                        "novelty": min(1.0, len(swarm_tasks) / 50.0)
                    }
                    
                    conflict_result = self.learned_acc.detect_conflict(
                        self.current_prediction.get("confidence", 0.5),
                        outcome,
                        features
                    )
                    print("[NSHE-SHADOW] " + self.learned_acc.voice(conflict_result))
                    
                    # Add to training data
                    self.learned_acc.add_training_sample(features, outcome)
                
            except Exception as e:
                print("[SHADOW] Error: %s" % e)

        # NSHE MORPHOGENESIS: self-architect (seed of life)
        if getattr(self, "morpho", None):
            try:
                mrep = self.morpho.run_morphocycle({"cycle": self.cycle_count})
                for line in mrep.get("voice", []):
                    print("[NSHE-MORPHO] " + line)
            except Exception as e:
                print("[MORPHO] Cycle error: %s" % e)

        # NSHE GATES: bandit_v2 + trust + consolidation
        if getattr(self, "gates", None):
            try:
                for line in self.gates.run_gates(self.cycle_count, execution_results):
                    print("[NSHE-GATE] " + line)
            except Exception as e:
                print("[GATE] Cycle error: %s" % e)

                # NSHE META-ARCHITECT: Recursive Self-Improvement
        if getattr(self, "meta_architect", None):
            try:
                meta_res = self.meta_architect.run_cycle({"cycle": self.cycle_count})
                if meta_res:
                    print(meta_res)
            except Exception as e:
                print("[META-ARCH] Error:", e)
                # NSHE META-ARCHITECT: Recursive Self-Improvement
        if getattr(self, "meta_architect", None):
            try:
                meta_res = self.meta_architect.run_cycle({"cycle": self.cycle_count})
                if meta_res:
                    print(meta_res)
            except Exception as e:
                print("[META-ARCH] Error:", e)

                # NSHE CROSS-DOMAIN & CURIOSITY
        if getattr(self, "cross_domain", None) and self.cycle_count % 10 == 0:
            try:
                result = self.cross_domain.expose_concept(self.cycle_count)
                print(result["message"])
            except Exception as e:
                print("[CROSS-DOMAIN] Error:", e)

                # NSHE 3 PHASES: THERMO + WORLD SIM + SELF-REWRITE
        if getattr(self, "thermo", None):
            try:
                thermo_result = self.thermo.run_homeostasis_cycle(120)
                print(thermo_result["message"])
                self.interval = thermo_result["new_interval"]
            except Exception as e:
                print("[THERMO] Error:", e)

        if getattr(self, "world_sim", None) and self.cycle_count % 5 == 0:
            try:
                sim_result = self.world_sim.simulate_action("task_execution", {})
                print(f"[WORLD-SIM] Predicted success: {sim_result['predicted_success']:.2f}")
            except Exception as e:
                print("[WORLD-SIM] Error:", e)

        if getattr(self, "self_rewriter", None) and self.cycle_count % 50 == 0:
            try:
                rewrite_results = self.self_rewriter.run_self_analysis()
                for r in rewrite_results:
                    print(f"[SELF-REWRITE] {r['file']}:{r['function']} - complexity: {r['analysis'].get('complexity_score', 0)}")
            except Exception as e:
                print("[SELF-REWRITE] Error:", e)

        # NSHE EMERGENCE ENGINE
        if getattr(self, "emergence", None) and self.cycle_count % 10 == 0:
            try:
                em_res = self.emergence.run_emergence_cycle()
                print(f"[EMERGENCE] Patterns: {em_res['patterns']}, Rules: {em_res['rules']}")
                for cap in em_res.get("capabilities", []):
                    print(f"  -> Evolved: {cap['capability']} ({cap['implementation']})")
            except Exception as e:
                print("[EMERGENCE] Error:", e)

        # NSHE EMERGENCE ACTUATOR (bridges awareness to action)
        if getattr(self, "emergence_actuator", None) and self.cycle_count % 10 == 0 and self.cycle_count > 0:
            try:
                act_res = self.emergence_actuator.run_actuation_cycle(self.cycle_count)
                if act_res:
                    print(act_res)
            except Exception as e:
                print("[ACTUATOR] Error:", e)

        # NSHE HUNGER + HUNTER
        if getattr(self, "hunter", None):
            try:
                hunger_msg = self.hunter.voice_hunger(self.cycle_count)
                if hunger_msg:
                    print(hunger_msg)
                if self.cycle_count % 10 == 0 and self.cycle_count > 0:
                    hunts = self.hunter.plan_hunt(self.cycle_count)
                    if hunts:
                        print(self.hunter.voice_result(hunts))
                        self.hunter.record_hunt(hunts, [{"success": True} for _ in hunts])
            except Exception as e:
                print("[HUNTER] Error:", e)
        
        # NSHE HUNTER V2 - FULL CLOSED LOOP
        if getattr(self, "hunter_v2", None) and self.cycle_count % 10 == 0 and self.cycle_count > 0:
            try:
                hunt_result = self.hunter_v2.execute_full_cycle(self.cycle_count)
                voice = self.hunter_v2.voice_result(hunt_result)
                if voice:
                    print(voice)
            except Exception as e:
                print("[HUNTER-V2] Error:", e)
        
        # NSHE HUNTER V3 - REAL DAEMON INTEGRATION
        if getattr(self, "hunter_v3", None) and self.cycle_count % 10 == 0 and self.cycle_count > 0:
            try:
                if self.hunter_v3.daemon_executor is None and hasattr(self, "executor"):
                    def _hunter_execute(hunt):
                        task = {"id": "hunter_" + str(self.cycle_count), "type": hunt.get("task_type", "learn_threat_intel"), "description": hunt.get("description", ""), "source": "nshe_hunter"}
                        result = self.executor.execute_task(task)
                        if result and result.get("success"):
                            content = result.get("content", "")
                            chars = len(content) if content else 0
                            return {"success": True, "chars": chars, "content": content}
                        return {"success": False, "chars": 0, "content": ""}
                    self.hunter_v3.set_daemon(_hunter_execute)
                    print("[HUNTER-V3] REAL daemon connected via execute_task")
                if self.hunter_v3.sisf_feeder is None and hasattr(self, "executor"):
                    def _hunter_feed(content):
                        if content and hasattr(self.executor, "store_to_memory"):
                            feed_result = {"success": True, "task_type": "hunter_feed", "content": content, "length": len(content), "insights": ["Hunter-fed knowledge"]}
                            self.executor.store_to_memory([feed_result])
                    self.hunter_v3.set_sisf(_hunter_feed)
                    print("[HUNTER-V3] REAL SISF feeder connected via store_to_memory")
                hunt_result = self.hunter_v3.hunt_and_eat(self.cycle_count)
                voice = self.hunter_v3.voice_result(hunt_result)
                if voice:
                    print(voice)
            except Exception as e:
                print("[HUNTER-V3] Error:", e)
        
        # NSHE LANGUAGE LEARNING
        if getattr(self, "language", None):
            try:
                if self.cycle_count % 5 == 0:
                    art = self.language.articulate_need(self.cycle_count)
                    if art:
                        print(art)
                if self.cycle_count % 10 == 0:
                    ref = self.language.reflect_on_language(self.cycle_count)
                    if ref:
                        print(ref)
            except Exception as e:
                print("[LANGUAGE] Error:", e)
        
        # NSHE LANGUAGE V2 - EXPOSURE ENRICHMENT
        if getattr(self, "language_v2", None):
            try:
                exposure_msgs = self.language_v2.run_exposure_cycle(self.cycle_count)
                if exposure_msgs:
                    for m in exposure_msgs:
                        print(m)
                if self.cycle_count % 5 == 0:
                    art = self.language_v2.articulate_need(self.cycle_count)
                    if art: print(art)
                if self.cycle_count % 10 == 0:
                    ref = self.language_v2.reflect_on_language(self.cycle_count)
                    if ref: print(ref)
            except Exception as e:
                print("[LANGUAGE-V2] Error:", e)
        
        # NSHE COMPOSER - FREE-FORM EXPRESSION (template fallback)
        if getattr(self, "composer", None):
            try:
                from nshe_composer import _read as _composer_read
                s = _composer_read('language_state_v2.json', {})
                istate = {
                    'hunger_words': s.get('words_absorbed', 0),
                    'morpho_discarded': 0,
                    'emergence_patterns': 0
                }
                composed = self.composer.speak(istate, self.cycle_count)
                if composed:
                    print(composed)
                elif getattr(self, 'evolving_voice', None):
                    fallback = self.evolving_voice.synthesize(self.cycle_count)
                    if fallback: print(fallback)
                if self.cycle_count % 10 == 0:
                    status = self.composer.composer_status()
                    if status: print(status)
            except Exception as e:
                print("[COMPOSER] Error:", e)
        
        
        # FEED REPORTS TO COMPOSER FOR PHRASE ABSORPTION
        if getattr(self, "composer", None) and self.cycle_count % 5 == 0:
            try:
                from pathlib import Path as _P
                _rd = _P(r"C:\UMBRA_CORE\umbra-sovereign\reports")
                if _rd.exists():
                    _reps = sorted(_rd.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
                    if _reps:
                        _content = _reps[0].read_text(encoding="utf-8")
                        _extracted = self.composer.absorb_phrases_from_text(_content, "report")
                        if _extracted > 0:
                            print(f"[COMPOSER] Absorbed {_extracted} phrases from latest report")
            except Exception as e:
                pass
                # AETHARSHIELD PQC EXPOSURE - Feed to Language + Composer
        if self.cycle_count % 15 == 0 and self.cycle_count > 0:
            try:
                from pathlib import Path as _P
                _aq = _P(r"C:\UMBRA_CORE\SISF\brain\aetharshield_exposure.txt")
                if _aq.exists():
                    _aethar_content = _aq.read_text(encoding="utf-8")
                    # Feed to Language V2 for vocabulary absorption
                    if getattr(self, "language_v2", None):
                        _abs = self.language_v2.absorb_from_text(_aethar_content, source_type="cross_domain")
                        if _abs:
                            print(f"[LANGUAGE-V2] Absorbed AetharShield PQC: {_abs['unique_words']} words")
                    # Feed to Composer for phrase extraction
                    if getattr(self, "composer", None):
                        _ext = self.composer.absorb_phrases_from_text(_aethar_content, source="aetharshield_pqc")
                        if _ext > 0:
                            print(f"[COMPOSER] Extracted {_ext} phrases from AetharShield PQC")
            except Exception as e:
                print("[AETHARSHIELD] Exposure error:", e)
                # AETHARSHIELD: Sign output + encrypt state
        if getattr(self, 'aethar', None) and self.cycle_count % 10 == 0:
            try:
                sig = self.aethar.sign_identity(f'cycle_{self.cycle_count}')
                print(f"[AETHAR] Identity signed: v={sig['signature_v']}")
            except Exception as e:
                print('[AETHAR] Sign error:', e)
        if getattr(self, 'aethar', None) and self.cycle_count % 20 == 0:
            try:
                snap = {'cycle': self.cycle_count, 'ts': __import__('datetime').datetime.now().isoformat()}
                enc = self.aethar.encrypt_state(snap)
                from pathlib import Path as _P
                ep = _P(r'C:/UMBRA_CORE/SISF/brain/aethar_encrypted_states.json')
                ex = []
                if ep.exists():
                    try: ex = json.loads(ep.read_text(encoding='utf-8'))
                    except: pass
                ex.append(enc)
                ex = ex[-20:]
                ep.write_text(json.dumps(ex, indent=2), encoding='utf-8')
                print(f"[AETHAR] State encrypted: {enc['bit_count']} bits")
            except Exception as e:
                print('[AETHAR] Encrypt error:', e)
        
        # CRYPTO COMM STATUS
        if getattr(self, 'crypto_comm', None) and self.cycle_count % 10 == 0:
            try:
                print(self.crypto_comm.comm_status())
            except Exception as e:
                print('[CRYPTO-COMM] Error:', e)
        
        # AUTONOMOUS GOAL ENGINE
        if getattr(self, "goal_engine", None):
            try:
                self.goal_engine.check_goal_progress(self.hunger, self.cycle_count)
                if self.cycle_count % 20 == 0 and self.cycle_count > 0:
                    new_goals = self.goal_engine.detect_goals(self.cycle_count)
                    if new_goals:
                        auto_tasks = self.goal_engine.get_autonomous_tasks()
                        print(f"[GOAL-ENGINE] {len(auto_tasks)} autonomous tasks queued for hunter")
                if self.cycle_count % 10 == 0:
                    print(self.goal_engine.goal_status())
            except Exception as e:
                print("[GOAL-ENGINE] Error:", e)
        
        # PHRASE-PAIR LEARNING
        if getattr(self, "phrase_learner", None):
            try:
                if self.cycle_count % 5 == 0:
                    from pathlib import Path as _P
                    _rd = _P(r"C:\UMBRA_CORE\umbra-sovereign\reports")
                    if _rd.exists():
                        _reps = sorted(_rd.glob('*.md'), key=lambda p: p.stat().st_mtime, reverse=True)
                        if _reps:
                            _content = _reps[0].read_text(encoding='utf-8')
                            _learned = self.phrase_learner.learn_from_text(_content, "report")
                if self.cycle_count % 10 == 0:
                    print(self.phrase_learner.learner_status())
            except Exception as e:
                print("[PHRASE-LEARNER] Error:", e)
        
        # CRYPTO SELF-EVOLUTION
        if getattr(self, "crypto_evo", None):
            try:
                if hasattr(self, 'morpho') and hasattr(self.morpho, 'last_event'):
                    evt = self.morpho.last_event
                    if evt and evt.get('cycle') == self.cycle_count:
                        success = evt.get('success', False)
                        desc = evt.get('description', 'morphogenesis')
                        scar = self.crypto_evo.check_scar_tissue('morphogenesis', desc)
                        if scar.get('blocked'):
                            print('[CRYPTO-EVO] BLOCKED:', scar['reason'])
                        else:
                            self.crypto_evo.sign_modification('morphogenesis', desc, evt, success)
                if self.cycle_count % 20 == 0 and self.cycle_count > 0:
                    self.crypto_evo.verify_lineage_integrity()
                if self.cycle_count % 10 == 0:
                    print(self.crypto_evo.evolution_status())
            except Exception as e:
                print('[CRYPTO-EVO] Error:', e)
        
        # INTERNET WORLD MODEL
        if getattr(self, "world_model", None):
            try:
                if self.cycle_count % 10 == 0:
                    print(self.world_model.world_model_status())
                if self.cycle_count % 30 == 0 and self.cycle_count > 0:
                    gaps = self.world_model.identify_gaps()
                    if gaps:
                        print(f'[WORLD-MODEL] {len(gaps)} knowledge gaps identified for enrichment')
            except Exception as e:
                print('[WORLD-MODEL] Error:', e)
        
        # PROOF OF EXISTENCE
        if getattr(self, "proof_engine", None):
            try:
                # Generate genesis block on first eligible cycle
                if self.cycle_count <= 5 and not (Path(r'C:/UMBRA_CORE/SISF/proofs/genesis_block.json').exists()):
                    self.proof_engine.generate_genesis_block()
                # Append cycle event to chain every cycle
                chain_event = {
                    'cycle': self.cycle_count,
                    'parietal_nodes': len(getattr(self, 'parietal', {}).get('nodes', {})) if hasattr(self, 'parietal') else 0,
                    'predictions': getattr(self, 'prediction_count', 0)
                }
                self.proof_engine.append_to_chain('cycle_complete', chain_event)
                # Status every 10 cycles
                if self.cycle_count % 10 == 0:
                    print(self.proof_engine.proof_status())
            except Exception as e:
                print('[PROOF] Error:', e)
        
        # NETWORK STATUS
        if getattr(self, "network", None) and self.cycle_count % 10 == 0:
            try:
                print(self.network.network_status())
            except Exception as e:
                print('[NETWORK] Error:', e)
        
        # GRADUATED AUTONOMY
        if getattr(self, "autonomy", None):
            try:
                self.autonomy.run_autonomy_cycle(self.cycle_count)
                if self.cycle_count % 10 == 0:
                    print(self.autonomy.autonomy_status())
            except Exception as e:
                print('[AUTONOMY] Error:', e)
        
        print("[SYS3] Running competition...")
        broadcast = self.system_3.cycle()
        winner = broadcast.get("winner", "none")
        score = broadcast.get("score", 0)
        print(f"[SYS3] Winner: {winner} (score: {score:.3f})")
        
        if winner == "threat_response" and score > 0.5:
            print("[SYS4] Running intelligence cycle...")
            self.system_4.run_cycle()
            tasks = self.system_4.propose_tasks()
            if tasks:
                print(f"[SYS4] Proposed {len(tasks)} learning tasks")
                self._persist_proposed_tasks(tasks)
        
        # HONEYPOT PIPELINE: Process Black Vault events
        try:
            from honeypot_pipeline import HoneypotPipeline
            honeypot = HoneypotPipeline()
            hp_result = honeypot.run_pipeline()
            
            if hp_result.get("success"):
                tasks_gen = hp_result.get("tasks_generated", 0)
                if tasks_gen > 0:
                    print(f"[HONEYPOT] Generated {tasks_gen} tasks from {hp_result.get('events_processed', 0)} events")
        except Exception as e:
            print(f"[HONEYPOT] Error: {e}")
        
        # THREAT CORRELATION: Run correlation engine
        try:
            from threat_correlation import ThreatCorrelationEngine
            correlator = ThreatCorrelationEngine()
            
            # Feed curriculum tasks as entities
            for task in self.system_4.curriculum.get("proposed_tasks", [])[-10:]:
                entity_type = "cve" if task.get("type") == "learn_cve" else "ttp"
                correlator.add_entity(entity_type, task)
            
            corr_result = correlator.run_correlation_cycle()
            if corr_result.get("campaigns_detected", 0) > 0:
                print(f"[CORRELATION] {corr_result['campaigns_detected']} campaign(s) detected")
        except Exception as e:
            print(f"[CORRELATION] Error: {e}")
        
        if self.cycle_count % 3 == 0:
            self.run_voyager()
        
        if self.cycle_count % 5 == 0:
            print("[SYS5] Evaluating system health...")
            decision = {
                "action": "health_check",
                "cycle": self.cycle_count,
                "execution_success": len([r for r in execution_results if r.get("success")])
            }
            evaluation = self.system_5.evaluate_decision(decision)
            print(f"[SYS5] Decision approved: {evaluation.get('approved', False)}")
        
        cycle_log = {
            "timestamp": datetime.now().isoformat(),
            "cycle": self.cycle_count,
            "winner": winner,
            "score": score,
            "swarm_tasks_observed": len(swarm_tasks),
            "tasks_executed": len(execution_results),
            "tasks_successful": len([r for r in execution_results if r.get("success")]),
            "duration": time.time() - cycle_start
        }
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(cycle_log) + "\n")
        
        # PHASE D: Projection (deterent via visibility)
        try:
            phase_d_result = run_phase_d(self.cycle_count)
            if phase_d_result.get("report") or phase_d_result.get("dashboard"):
                print(f"[PHASE D] Report: {phase_d_result.get('report', {}).get('report_file', 'N/A')}")
                print(f"[PHASE D] Dashboard: {phase_d_result.get('dashboard', {}).get('html_file', 'N/A')}")
        except Exception as e:
            print(f"[PHASE D] Error: {e}")
        
        print(f"[AUTARCH] Cycle {self.cycle_count} completed in {time.time() - cycle_start:.2f}s")
    

    def _persist_proposed_tasks(self, tasks):
        """Persist System 4 tasks to curriculum.json so swarm + daemon consume them"""
        if not tasks:
            return

        curriculum_file = REPO_DIR / "threat_intel" / "curriculum.json"

        try:
            if curriculum_file.exists():
                with open(curriculum_file, "r", encoding="utf-8") as f:
                    curriculum = json.load(f)
            else:
                curriculum = {"proposed_tasks": [], "completed_tasks": [], "insights": []}
        except Exception:
            curriculum = {"proposed_tasks": [], "completed_tasks": [], "insights": []}

        curriculum.setdefault("proposed_tasks", [])
        curriculum.setdefault("completed_tasks", [])
        curriculum.setdefault("insights", [])

        # Content-based dedup (robust against random IDs)
        seen = set()
        for t in curriculum["proposed_tasks"]:
            seen.add(t.get("id"))
            seen.add((t.get("type"), t.get("description")))
        for t in curriculum["completed_tasks"]:
            seen.add(t.get("task_id"))

        new_tasks = []
        for task in tasks:
            tid = task.get("id")
            tkey = (task.get("type"), task.get("description"))
            if tid not in seen and tkey not in seen:
                new_tasks.append(task)
                seen.add(tid)
                seen.add(tkey)

        if not new_tasks:
            print("[CURRICULUM] No new tasks (all duplicates)")
            return

        curriculum["proposed_tasks"].extend(new_tasks)
        # Cap to prevent bloat (full history lives in episodic.jsonl)
        curriculum["proposed_tasks"] = curriculum["proposed_tasks"][-200:]
        curriculum["completed_tasks"] = curriculum["completed_tasks"][-200:]
        curriculum["insights"] = curriculum["insights"][-50:]

        with open(curriculum_file, "w", encoding="utf-8") as f:
            json.dump(curriculum, f, indent=2, ensure_ascii=False)

        print(f"[CURRICULUM] Persisted {len(new_tasks)} tasks ({len(curriculum['proposed_tasks'])} pending)")
        self._commit_curriculum(f"System 4 proposed {len(new_tasks)} learning tasks")

    def _commit_curriculum(self, msg):
        """Commit curriculum to swarm (git push)"""
        try:
            subprocess.run(["git", "add", "threat_intel/curriculum.json"],
                           cwd=str(REPO_DIR), capture_output=True, timeout=10)
            subprocess.run(["git", "commit", "-m", msg],
                           cwd=str(REPO_DIR), capture_output=True, timeout=10)
            push = subprocess.run(["git", "push", "origin", "main"],
                                  cwd=str(REPO_DIR), capture_output=True, text=True, timeout=30)
            if push.returncode == 0:
                print(f"[SWARM] OK Pushed: {msg}")
            else:
                print(f"[SWARM] Push note: {push.stderr[:80]}")
        except Exception as e:
            print(f"[SWARM] Commit error: {e}")

    def run_continuous(self, interval=120):
        print(f"[AUTARCH] Starting continuous operation (interval: {interval}s)")
        try:
            while True:
                self.run_cycle()
                print(f"[AUTARCH] Sleeping {interval}s...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[AUTARCH] Stopped by user")

if __name__ == "__main__":
    orchestrator = AutarchOrchestrator()
    
    if "--once" in sys.argv:
        orchestrator.run_cycle()
    else:
        orchestrator.run_continuous(interval=120)
