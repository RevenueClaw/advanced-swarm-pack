#!/usr/bin/env python3
"""
Routing Utilities - Common routing logic for v1.4.0 skills.

Provides helper functions to decide local vs cloud model routing.
"""

from typing import Dict, List, Literal, Optional, Any
from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """Task types with routing recommendations."""
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    DEDUPLICATION = "deduplication"
    TRIAGE = "triage"
    ROUTING = "routing"
    TAGGING = "tagging"
    NEWSLETTER_PROCESSING = "newsletter_processing"
    PRICE_MONITORING = "price_monitoring"
    REPORT_DRAFT = "report_draft"
    PASSIVE_CODEBASE_SCAN = "passive_codebase_scan"
    # Cloud-only tasks
    CREDENTIAL_MODIFICATION = "credential_modification"
    DESTRUCTIVE_OPERATION = "destructive_operation"
    PRODUCTION_DEPLOY = "production_deploy"
    FINANCIAL_DECISION = "financial_decision"


class RiskLevel(Enum):
    """Risk assessment for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """Task description for routing."""
    task_type: str
    risk: RiskLevel
    privacy_required: bool = False
    urgency: Literal["immediate", "normal", "overnight"] = "normal"
    estimated_tokens: int = 1000
    destructive: bool = False


class ModelRouter:
    """
    Router for selecting local vs cloud model.
    
    Follows v1.4.0 principles:
    - Local for read-only, verifiable, low-risk tasks
    - Cloud for destructive, financial, credential, uncertain tasks
    """
    
    # Task -> recommended profile mapping
    TASK_PROFILES = {
        TaskType.CLASSIFICATION: ("fast", "local"),
        TaskType.EXTRACTION: ("fast", "local"),
        TaskType.ROUTING: ("fast", "local"),
        TaskType.TAGGING: ("fast", "local"),
        TaskType.DEDUPLICATION: ("balanced", "local"),
        TaskType.TRIAGE: ("balanced", "local"),
        TaskType.SUMMARIZATION: ("balanced", "local"),  # Changed from overnight
        TaskType.NEWSLETTER_PROCESSING: ("balanced", "local"),
        TaskType.PRICE_MONITORING: ("balanced", "local"),
        TaskType.REPORT_DRAFT: ("overnight", "local"),
        TaskType.PASSIVE_CODEBASE_SCAN: ("overnight", "local"),
        TaskType.FINANCIAL_DECISION: (None, "cloud"),
        TaskType.CREDENTIAL_MODIFICATION: (None, "cloud"),
        TaskType.DESTRUCTIVE_OPERATION: (None, "cloud"),
        TaskType.PRODUCTION_DEPLOY: (None, "cloud"),
    }
    
    @classmethod
    def choose_model(cls, task: Task) -> tuple[str, str, str]:
        """
        Choose model for task.
        
        Returns: (profile, tier, reason)
        - profile: fast/balanced/overnight/cloud
        - tier: local/cloud
        - reason: explanation
        """
        # Force cloud for high-risk tasks
        if task.risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return ("cloud_leader", "cloud", f"high_risk_{task.risk.value}")
        
        if task.destructive:
            return ("cloud_leader", "cloud", "destructive_operation")
        
        # Check task type mapping
        try:
            task_enum = TaskType(task.task_type)
        except ValueError:
            task_enum = None
        
        if task_enum and task_enum in cls.TASK_PROFILES:
            profile, tier = cls.TASK_PROFILES[task_enum]
            if tier == "local":
                # Override profile for urgency
                if task.urgency == "overnight":
                    profile = "overnight"
                return (profile, tier, f"task_mapping_{task.task_type}")
            else:
                return (profile or "cloud_leader", tier, f"task_mapping_{task.task_type}")
        
        # Check urgency
        if task.urgency == "overnight":
            return ("overnight", "local", "overnight_batch")
        
        # Check privacy
        if task.privacy_required:
            return ("balanced", "local", "privacy_required")
        
        # Default
        return ("balanced", "local", "default_local_first")
    
    @classmethod
    def can_run_locally(cls, task: Task) -> bool:
        """Quick check if task can run locally."""
        profile, tier, _ = cls.choose_model(task)
        return tier == "local"


# Convenience decorators and helpers
def requires_cloud(fn):
    """Decorator to mark function as cloud-only."""
    fn._requires_cloud = True
    return fn


def allows_local(fn):
    """Decorator to mark function as local-safe."""
    fn._allows_local = True
    return fn


# Test
if __name__ == "__main__":
    from pprint import pprint
    
    test_tasks = [
        Task("classification", RiskLevel.LOW),
        Task("extraction", RiskLevel.LOW),
        Task("newsletter_processing", RiskLevel.LOW),
        Task("report_draft", RiskLevel.LOW, urgency="overnight"),
        Task("financial_decision", RiskLevel.HIGH),
        Task("passive_codebase_scan", RiskLevel.LOW, urgency="overnight"),
    ]
    
    print("Model Routing Tests:")
    for task in test_tasks:
        profile, tier, reason = ModelRouter.choose_model(task)
        print(f"  {task.task_type:30s} -> {tier:6s}/{profile:10s} ({reason})")
