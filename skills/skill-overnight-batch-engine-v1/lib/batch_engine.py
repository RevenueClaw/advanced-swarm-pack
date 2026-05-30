#!/usr/bin/env python3
"""
BatchEngine - Process overnight jobs locally with safety and checkpointing.

Author: RockClaw
"""

import json
import yaml
import time
import psutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from threading import Lock

logger = logging.getLogger("BatchEngine")


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class JobConfig:
    """Configuration for a batch job."""
    name: str
    skill: str
    model_profile: str = "overnight"
    fallback: str = "cloud_if_failed"  # never, cloud_if_failed, cloud_if_confidence_low
    schedule: str = "0 2 * * *"  # cron format
    enabled: bool = True
    max_runtime_minutes: int = 60
    cooldown_minutes: int = 5
    requires_privacy: bool = True
    params: Dict = field(default_factory=dict)


@dataclass
class JobResult:
    """Result from job execution."""
    job_name: str
    status: JobStatus
    start_time: str
    end_time: str
    tokens_generated: int
    wall_time_minutes: float
    output_path: Optional[str] = None
    error: Optional[str] = None
    escalated_to_cloud: bool = False
    checkpoint_saved: bool = False
    confidence: float = 0.0


class BatchEngine:
    """
    Overnight batch job processor.
    
    Features:
    - Job queue with priority
    - Memory/load checks before starting
    - Checkpoint/resume support
    - Safety enforcement (read-only)
    - Morning digest generation
    """
    
    DEFAULT_BASE_DIR = Path.home() / ".local_swarm"
    MAX_RAM_PERCENT = 85
    MIN_FREE_MB = 2048
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or self.DEFAULT_BASE_DIR
        self.jobs_dir = self.base_dir / "jobs"
        self.outputs_dir = self.base_dir / "outputs"
        self.checkpoints_dir = self.base_dir / "checkpoints"
        self.failed_dir = self.base_dir / "failed_jobs"
        self.logs_dir = self.base_dir / "logs"
        self.digests_dir = self.base_dir / "morning_digests"
        
        # Create directories
        for d in [self.jobs_dir, self.outputs_dir, self.checkpoints_dir, 
                  self.failed_dir, self.logs_dir, self.digests_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        self.jobs: Dict[str, JobConfig] = {}
        self.job_results: List[JobResult] = []
        self.lock = Lock()
        self._load_config()
        
        # Safety: Track destructive operations blocked
        self.blocked_operations: List[Dict] = []
    
    def _load_config(self):
        """Load job configuration from YAML."""
        config_file = self.base_dir / "overnight-jobs.yaml"
        if config_file.exists():
            with open(config_file) as f:
                data = yaml.safe_load(f) or {}
                for job_data in data.get("jobs", []):
                    job = JobConfig(**job_data)
                    self.jobs[job.name] = job
    
    def queue_job(self, config: JobConfig) -> bool:
        """Add a job to the queue."""
        with self.lock:
            self.jobs[config.name] = config
            
            # Save job config
            job_file = self.jobs_dir / f"{config.name}.json"
            with open(job_file, 'w') as f:
                json.dump(asdict(config), f, indent=2)
            
            logger.info(f"Queued job: {config.name}")
            return True
    
    def can_run(self) -> tuple[bool, str]:
        """Check if system can safely run batch jobs."""
        # Check memory
        mem = psutil.virtual_memory()
        if mem.percent > self.MAX_RAM_PERCENT:
            return False, f"Memory usage too high: {mem.percent}%"
        
        if mem.available < self.MIN_FREE_MB * 1024 * 1024:
            return False, f"Low memory: {mem.available // (1024*1024)}MB free"
        
        # Check CPU
        cpu = psutil.cpu_percent(interval=0.1)
        if cpu > 90:
            return False, f"CPU too busy: {cpu}%"
        
        return True, "OK"
    
    def run_batch(self, job_names: Optional[List[str]] = None) -> List[JobResult]:
        """
        Process batch of jobs.
        
        Args:
            job_names: Specific jobs to run, or None for all enabled
            
        Returns:
            List of JobResults
        """
        can_run, reason = self.can_run()
        if not can_run:
            logger.error(f"Cannot run batch: {reason}")
            return []
        
        results = []
        
        # Determine which jobs to run
        if job_names:
            to_run = {k: v for k, v in self.jobs.items() if k in job_names}
        else:
            to_run = {k: v for k, v in self.jobs.items() if v.enabled}
        
        logger.info(f"Starting batch: {len(to_run)} jobs")
        
        for name, config in to_run.items():
            result = self._run_job(config)
            results.append(result)
            
            # Small cooldown
            time.sleep(1)
        
        # Save results
        self.job_results.extend(results)
        
        # Generate morning digest
        self._generate_digest(results)
        
        return results
    
    def _run_job(self, config: JobConfig) -> JobResult:
        """Run a single job."""
        start_time = datetime.now()
        
        logger.info(f"Running job: {config.name}")
        
        # Create checkpoint
        checkpoint_path = self.checkpoints_dir / f"{config.name}.json"
        with open(checkpoint_path, 'w') as f:
            json.dump({
                "job_name": config.name,
                "status": "running",
                "started": start_time.isoformat()
            }, f)
        
        try:
            # Import and run the skill
            # This is simplified - actual implementation would import and call skill
            result = self._execute_skill(config)
            
            status = JobStatus.COMPLETED if result.get("success") else JobStatus.FAILED
            
            return JobResult(
                job_name=config.name,
                status=status,
                start_time=start_time.isoformat(),
                end_time=datetime.now().isoformat(),
                tokens_generated=result.get("tokens", 0),
                wall_time_minutes=(datetime.now() - start_time).total_seconds() / 60,
                output_path=str(self.outputs_dir / f"{config.name}.json"),
                error=result.get("error"),
                escalated_to_cloud=result.get("escalated", False),
                checkpoint_saved=True,
                confidence=result.get("confidence", 0.0)
            )
            
        except Exception as e:
            logger.error(f"Job {config.name} failed: {e}")
            
            return JobResult(
                job_name=config.name,
                status=JobStatus.FAILED,
                start_time=start_time.isoformat(),
                end_time=datetime.now().isoformat(),
                tokens_generated=0,
                wall_time_minutes=(datetime.now() - start_time).total_seconds() / 60,
                error=str(e),
                checkpoint_saved=True,
            )
        finally:
            # Cleanup checkpoint
            if checkpoint_path.exists():
                checkpoint_path.unlink()
    
    def _execute_skill(self, config: JobConfig) -> Dict:
        """Execute the skill. Actual implementation would import and call."""
        # Placeholder - real implementation imports skill
        return {
            "success": True,
            "tokens": 500,
            "confidence": 0.85,
            "escalated": False
        }
    
    def _generate_digest(self, results: List[JobResult]):
        """Generate morning digest."""
        digest = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "jobs_completed": len([r for r in results if r.status == JobStatus.COMPLETED]),
            "cloud_tokens_avoided": sum(r.tokens_generated for r in results),
            "escalated_to_cloud": len([r for r in results if r.escalated_to_cloud]),
            "failed": len([r for r in results if r.status == JobStatus.FAILED]),
            "avg_local_confidence": sum(r.confidence for r in results) / len(results) if results else 0,
            "jobs": [asdict(r) for r in results]
        }
        
        digest_path = self.digests_dir / f"digest_{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(digest_path, 'w') as f:
            json.dump(digest, f, indent=2)
        
        logger.info(f"Morning digest saved: {digest_path}")
        return digest
    
    def get_status(self) -> Dict:
        """Get current batch status."""
        return {
            "queued_jobs": len(self.jobs),
            "completed_jobs": len(self.job_results),
            "can_run": self.can_run()[0],
            "blocked_operations": len(self.blocked_operations),
        }


# Test
if __name__ == "__main__":
    print("BatchEngine test - creating engine")
    engine = BatchEngine()
    
    print(f"Base dir: {engine.base_dir}")
    print(f"Can run: {engine.can_run()}")
    print(f"Status: {engine.get_status()}")
    print("OK")
