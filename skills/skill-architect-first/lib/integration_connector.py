#!/usr/bin/env python3
"""
Integration Connector - Phase 3: Connect Architect-First to existing systems.

Connects to:
- HITL (skill-hitl): Escalation on low-confidence plans
- Versioning (skill-versioning): Plan versioning like skills
- Preference Learning (skill-preference-learning): User planning style

Author: RockClaw
Version: 1.0.0-alpha
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import asdict

# Add paths for other skills
sys.path.insert(0, str(Path.home() / ".openclaw/workspace/skills/skill-versioning/lib"))
sys.path.insert(0, str(Path.home() / ".openclaw/workspace/skills/skill-preference-learning/lib"))

try:
    from version_manager import SkillVersionManager, VersionStatus
    VERSIONING_AVAILABLE = True
except ImportError:
    VERSIONING_AVAILABLE = False

try:
    from preference_engine import PreferenceEngine
    PREFERENCE_AVAILABLE = True
except ImportError:
    PREFERENCE_AVAILABLE = False


class ArchitectFirstIntegrations:
    """
    Connects Architect-First planning to existing swarm systems.
    """
    
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.version_manager = None
        self.preference_engine = None
        
        if VERSIONING_AVAILABLE:
            self.version_manager = SkillVersionManager("architect-plans")
        
        if PREFERENCE_AVAILABLE:
            try:
                self.preference_engine = PreferenceEngine(user_id)
            except Exception as e:
                print(f"PreferenceEngine init failed: {e}")
    
    def should_escalate_to_human(self, reviewed_plan: Any) -> tuple[bool, str]:
        """Determine if plan should escalate to human via HITL."""
        if reviewed_plan.scores.overall < 60:
            return True, f"Plan scored {reviewed_plan.scores.overall}/100 - below threshold"
        
        critical_count = sum(1 for c in reviewed_plan.critiques if c.severity == "critical")
        if critical_count >= 2:
            return True, f"{critical_count} critical issues require human judgment"
        
        if reviewed_plan.execution_confidence < 0.5:
            return True, f"Execution confidence {reviewed_plan.execution_confidence:.0%} too low"
        
        return False, "Plan acceptable for automated execution"
    
    def format_hitl_request(self, reviewed_plan: Any, task_description: str) -> Dict[str, Any]:
        """Format a HITL request for human review of a plan."""
        critiques_summary = [f"[{c.severity.upper()}] {c.category}: {c.issue}" 
                            for c in reviewed_plan.critiques[:5]]
        
        return {
            "type": "plan_review",
            "priority": "normal" if reviewed_plan.scores.overall >= 50 else "urgent",
            "task": task_description,
            "plan_score": reviewed_plan.scores.overall,
            "execution_confidence": reviewed_plan.execution_confidence,
            "critiques": critiques_summary,
            "acceptance_criteria": reviewed_plan.acceptance_criteria.must_satisfy,
            "recommendation": "PROCEED" if reviewed_plan.recommend_proceed else "REVISION",
            "question_for_human": self._generate_human_question(reviewed_plan),
            "options": [
                "APPROVE - Proceed with automated execution",
                "REVISE - Request plan revision",
                "OVERRIDE - Proceed despite concerns",
                "ESCALATE - Hand to different team"
            ]
        }
    
    def _generate_human_question(self, reviewed_plan: Any) -> str:
        """Generate specific question for human based on review."""
        if reviewed_plan.scores.overall < 50:
            return "This plan has significant gaps. Please review or provide guidance."
        elif reviewed_plan.scores.risk_assessment < 60:
            return "Risk assessment incomplete. Should we proceed?"
        elif not reviewed_plan.recommend_proceed:
            return "Automated review does not recommend proceeding. Your decision?"
        return "Review complete. Approve for execution?"
    
    def version_plan(self, plan_name: str, reviewed_plan: Any, 
                     metadata: Optional[Dict] = None) -> Optional[str]:
        """Version a reviewed plan like a skill."""
        if not self.version_manager:
            print("Versioning not available - skipping plan versioning")
            return None
        
        base_path = Path.home() / f".openclaw/architect-plans/{plan_name}"
        version = self._calculate_version(reviewed_plan)
        version_path = base_path / f"v{version}"
        version_path.mkdir(parents=True, exist_ok=True)
        
        plan_data = {
            "plan_name": plan_name,
            "version": version,
            "scores": {
                "overall": reviewed_plan.scores.overall,
                "clarity": reviewed_plan.scores.clarity,
                "risk_assessment": reviewed_plan.scores.risk_assessment,
                "completeness": reviewed_plan.scores.completeness,
                "feasibility": reviewed_plan.scores.feasibility,
                "testability": reviewed_plan.scores.testability,
            },
            "recommend_proceed": reviewed_plan.recommend_proceed,
            "reviewed_at": reviewed_plan.reviewed_at,
            "metadata": metadata or {}
        }
        
        with open(version_path / "plan.json", "w") as f:
            json.dump(plan_data, f, indent=2)
        
        try:
            status = VersionStatus.PRODUCTION if reviewed_plan.recommend_proceed else VersionStatus.DEVELOPMENT
            self.version_manager.register_version(version=version, path=version_path, status=status)
        except Exception as e:
            print(f"Version registration: {e}")
        
        return version
    
    def _calculate_version(self, reviewed_plan: Any) -> str:
        """Generate semantic version from plan score."""
        import datetime
        
        score = reviewed_plan.scores.overall
        if score >= 90:
            major, minor = "1", "0"
        elif score >= 70:
            major, minor = "0", "1"
        else:
            major, minor = "0", "0"
        
        patch = datetime.datetime.now().strftime("%Y%m%d%H%M")
        return f"{major}.{minor}.{patch}"
    
    def learn_planning_preference(self, task_type: str, mode_used: str, 
                                   success: bool, user_feedback: Optional[str] = None):
        """Learn from planning outcomes (placeholder for full integration)."""
        print(f"   [Learning: {task_type} using {mode_used} -> success={success}]")
        
        if user_feedback:
            if "too much planning" in user_feedback.lower():
                print(f"   [Preference: User prefers less overhead]")
            elif "should have planned more" in user_feedback.lower():
                print(f"   [Preference: User prefers thorough planning]")
    
    def get_user_planning_style(self) -> Dict[str, Any]:
        """Get learned planning preferences for user."""
        return {
            "available": PREFERENCE_AVAILABLE,
            "overhead_tolerance": "medium",
            "default_mode": "standard"
        }


def create_integrations(user_id: str = "shayne") -> ArchitectFirstIntegrations:
    """Factory function to create integrations."""
    return ArchitectFirstIntegrations(user_id)


if __name__ == "__main__":
    print("Architect-First Integrations loaded successfully")
