#!/usr/bin/env python3
"""
Health Monitor - System health checks for local LLM workloads.

Monitors:
- Model server health
- System memory pressure
- CPU load
- Temperature (if available)
- Response latency
"""

import time
import psutil
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass
class HealthSnapshot:
    """Snapshot of system health."""
    timestamp: str
    cpu_percent: float
    memory_available_mb: int
    memory_percent: float
    temperature_c: Optional[float]
    disk_free_gb: float
    healthy: bool
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class HealthMonitor:
    """Monitor system health for local LLM operations."""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".openclaw/logs/health-monitor"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.warnings: List[str] = []
    
    def get_system_health(self) -> HealthSnapshot:
        """Get current system health snapshot."""
        self.warnings = []
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 85:
            self.warnings.append(f"High CPU: {cpu_percent}%")
        
        # Memory
        mem = psutil.virtual_memory()
        memory_available_mb = mem.available // (1024 * 1024)
        memory_percent = mem.percent
        if memory_percent > 85:
            self.warnings.append(f"High memory usage: {memory_percent}%")
        
        # Temperature (Linux only)
        temperature = None
        try:
            temp = psutil.sensors_temperatures()
            if 'cpu_thermal' in temp:
                temperature = temp['cpu_thermal'][0].current
        except Exception:
            pass
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_free_gb = disk.free / (1024**3)
        if disk_free_gb < 5:
            self.warnings.append(f"Low disk space: {disk_free_gb:.1f}GB free")
        
        healthy = len(self.warnings) == 0
        
        return HealthSnapshot(
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
            cpu_percent=cpu_percent,
            memory_available_mb=memory_available_mb,
            memory_percent=memory_percent,
            temperature_c=temperature,
            disk_free_gb=disk_free_gb,
            healthy=healthy,
            warnings=self.warnings.copy()
        )
    
    def can_run_local_model(self, min_memory_mb: int = 2048) -> bool:
        """Check if system has resources to run local model."""
        health = self.get_system_health()
        
        if health.memory_available_mb < min_memory_mb:
            return False
        
        if health.memory_percent > 90:
            return False
        
        if health.cpu_percent > 95:
            return False
        
        return True
    
    def log_health(self, health: HealthSnapshot):
        """Log health snapshot."""
        log_file = self.log_dir / f"health_{time.strftime('%Y-%m')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(health.to_dict()) + '\n')


if __name__ == "__main__":
    import json
    monitor = HealthMonitor()
    health = monitor.get_system_health()
    print(json.dumps(health.to_dict(), indent=2))
    print(f"\nCan run local model: {monitor.can_run_local_model()}")
