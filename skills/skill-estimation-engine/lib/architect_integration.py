#!/usr/bin/env python3
"""
Architect-First Integration - Connect estimation engine to planning system.

Author: RockClaw
Version: 1.0.0
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add paths
sys.path.insert(0, str(Path.home() / ".openclaw/workspace/skills/skill-architect-first/lib"))
sys.path.insert(0, str(Path.home() / ".openclaw/workspace/skills/skill-preference-learning/lib"))

try:
    from planning_modes import TaskProfile, RiskLevel
    ARCHITECT_AVAILABLE = True
except ImportError:
    ARCHITECT_AVAILABLE = False

try:
    from preference_engine import PreferenceEngine
    PREFERENCE_AVAILABLE = True
except ImportError:
    PREFERENCE_AVAILABLE = False


class ArchitectEstimationIntegration:
    """
    Integrates EstimationEngine with Architect-First planning.
    
    Usage:
        from estimation_engine import EstimationEngine
        from architect_integration import ArchitectEstimationIntegration
        
        engine = EstimationEngine()
        integration = ArchitectEstimationIntegration(engine, "shayne")
        
        # During planning, get estimate with Architect-First context
        estimate = integration.estimate_for_plan(
            task="Implement feature",
            draft_plan={...},
            mode="architect"
        )
    """
    
    def __init__(self, estimation_engine: Any, user_id: str = "default"):
        self.engine = estimation_engine
        self.user_id = user_id
        self.preference_engine = None
        
        if PREFERENCE_AVAILABLE:
            try:
                self.preference_engine = PreferenceEngine(user_id)
            except Exception as e:
                print(f"Preference engine init: {e}")
    
    def estimate_for_plan(self,
                          task: str,
                          draft_plan: Dict[str, Any],
                          mode: str = "standard") -> Dict[str, Any]:
        """
        Generate estimate with Architect-First context.
        
        Args:
            task: Task description
            draft_plan: The draft plan with steps
            mode: Planning mode (fast/standard/architect)
            
        Returns:
            Enhanced estimate with planning context
        """
        # Extract subtasks from plan
        steps = draft_plan.get("steps", [])
        subtasks = []
        
        for step in steps:
            if isinstance(step, dict):
                name = step.get("name", step.get("description", "Unknown"))
                hours = step.get("estimated_hours", 0.5)
            else:
                name = str(step) if len(str(step)) < 50 else str(step)[:50] + "..."
                hours = 0.5  # Default if not specified
            
            subtasks.append((name, hours))
        
        # Determine characteristics
        is_novel = mode == "architect"
        has_pattern = mode == "fast"
        
        # Get user's tolerance preference
        tolerance = self._get_tolerance_preference()
        
        # Generate estimate
        from estimation_engine import TaskCategory
        import random
        
        # Assign to category based on task
        category = TaskCategory.CODING if "code" in task.lower() else TaskCategory.UNKNOWN
        
        estimate = self.engine.estimate(
            task=task,
            subtasks=subtasks,
            category=category,
            is_novel=is_novel,
            has_similar_pattern=has_pattern
        )
        
        # Add planning context
        estimate["planning_context"] = {
            "mode": mode,
            "mode_multiplier": {"fast": 0.8, "standard": 1.0, "architect": 1.2}.get(mode, 1.0),
            "user_tolerance": tolerance,
            "recommendation": self._planning_recommendation(mode, estimate, tolerance)
        }
        
        return estimate
    
    def _get_tolerance_preference(self) -> str:
        """Get user's estimation tolerance preference."""
        if not self.preference_engine:
            return "balanced"
        
        try:
            tolerance = self.preference_engine.get_trait("planning.time_tolerance", "balanced")
            return tolerance
        except:
            return "balanced"
    
    def _planning_recommendation(self, mode: str, estimate: Dict, tolerance: str) -> str:
        """Generate planning-specific recommendation."""
        parts = []
        
        base_hours = estimate["total_estimated_hours"]
        
        # Tolerance-based adjustment
        if tolerance == "aggressive":
            parts.append("User prefers tighter estimates")
        elif tolerance == "conservative":
            parts.append("User prefers generous buffers")
        
        # Mode-specific advice
        if mode == "architect":
            if base_hours > 10:
                parts.append("Consider breaking into multiple sprints")
            parts.append("Milestone check-ins recommended")
        
        return " ".join(parts) if parts else "Proceed with estimate"
    
    def record_planning_outcome(self,
                               task_type: str,
                               estimated_hours: float,
                               actual_hours: float,
                               accuracy_satisfaction: bool = True):
        """
        Record outcome for preference learning.
        
        Used to learn user's estimation accuracy preferences.
        """
        if not self.preference_engine:
            return
        
        # Learn from actual vs predicted
        error_ratio = actual_hours / estimated_hours if estimated_hours > 0 else 1.0
        
        if error_ratio > 1.5:
            # Underestimated - user needs more buffer
            self.preference_engine.learn_trait(
                name="planning.time_tolerance",
                value="conservative",
                confidence=0.6,
                source="post_execution"
            )
        elif error_ratio < 0.7:
            # Overestimated - user prefers tighter
            self.preference_engine.learn_trait(
                name="planning.time_tolerance",
                value="aggressive",
                confidence=0.6,
                source="post_execution"
            )


def create_planning_estimate(draft_plan: Dict[str, Any], user_id: str = "shayne") -> Dict[str, Any]:
    """
    Factory function for quick estimate during planning.
    
    Usage during Architect-First planning:
        estimate = create_planning_estimate({
            "goal": "Implement X",
            "steps": [...],
        })
    """
    from estimation_engine import EstimationEngine
    
    engine = EstimationEngine()
    integration = ArchitectEstimationIntegration(engine, user_id)
    
    return integration.estimate_for_plan(
        task=draft_plan.get("goal", "Unknown task"),
        draft_plan=draft_plan,
        mode=draft_plan.get("planning_mode", "standard")
    )


if __name__ == "__main__":
    print("Architect-Estimation Integration loaded")