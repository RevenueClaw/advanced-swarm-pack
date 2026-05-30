#!/usr/bin/env python3
"""
Job Queue - Simple persistent queue for batch jobs.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class QueuedJob:
    """A job in the queue."""
    name: str
    skill: str
    profile: str
    params: Dict
    priority: int = 10
    created_at: str = ""
    status: str = "pending"
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.strftime("%Y-%m-%dT%H:%M:%S")


class JobQueue:
    """Persistent job queue with priorities."""
    
    def __init__(self, queue_dir: Path):
        self.queue_dir = queue_dir
        self.queue_dir.mkdir(parents=True, exist_ok=True)
    
    def enqueue(self, job: QueuedJob, priority: int = 10) -> bool:
        """Add job to queue."""
        job_file = self.queue_dir / f"{priority:02d}_{job.name}_{int(time.time())}.json"
        with open(job_file, 'w') as f:
            json.dump(asdict(job), f, indent=2)
        return True
    
    def dequeue(self) -> Optional[QueuedJob]:
        """Get highest priority job."""
        # Find lowest priority number (highest priority)
        job_files = sorted(self.queue_dir.glob("*.json"))
        if not job_files:
            return None
        
        job_file = job_files[0]
        with open(job_file) as f:
            data = json.load(f)
        
        # Remove from queue
        job_file.unlink()
        
        return QueuedJob(**data)
    
    def peek(self, n: int = 5) -> List[QueuedJob]:
        """Preview next N jobs without removing."""
        job_files = sorted(self.queue_dir.glob("*.json"))[:n]
        jobs = []
        for job_file in job_files:
            with open(job_file) as f:
                data = json.load(f)
            jobs.append(QueuedJob(**data))
        return jobs
    
    def size(self) -> int:
        """Return queue size."""
        return len(list(self.queue_dir.glob("*.json")))
    
    def clear(self):
        """Clear all jobs."""
        for job_file in self.queue_dir.glob("*.json"):
            job_file.unlink()


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        queue = JobQueue(Path(d) / "queue")
        
        # Test enqueue
        queue.enqueue(QueuedJob("test1", "skill-test", "fast", {}))
        queue.enqueue(QueuedJob("test2", "skill-test", "fast", {}))
        print(f"Queue size: {queue.size()}")
        
        # Test dequeue
        job = queue.dequeue()
        print(f"Dequeued: {job.name}")
        print(f"Remaining: {queue.size()}")
