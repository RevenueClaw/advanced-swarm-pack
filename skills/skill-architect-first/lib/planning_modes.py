#!/usr/bin/env python3
"""
Planning Modes - Automatic selection of planning depth based on task characteristics.

Implements tiered planning:
- FAST: Simple tasks (<2 subtasks, low risk, known pattern)
- STANDARD: Normal work (2-5 subtasks, medium risk)
- ARCHITECT_FIRST: Complex/novel/high-risk (5+ subtasks, high risk, novel)

Author: RockClaw
Version: 1.0.0-alpha
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import json


class PlanningMode(Enum):
    """Available planning modes."""
    FAST = "fast"                    # Minimal planning
    STANDARD = "standard"            # Normal planning
    ARCHITECT_FIRST = "architect"    # Heavy planning
    

class TaskComplexity(Enum):
    """Task complexity levels."""
    TRIVIAL = 1      # Single action
    SIMPLE = 2       # 1-2 steps
    MODERATE = 3     # 3-5 steps
    COMPLEX = 4      # 5+ steps or unclear
    NOVEL = 5        # Unknown territory


class RiskLevel(Enum):
    """Risk assessment levels."""
    NONE = 0         # Read-only, safe
    LOW = 1          # Low impact, easily reversible
    MEDIUM = 2       # Some impact, needs care
    HIGH = 3         # Significant impact, destructive
    CRITICAL = 4     # System/data critical


@dataclass  
class TaskProfile:
    """Profile of a task for mode selection."""
    description: str
    estimated_subtasks: int
    risk_level: RiskLevel
    is_novel: bool           # Never done this before
    has_pattern_match: bool  # Done similar before
    estimated_hours: float
    involves_external: bool  # API calls, emails, etc.
    is_destructive: bool     # Deletes, overwrites
    requires_internet: bool
    has_learned_pattern: bool  # From preference learning
    

@dataclass
class ModeDecision:
    """Decision on which planning mode to use."""
    selected_mode: PlanningMode
    confidence: float          # 0.0-1.0
    reasoning: List[str]      # Why this mode
    estimated_review_time: str  # How long planning should take
    can_skip_review: bool      # For FAST mode only
    

class ModeSelector:
    """
    Selects appropriate planning mode based on task characteristics.
    
    Usage:
        selector = ModeSelector()
        
        profile = TaskProfile(
            description="Fix typo in README",
            estimated_subtasks=1,
            risk_level=RiskLevel.LOW,
            is_novel=False,
            ...
        )
        
        decision = selector.select_mode(profile)
        # Returns FAST mode for simple, safe tasks
    """
    
    def __init__(self, preference_learning_enabled: bool = True):
        self.preference_learning_enabled = preference_learning_enabled
        
    def analyze_task(self, 
                    description: str,
                    draft_plan: Optional[Dict] = None,
                    user_preferences: Optional[Dict] = None) -> TaskProfile:
        """
        Analyze a task and build a profile.
        
        Analyzes:
        - Description keywords for risk/novelty
        - Draft plan if provided (step count, complexity)
        - User preferences for learned patterns
        """
        desc_lower = description.lower()
        
        # Estimate subtasks from description or draft
        if draft_plan and "steps" in draft_plan:
            estimated_subtasks = len(draft_plan["steps"])
        else:
            # Heuristic based on description
            estimated_subtasks = self._estimate_subtasks(description)
        
        # Assess risk
        risk_level = self._assess_risk(description, draft_plan)
        
        # Check novelty
        is_novel = self._check_novelty(description, user_preferences)
        has_pattern_match = not is_novel  # Simplified
        
        # Time estimate
        estimated_hours = self._estimate_hours(estimated_subtasks, risk_level)
        
        # External/destructive indicators
        involves_external = any(word in desc_lower for word in 
                               ["send", "email", "post", "tweet", "api", "http"])
        is_destructive = any(word in desc_lower for word in 
                            ["delete", "remove", "drop", "destroy", "overwrite"])
        requires_internet = involves_external or "web" in desc_lower
        
        # Check learned patterns
        has_learned_pattern = (user_preferences and 
                              self._check_learned_pattern(description, user_preferences))
        
        return TaskProfile(
            description=description,
            estimated_subtasks=estimated_subtasks,
            risk_level=risk_level,
            is_novel=is_novel,
            has_pattern_match=has_pattern_match,
            estimated_hours=estimated_hours,
            involves_external=involves_external,
            is_destructive=is_destructive,
            requires_internet=requires_internet,
            has_learned_pattern=has_learned_pattern
        )
    
    def _estimate_subtasks(self, description: str) -> int:
        """Estimate number of subtasks from description."""
        # Count action verbs
        action_words = ["and", "then", "also", "plus", "additionally", "next"]
        count = sum(1 for word in action_words if word in description.lower())
        
        # Look for list indicators
        if any(indic in description for indic in [",", ";", "1.", "2."]):
            count += 1
        
        return max(1, count + 1)
    
    def _assess_risk(self, description: str, draft_plan: Optional[Dict]) -> RiskLevel:
        """Assess risk level from description."""
        desc_lower = description.lower()
        
        # Critical risk words
        critical = ["reformat", "wipe", "destroy", "delete all", "reset"]
        if any(word in desc_lower for word in critical):
            return RiskLevel.CRITICAL
        
        # High risk
        high = ["delete", "remove", "drop", "overwrite", "modify production", "deploy", "production"]
        if any(word in desc_lower for word in high):
            return RiskLevel.HIGH
        
        # Medium risk
        medium = ["edit", "change", "update", "configure", "install", "restart"]
        if any(word in desc_lower for word in medium):
            return RiskLevel.MEDIUM
        
        # External actions
        if any(word in desc_lower for word in ["send", "email", "post", "tweet", "publish"]):
            return RiskLevel.MEDIUM
        
        # Check draft plan risks if provided
        if draft_plan and "risks" in draft_plan:
            if len(draft_plan["risks"]) > 2:
                return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _check_novelty(self, description: str, user_preferences: Optional[Dict]) -> bool:
        """Check if this appears to be a novel task."""
        # Simple heuristic: complex keywords suggest novelty
        complex_indicators = ["new", "implement", "create", "build", "design", "architect"]
        return any(word in description.lower() for word in complex_indicators)
    
    def _check_learned_pattern(self, description: str, user_preferences: Dict) -> bool:
        """Check if user has done similar task before."""
        # Would integrate with preference learning
        patterns = user_preferences.get("workflow_patterns", [])
        return len(patterns) > 0  # Simplified
    
    def _estimate_hours(self, subtasks: int, risk: RiskLevel) -> float:
        """Estimate hours based on subtasks and risk."""
        base = subtasks * 0.5  # 30 min per subtask
        
        if risk.value >= RiskLevel.HIGH.value:
            base *= 2.0  # Double for high risk
        elif risk.value >= RiskLevel.MEDIUM.value:
            base *= 1.5
        
        return base
    
    def select_mode(self, profile: TaskProfile) -> ModeDecision:
        """
        Select appropriate planning mode based on task profile.
        
        Logic:
        - FAST: <2 subtasks, LOW risk, has pattern, not destructive
        - ARCHITECT_FIRST: >5 subtasks, HIGH+ risk, or novel/complex
        - STANDARD: Everything else
        """
        reasoning = []
        
        # Check for FAST mode conditions
        if self._qualifies_for_fast_mode(profile, reasoning):
            return ModeDecision(
                selected_mode=PlanningMode.FAST,
                confidence=0.85,
                reasoning=reasoning,
                estimated_review_time="2-3 minutes",
                can_skip_review=True
            )
        
        # Check for ARCHITECT_FIRST conditions  
        if self._qualifies_for_architect_first(profile, reasoning):
            return ModeDecision(
                selected_mode=PlanningMode.ARCHITECT_FIRST,
                confidence=0.80,
                reasoning=reasoning,
                estimated_review_time="15-30 minutes",
                can_skip_review=False
            )
        
        # Default to STANDARD
        reasoning.append("Standard complexity - moderate planning appropriate")
        return ModeDecision(
            selected_mode=PlanningMode.STANDARD,
            confidence=0.90,
            reasoning=reasoning,
            estimated_review_time="5-10 minutes",
            can_skip_review=False
        )
    
    def _qualifies_for_fast_mode(self, profile: TaskProfile, reasoning: List[str]) -> bool:
        """Check if task qualifies for fast mode."""
        meets_criteria = []
        
        # Must have <= 2 subtasks
        if profile.estimated_subtasks <= 2:
            meets_criteria.append(f"Only {profile.estimated_subtasks} subtasks")
        else:
            return False
        
        # Must be low risk
        if profile.risk_level == RiskLevel.LOW:
            meets_criteria.append("Low risk")
        else:
            return False
        
        # Must not be destructive
        if profile.is_destructive:
            return False  # Never FAST for destructive
        
        # Should have pattern match or be learned
        if profile.has_learned_pattern or profile.has_pattern_match:
            meets_criteria.append("Similar pattern exists")
        
        # Should not involve external actions
        if profile.involves_external:
            return False  # External needs more care
        
        if meets_criteria:
            reasoning.extend(meets_criteria)
            reasoning.append("Task qualifies for FAST mode (minimal planning)")
            return True
        
        return False
    
    def _qualifies_for_architect_first(self, profile: TaskProfile, reasoning: List[str]) -> bool:
        """Check if task needs architect-first mode."""
        meets_criteria = []
        
        # High subtask count
        if profile.estimated_subtasks >= 5:
            meets_criteria.append(f"{profile.estimated_subtasks} subtasks (complex)")
        
        # High risk
        if profile.risk_level.value >= RiskLevel.HIGH.value:
            meets_criteria.append(f"{profile.risk_level.name.lower()} risk")
        
        # Novel task
        if profile.is_novel and not profile.has_pattern_match:
            meets_criteria.append("Novel task (no existing pattern)")
        
        # Critical/Destructive
        if profile.is_destructive:
            meets_criteria.append("Destructive operation")
        
        # Long duration
        if profile.estimated_hours >= 8:
            meets_criteria.append(f"Estimated {profile.estimated_hours:.0f} hours (substantial)")
        
        if meets_criteria:
            reasoning.extend(meets_criteria)
            reasoning.append("Task requires ARCHITECT_FIRST mode (heavy planning)")
            return True
        
        return False
    
    def get_complexity_label(self, mode: PlanningMode) -> str:
        """Get human-readable complexity label."""
        labels = {
            PlanningMode.FAST: "Simple",
            PlanningMode.STANDARD: "Moderate", 
            PlanningMode.ARCHITECT_FIRST: "Complex"
        }
        return labels.get(mode, "Unknown")


class PlanningOrchestrator:
    """
    Orchestrates planning workflow based on selected mode.
    
    Integrates PlanReviewer from Phase 1.
    """
    
    def __init__(self, reviewer: Optional[Any] = None):
        self.mode_selector = ModeSelector()
        self.reviewer = reviewer  # PlanReviewer instance
        
    def plan_task(self, description: str, 
                  draft: Optional[Dict] = None,
                  preferences: Optional[Dict] = None) -> Dict:
        """
        Execute full planning workflow for a task.
        
        Returns dict with:
        - mode: Selected mode
        - decision: ModeDecision details
        - review: PlanReview (if applicable)
        - can_proceed: Whether to proceed
        """
        # Step 1: Analyze task
        profile = self.mode_selector.analyze_task(description, draft, preferences)
        
        # Step 2: Select mode
        decision = self.mode_selector.select_mode(profile)
        
        result = {
            "mode": decision.selected_mode.value,
            "mode_decision": decision,
            "task_profile": profile,
            "can_proceed": True,
            "review": None
        }
        
        # Step 3: Apply mode-specific processing
        if decision.selected_mode == PlanningMode.FAST:
            result["can_proceed"] = True
            result["notes"] = "Fast mode: Proceed with minimal planning"
            
        elif decision.selected_mode == PlanningMode.STANDARD:
            # Review if available
            if self.reviewer and draft:
                review = self.reviewer.review(draft)
                result["review"] = review
                result["can_proceed"] = review.recommend_proceed
                result["notes"] = f"Standard mode: Score {review.scores.overall}/100"
            else:
                result["notes"] = "Standard mode: Basic review recommended"
                
        elif decision.selected_mode == PlanningMode.ARCHITECT_FIRST:
            # Mandatory detailed review
            if self.reviewer and draft:
                review = self.reviewer.review(draft)
                result["review"] = review
                result["can_proceed"] = review.recommend_proceed
                result["notes"] = f"Architect mode: Deep review required"
                
                # Check for escalation
                should_escalate, reason = self.reviewer.should_escalate(review)
                if should_escalate:
                    result["escalate"] = True
                    result["escalation_reason"] = reason
            else:
                result["notes"] = "Architect mode: Draft plan required for review"
                result["can_proceed"] = False
        
        return result


def demo_mode_selection():
    """Demonstrate mode selection for various tasks."""
    selector = ModeSelector()
    
    test_tasks = [
        # FAST mode tasks
        ("Fix typo in README", TaskProfile(
            "Fix typo in README", 1, RiskLevel.LOW, False, True, 0.1, False, False, False, True)),
        
        # STANDARD mode tasks  
        ("Refactor login module", TaskProfile(
            "Refactor login module", 3, RiskLevel.MEDIUM, False, True, 2.0, False, False, False, True)),
        
        # ARCHITECT_FIRST mode tasks
        ("Implement new database schema", TaskProfile(
            "Implement new database schema", 8, RiskLevel.HIGH, True, False, 16.0, False, True, True, False)),
    ]
    
    print("=" * 70)
    print("TIERED PLANNING MODES - DEMONSTRATION")
    print("=" * 70)
    
    for desc, profile in test_tasks:
        print(f"\n{'='*70}")
        print(f"Task: {desc}")
        print(f"  Subtasks: {profile.estimated_subtasks}")
        print(f"  Risk: {profile.risk_level.name}")
        print(f"  Novel: {profile.is_novel}")
        print(f"  Destructive: {profile.is_destructive}")
        
        decision = selector.select_mode(profile)
        
        print(f"\n  → SELECTED MODE: {decision.selected_mode.value.upper()}")
        print(f"    Confidence: {decision.confidence:.0%}")
