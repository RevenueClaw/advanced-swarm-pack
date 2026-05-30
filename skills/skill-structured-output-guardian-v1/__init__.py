"""
skill-structured-output-guardian-v1 - Reliable JSON from local models.

v1.4.0 Local Intelligence & Cost Optimization

Usage:
    from skill_structured_output_guardian import OutputGuardian
    from pydantic import BaseModel
    
    class MyResult(BaseModel):
        title: str
        confidence: float
    
    guardian = OutputGuardian()
    result = guardian.generate_and_validate(
        prompt="Extract...",
        schema=MyResult,
        model_profile="fast"
    )
"""

__version__ = "1.0.0"
__author__ = "RockClaw"

from .lib.output_guardian import OutputGuardian, ValidationResult, EscalationTrigger
from .lib.schemas import LocalTaskResult, EvidencePack, TaskClassification

__all__ = [
    "OutputGuardian",
    "ValidationResult",
    "EscalationTrigger",
    "LocalTaskResult",
    "EvidencePack",
    "TaskClassification",
]
