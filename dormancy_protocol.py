#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTARCH Dormancy Protocol
Resource discipline: System 1 + 5 always-on, others sleep when RAM > 90%
"""

import psutil
import time
from pathlib import Path

RAM_THRESHOLD = 90.0  # Percent
DORMANCY_LOG = Path(r"C:\UMBRA_CORE\autarch\dormancy_log.jsonl")

class DormancyProtocol:
    """Resource-aware dormancy system"""
    
    def __init__(self):
        self.systems_status = {
            "system_1": "always_on",
            "system_2": "active",
            "system_3": "active",
            "system_4": "active",
            "system_5": "always_on"
        }
    
    def check_resource_pressure(self):
        """Check RAM and CPU pressure"""
        ram_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent()
        
        return {
            "ram_percent": ram_percent,
            "cpu_percent": cpu_percent,
            "ram_available_mb": (100 - ram_percent) * 80,  # 8GB total
            "pressure_high": ram_percent > RAM_THRESHOLD
        }
    
    def activate_dormancy(self):
        """Activate dormancy protocol"""
        pressure = self.check_resource_pressure()
        
        if pressure["pressure_high"]:
            print(f"[DORMANCY] HIGH PRESSURE: RAM {pressure['ram_percent']:.1f}%")
            print(f"[DORMANCY] Activating protocol...")
            
            # System 4 sleeps (heaviest)
            self.systems_status["system_4"] = "dormant"
            print(f"[DORMANCY] System 4 (Intelligence): DORMANT")
            
            # System 3 reduces frequency
            self.systems_status["system_3"] = "reduced"
            print(f"[DORMANCY] System 3 (Control): REDUCED FREQUENCY")
            
            # System 1 + 5 stay always-on
            print(f"[DORMANCY] System 1 (Ops): ALWAYS-ON")
            print(f"[DORMANCY] System 5 (Policy): ALWAYS-ON")
            
            return True
        else:
            # Wake up dormant systems
            if self.systems_status["system_4"] == "dormant":
                self.systems_status["system_4"] = "active"
                print(f"[DORMANCY] System 4: AWAKE")
            
            if self.systems_status["system_3"] == "reduced":
                self.systems_status["system_3"] = "active"
                print(f"[DORMANCY] System 3: NORMAL")
            
            return False
    
    def get_system_status(self, system_name):
        """Get status of a system"""
        return self.systems_status.get(system_name, "unknown")
    
    def should_run_system(self, system_name):
        """Check if system should run"""
        status = self.get_system_status(system_name)
        return status in ["always_on", "active"]

if __name__ == "__main__":
    protocol = DormancyProtocol()
    
    print("Resource pressure check:")
    pressure = protocol.check_resource_pressure()
    print(f"  RAM: {pressure['ram_percent']:.1f}%")
    print(f"  CPU: {pressure['cpu_percent']:.1f}%")
    print(f"  Available: {pressure['ram_available_mb']:.0f}MB")
    
    print(f"\nDormancy needed: {protocol.activate_dormancy()}")
