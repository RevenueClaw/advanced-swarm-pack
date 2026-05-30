"""
skill-overnight-batch-engine-v1 - Queue and process overnight batch jobs.

v1.4.0 Local Intelligence & Cost Optimization

Usage:
    from skill_overnight_batch_engine import BatchEngine
    
    engine = BatchEngine()
    engine.queue_job(
        name="newsletter_digest",
        skill="skill-newsletter-processor",
        model_profile="overnight"
    )
    engine.run_batch()
"""

__version__ = "1.0.0"
__author__ = "RockClaw"

from .lib.batch_engine import BatchEngine, JobConfig, JobResult
from .lib.job_queue import JobQueue, JobStatus
from .lib.morning_digest import MorningDigestGenerator

__all__ = [
    "BatchEngine",
    "JobConfig",
    "JobResult",
    "JobQueue",
    "JobStatus",
    "MorningDigestGenerator",
]
