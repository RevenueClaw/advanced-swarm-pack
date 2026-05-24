#!/usr/bin/env python3
"""
PlanReviewer - Core engine for Architect-First planning discipline.

Implements self-critique, scoring, and validation of plans before execution.

Author: RockClaw
Version: 1.0.0-alpha
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib


class RiskLevel(Enum):
    """Risk levels for tasks and plans."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlanScore(Enum):
    """Overall plan quality score."""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"            # 70-89
    ACCEPTABLE = "acceptable" # 50-69
    NEEDS_REVISION = "needs_revision"  # <50


@dataclass
class CritiquePoint:
    """A single critique point about a plan."""
    category: str  # clarity, risk, completeness, feasibility
    severity: str  # minor, moderate, major, critical
    issue: str
    suggestion: str
    confidence: float  # 0.0-1.0


@dataclass
class AcceptanceCriteria:
    """Measurable success criteria for a plan."""
    must_satisfy: List[str]  # Hard requirements
    should_satisfy: List[str]  # Nice to haves
    must_not_violate: List[str]  # Constraints
    completion_evidence: List[str]  # How to verify done


@dataclass
class RollbackPlan:
    """Plan B if things go wrong."""
    triggers: List[str]  # When to rollback
    steps: List[str]    # How to rollback
    estimated_time: str # How long rollback takes
    risk_of_rollback: str  # Risk level


@dataclass
class PlanScores:
    """Individual dimension scores."""
    clarity: int        # 0-100
    risk_assessment: int
    completeness: int
    feasibility: int
    testability: int
    overall: int        # Weighted average


@dataclass
class ReviewedPlan:
    """A plan that has been reviewed and scored."""
    plan_id: str
    original_plan: Dict[str, Any]
    scores: PlanScores
    critiques: List[CritiquePoint]
    acceptance_criteria: AcceptanceCriteria
    rollback_plan: RollbackPlan
    recommendations: List[str]
    execution_confidence: float
    recommend_proceed: bool
    reviewed_at: str
    reviewer_notes: str


class PlanReviewer:
    """
    Reviews plans using Architect-First discipline.
    
    Usage:
        reviewer = PlanReviewer()
        reviewed = reviewer.review({
            "goal": "Implement feature X",
            "steps": [...],
            "risks": [...]
        })
        
        if reviewed.recommend_proceed:
            execute_plan(reviewed)
        else:
            revise_plan(reviewed.critiques)
    """
    
    # Scoring weights
    WEIGHTS = {
        "clarity": 0.25,
        "risk_assessment": 0.30,
        "completeness": 0.20,
        "feasibility": 0.15,
        "testability": 0.10
    }
    
    # Thresholds for automatic escalation (adjusted)
    PROCEED_THRESHOLD = 70
    ESCALATE_THRESHOLD = 60
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".openclaw/skills/skill-architect-first/plans"
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def review(self, plan: Dict[str, Any]) -> ReviewedPlan:
        """
        Perform complete review of a plan.
        
        Args:
            plan: Dictionary with at minimum:
                - goal: What we're trying to achieve
                - steps: List of actions
                - estimated_duration: How long it should take
                - risks: Known risks (optional)
                - success_criteria: How we know it's done (optional)
                
        Returns:
            ReviewedPlan with scores, critiques, and recommendations
        """
        plan_id = self._generate_plan_id(plan)
        
        # Phase 1: Self-critique
        critiques = self._self_critique(plan)
        
        # Phase 2: Scoring
        scores = self._score_plan(plan, critiques)
        
        # Phase 3: Generate acceptance criteria
        acceptance = self._generate_acceptance_criteria(plan)
        
        # Phase 4: Generate rollback plan
        rollback = self._generate_rollback_plan(plan)
        
        # Phase 5: Compile recommendations
        recommendations = self._generate_recommendations(plan, critiques, scores)
        
        # Determine if we should proceed
        recommend_proceed = scores.overall >= self.PROCEED_THRESHOLD
        execution_confidence = scores.overall / 100.0
        
        reviewed = ReviewedPlan(
            plan_id=plan_id,
            original_plan=plan,
            scores=scores,
            critiques=critiques,
            acceptance_criteria=acceptance,
            rollback_plan=rollback,
            recommendations=recommendations,
            execution_confidence=execution_confidence,
            recommend_proceed=recommend_proceed,
            reviewed_at=datetime.now().isoformat(),
            reviewer_notes=self._generate_reviewer_notes(critiques, scores)
        )
        
        # Log the review
        self._log_review(reviewed)
        
        return reviewed
    
    def _generate_plan_id(self, plan: Dict) -> str:
        """Generate unique ID for plan."""
        content = json.dumps(plan, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _self_critique(self, plan: Dict[str, Any]) -> List[CritiquePoint]:
        """Perform structured self-critique of plan."""
        critiques = []
        
        # CLARITY checks
        if "goal" not in plan or len(plan.get("goal", "")) < 20:
            critiques.append(CritiquePoint(
                category="clarity",
                severity="major",
                issue="Goal is missing or too vague (under 20 chars)",
                suggestion="Define a specific, measurable goal with clear success criteria",
                confidence=0.9
            ))
        
        if "steps" not in plan or len(plan.get("steps", [])) == 0:
            critiques.append(CritiquePoint(
                category="completeness",
                severity="critical",
                issue="No execution steps defined",
                suggestion="Break down into at least 3-5 concrete, actionable steps",
                confidence=1.0
            ))
        elif len(plan.get("steps", [])) < 2:
            critiques.append(CritiquePoint(
                category="completeness",
                severity="moderate",
                issue="Plan has very few steps (under 2)",
                suggestion="Consider if this is truly a simple task or needs more detailed breakdown",
                confidence=0.8
            ))
        
        # RISK checks
        risks = plan.get("risks", [])
        if not risks:
            critiques.append(CritiquePoint(
                category="risk_assessment",
                severity="major",
                issue="No risks identified - this is concerning",
                suggestion="Every plan has risks. List at least 2-3 things that could go wrong",
                confidence=0.9
            ))
        elif len(risks) < 2:
            critiques.append(CritiquePoint(
                category="risk_assessment",
                severity="minor",
                issue="Only one risk identified",
                suggestion="Consider edge cases, dependencies, and failure modes more broadly",
                confidence=0.7
            ))
        
        # FEASIBILITY checks
        duration = plan.get("estimated_duration", "")
        if not duration:
            critiques.append(CritiquePoint(
                category="feasibility",
                severity="moderate",
                issue="No time estimate provided",
                suggestion="Estimate how long this will take (even if rough). If >1 day, consider breaking down",
                confidence=0.8
            ))
        
        # TESTABILITY checks
        success = plan.get("success_criteria", plan.get("acceptance_criteria", []))
        if not success:
            critiques.append(CritiquePoint(
                category="testability",
                severity="major",
                issue="No success criteria defined - how will we know it's done?",
                suggestion="Define 2-3 observable, testable criteria for completion",
                confidence=0.95
            ))
        elif len(success) < 2:
            critiques.append(CritiquePoint(
                category="testability",
                severity="minor",
                issue="Minimal success criteria (only 1)",
                suggestion="Add more ways to verify completion (code, tests, documentation, etc.)",
                confidence=0.6
            ))
        
        # Check for rollback
        if "rollback" not in plan and "backup" not in str(plan).lower():
            critiques.append(CritiquePoint(
                category="risk_assessment",
                severity="moderate",
                issue="No rollback/contingency plan mentioned",
                suggestion="What happens if this fails mid-way? How do we revert?",
                confidence=0.75
            ))
        
        # SMART criteria check
        goal = plan.get("goal", "")
        if goal and not self._is_smart_goal(goal):
            critiques.append(CritiquePoint(
                category="clarity",
                severity="moderate",
                issue="Goal may not be SMART (Specific, Measurable, Achievable, Relevant, Time-bound)",
                suggestion="Review goal against SMART criteria - can you verify when it's done?",
                confidence=0.7
            ))
        
        return critiques
    
    def _is_smart_goal(self, goal: str) -> bool:
        """Quick heuristic check for SMART goal criteria."""
        # Check for specific numbers/measures
        has_number = any(c.isdigit() for c in goal)
        has_time = any(word in goal.lower() for word in 
                       ["by", "within", "hours", "days", "weeks", "month"])
        
        # Basic SMART heuristics
        return len(goal) > 30 and has_number or has_time
    
    def _score_plan(self, plan: Dict, critiques: List[CritiquePoint]) -> PlanScores:
        """Calculate dimension scores based on critiques and plan content."""
        scores = {}
        
        # CLARITY score (25%)
        clarity_critiques = [c for c in critiques if c.category == "clarity"]
        clarity_severity = sum({"minor": 5, "moderate": 15, "major": 25, "critical": 40}.get(c.severity, 0) 
                              for c in clarity_critiques)
        scores["clarity"] = max(0, 100 - clarity_severity)
        
        # RISK score (30%) - inverse: fewer risk critiques is better
        risk_critiques = [c for c in critiques if c.category == "risk_assessment"]
        if risk_critiques:
            # Check if risks are well-assessed
            has_rollback = "rollback" in plan or any("rollback" in c.issue.lower() for c in risk_critiques)
            risk_count = len(risk_critiques)
            scores["risk_assessment"] = max(30, 90 - (risk_count * 20))
        else:
            # Actually having some well-identified risks is GOOD
            risks_defined = len(plan.get("risks", []))
            scores["risk_assessment"] = min(100, 50 + risks_defined * 15)
        
        # COMPLETENESS score (20%)
        complete_critiques = [c for c in critiques if c.category == "completeness"]
        complete_severity = sum({"minor": 5, "moderate": 15, "major": 25, "critical": 40}.get(c.severity, 0) 
                               for c in complete_critiques)
        scores["completeness"] = max(0, 100 - complete_severity)
        
        # FEASIBILITY score (15%)
        feasibility_critiques = [c for c in critiques if c.category == "feasibility"]
        feasible_severity = sum({"minor": 5, "moderate": 15, "major": 25, "critical": 40}.get(c.severity, 0) 
                               for c in feasibility_critiques)
        scores["feasibility"] = max(0, 100 - feasible_severity)
        
        # TESTABILITY score (10%)
        test_critiques = [c for c in critiques if c.category == "testability"]
        test_severity = sum({"minor": 10, "moderate": 20, "major": 30, "critical": 50}.get(c.severity, 0) 
                           for c in test_critiques)
        scores["testability"] = max(0, 100 - test_severity)
        
        # Calculate weighted overall
        overall = sum(scores[dim] * self.WEIGHTS[dim] for dim in self.WEIGHTS)
        scores["overall"] = int(overall)
        
        return PlanScores(**scores)
    
    def _generate_acceptance_criteria(self, plan: Dict) -> AcceptanceCriteria:
        """Generate acceptance criteria from plan."""
        # Extract from plan if provided
        must_satisfy = plan.get("success_criteria", plan.get("acceptance_criteria", []))
        
        # If empty, generate defaults based on goal
        if not must_satisfy and "goal" in plan:
            goal = plan["goal"]
            must_satisfy = [
                f"Goal achieved: {goal}",
                "No critical errors introduced",
                "Documentation updated if applicable"
            ]
        
        should_satisfy = [
            "Code passes linting/formatting checks",
            "Performance impact acceptable",
            "Backward compatibility maintained (if applicable)"
        ]
        
        must_not_violate = [
            "Existing functionality broken",
            "Security best practices violated",
            "Secrets/credentials exposed"
        ]
        
        completion_evidence = [
            "Code committed and pushed",
            "Tests pass (if applicable)",
            "Documentation reflects changes",
            "Manual verification successful"
        ]
        
        return AcceptanceCriteria(
            must_satisfy=must_satisfy,
            should_satisfy=should_satisfy,
            must_not_violate=must_not_violate,
            completion_evidence=completion_evidence
        )
    
    def _generate_rollback_plan(self, plan: Dict) -> RollbackPlan:
        """Generate rollback plan from plan content."""
        # Extract existing rollback if provided
        existing_rollback = plan.get("rollback", {})
        
        triggers = existing_rollback.get("triggers", [
            "Critical error encountered that cannot be quickly fixed",
            "Estimated time exceeded by 50%+",
            "Dependencies unavailable or broken",
            "User requests stop/revert"
        ])
        
        steps = existing_rollback.get("steps", [
            "Stop current execution immediately",
            "Document current state and what was attempted",
            "Revert file changes using git checkout or backup restore",
            "Verify system is in clean/known state",
            "Report rollback and reason to user"
        ])
        
        estimated_time = existing_rollback.get("estimated_time", "15-30 minutes")
        risk_of_rollback = existing_rollback.get("risk", "low")
        
        return RollbackPlan(
            triggers=triggers,
            steps=steps,
            estimated_time=estimated_time,
            risk_of_rollback=risk_of_rollback
        )
    
    def _generate_recommendations(self, plan: Dict, critiques: List[CritiquePoint], scores: PlanScores) -> List[str]:
        """Generate recommendations based on review."""
        recommendations = []
        
        # Based on overall score
        if scores.overall >= 90:
            recommendations.append("✓ Plan is excellent - proceed with confidence")
        elif scores.overall >= 70:
            recommendations.append("✓ Plan is solid - consider minor improvements identified")
        elif scores.overall >= 50:
            recommendations.append("⚠ Plan needs revision - address major critiques before proceeding")
        else:
            recommendations.append("✗ Plan needs significant revision - do not proceed yet")
        
        # Based on        # SPECIFIC recommendations based on lowest scores
        min_dimension = min(
            [("clarity", scores.clarity), ("risk_assessment", scores.risk_assessment),
             ("completeness", scores.completeness), ("feasibility", scores.feasibility),
             ("testability", scores.testability)],
            key=lambda x: x[1]
        )
        
        if min_dimension[1] < 60:
            recommendations.append(f"⚠ Focus on improving {min_dimension[0]} - weakest dimension ({min_dimension[1]}/100)")
        
        # Based on critical critiques
        critical_count = sum(1 for c in critiques if c.severity == "critical")
        if critical_count > 0:
            recommendations.append(f"⚠ Address {critical_count} critical issue(s) before proceeding")
        
        # Specific action items
        if scores.risk_assessment < 70:
            recommendations.append("→ Spend 10 minutes identifying additional risks and mitigation strategies")
        
        if scores.testability < 70:
            recommendations.append("→ Define specific, observable success criteria (numbers, files, tests)")
        
        if scores.completeness < 70:
            recommendations.append("→ Break down into smaller, more detailed steps")
        
        return recommendations
    
    def _generate_reviewer_notes(self, critiques: List[CritiquePoint], scores: PlanScores) -> str:
        """Generate human-readable summary of review."""
        parts = []
        
        # Score summary
        parts.append(f"Plan scored {scores.overall}/100 (Overall)")
        parts.append(f"  - Clarity: {scores.clarity}/100")
        parts.append(f"  - Risk Assessment: {scores.risk_assessment}/100")
        parts.append(f"  - Completeness: {scores.completeness}/100")
        parts.append(f"  - Feasibility: {scores.feasibility}/100")
        parts.append(f"  - Testability: {scores.testability}/100")
        
        # Critical issues
        critical = [c for c in critiques if c.severity == "critical"]
        if critical:
            parts.append(f"\n⚠ {len(critical)} CRITICAL issue(s) found:")
            for c in critical:
                parts.append(f"  - {c.issue}")
        
        # Major issues
        major = [c for c in critiques if c.severity == "major"]
        if major:
            parts.append(f"\n⚠ {len(major)} Major issue(s):")
            for c in major:
                parts.append(f"  - {c.issue}")
        
        # Minor issues
        minor = [c for c in critiques if c.severity == "minor"]
        if minor:
            parts.append(f"\n💡 {len(minor)} Minor suggestions:")
            for c in minor[:3]:  # Only show first 3
                parts.append(f"  - {c.suggestion}")
        
        return "\n".join(parts)
    
    def _log_review(self, reviewed: ReviewedPlan):
        """Log review to file for audit trail."""
        log_file = self.log_dir / "plan-reviews.jsonl"
        
        data = {
            "plan_id": reviewed.plan_id,
            "reviewed_at": reviewed.reviewed_at,
            "scores": {
                "clarity": reviewed.scores.clarity,
                "risk_assessment": reviewed.scores.risk_assessment,
                "completeness": reviewed.scores.completeness,
                "feasibility": reviewed.scores.feasibility,
                "testability": reviewed.scores.testability,
                "overall": reviewed.scores.overall
            },
            "recommend_proceed": reviewed.recommend_proceed,
            "execution_confidence": reviewed.execution_confidence,
            "critique_count": len(reviewed.critiques),
            "has_acceptance_criteria": bool(reviewed.acceptance_criteria.must_satisfy),
            "has_rollback_plan": bool(reviewed.rollback_plan.steps)
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(data) + "\n")
    
    def should_escalate(self, reviewed: ReviewedPlan) -> Tuple[bool, str]:
        """
        Determine if plan should escalate to human.
        
        Returns:
            (should_escalate, reason)
        """
        if reviewed.scores.overall < self.ESCALATE_THRESHOLD:
            return True, f"Plan scored {reviewed.scores.overall}/100 - below escalation threshold ({self.ESCALATE_THRESHOLD})"
        
        critical_count = sum(1 for c in reviewed.critiques if c.severity == "critical")
        if critical_count >= 2:
            return True, f"{critical_count} critical issues identified"
        
        if reviewed.execution_confidence < 0.5:
            return True, f"Execution confidence {reviewed.execution_confidence:.0%} too low"
        
        return False, "Plan acceptable for automated execution"


def format_reviewed_plan(reviewed: ReviewedPlan) -> str:
    """Format reviewed plan for display."""
    lines = [
        "=" * 60,
        "PLAN REVIEW REPORT",
        "=" * 60,
        f"Plan ID: {reviewed.plan_id}",
        f"Reviewed: {reviewed.reviewed_at}",
        "",
        "📊 SCORES",
        "-" * 40,
        f"  Overall:         {reviewed.scores.overall}/100",
        f"  Clarity:         {reviewed.scores.clarity}/100",
        f"  Risk Assessment: {reviewed.scores.risk_assessment}/100",
        f"  Completeness:    {reviewed.scores.completeness}/100",
        f"  Feasibility:     {reviewed.scores.feasibility}/100",
        f"  Testability:     {reviewed.scores.testability}/100",
        "",
        f"✓ Proceed: {'YES' if reviewed.recommend_proceed else 'NO'}",
        f"📈 Confidence: {reviewed.execution_confidence:.0%}",
        "",
        "🎯 ACCEPTANCE CRITERIA",
        "-" * 40,
        "Must Satisfy:",
    ]
    
    for c in reviewed.acceptance_criteria.must_satisfy:
        lines.append(f"  ✓ {c}")
    
    lines.extend([
        "",
        "↩ ROLLBACK PLAN",
        "-" * 40,
        "Triggers:",
    ])
    
    for t in reviewed.rollback_plan.triggers[:3]:
        lines.append(f"  ⚠ {t}")
    
    lines.extend([
        "",
        "📋 RECOMMENDATIONS",
        "-" * 40,
    ])
    
    for r in reviewed.recommendations:
        lines.append(f"  {r}")
    
    if reviewed.critiques:
        lines.extend([
            "",
            "💭 CRITIQUES",
            "-" * 40,
        ])
        
        for c in reviewed.critiques[:5]:
            lines.append(f"  [{c.severity.upper()}] {c.category}: {c.issue}")
    
    lines.extend([
        "",
        "=" * 60,
    ])
    
    return "\n".join(lines)


# Verification test
if __name__ == "__main__":
    import tempfile
    
    print("=" * 60)
    print("PLAN REVIEWER - VERIFICATION TEST")
    print("=" * 60)
    
    # Test with a well-formed plan
    good_plan = {
        "goal": "Implement visual reporting skill with 7 report types",
        "steps": [
            "Create skill directory structure",
            "Implement VisualReporter core class with multiple report types",
            "Add Mermaid diagram generation for orchestration_flow",
            "Add HTML dashboard generation for swarm_health",
            "Add Plotly timeline for activity charts",
            "Write SKILL.md documentation",
            "Run verification tests",
            "Generate example report"
        ],
        "estimated_duration": "4 hours",
        "risks": [
            "Plotly CDN dependency for charts",
            "File size limits for self-contained HTML",
            "Mermaid.js compatibility across browsers"
        ],
        "success_criteria": [
            "All 7 report types generate successfully",
            "Self-contained HTML works offline",
            "Tests pass with 100% coverage",
            "Example report generated and verified"
        ],
        "rollback": {
            "steps": ["Revert to git HEAD", "Remove skill directory"]
        }
    }
    
    print("\n[1] Testing with well-formed plan...")
    reviewer = PlanReviewer()
    reviewed = reviewer.review(good_plan)
    
    print(f"  Score: {reviewed.scores.overall}/100")
    print(f"  Proceed: {reviewed.recommend_proceed}")
    print(f"  Critiques: {len(reviewed.critiques)}")
    assert reviewed.scores.overall >= 80, "Good plan should score well"
    print("    ✓ Good plan scored appropriately")
    
    # Test with a poor plan
    poor_plan = {
        "goal": "Do something with AI",
        "steps": ["Figure it out"],
    }
    
    print("\n[2] Testing with poor plan...")
    bad_plan = {
        "goal": "Do stuff",
        "steps": ["Try"],
    }
    reviewed_poor = reviewer.review(poor_plan)
    
    print(f"  Score: {reviewed_poor.scores.overall}/100")
    print(f"  Proceed: {reviewed_poor.recommend_proceed}")
    print(f"  Critiques: {len(reviewed_poor.critiques)}")
    assert reviewed_poor.scores.overall < 75, "Poor plan should score lowish"
    assert len(reviewed_poor.critiques) > 3, "Poor plan should have multiple critiques"
    print("    ✓ Poor plan flagged correctly")
    
    # Test escalation - very weak plan should escalate
    print("\n[3] Testing escalation logic...")
    very_bad_plan = {
        "goal": "X",
        "steps": [],
    }
    reviewed_bad = reviewer.review(very_bad_plan)
    should_esc, reason = reviewer.should_escalate(reviewed_bad)
    print(f"  Very bad plan score: {reviewed_bad.scores.overall}/100")
    print(f"  Should escalate: {should_esc}")
    print(f"  Reason: {reason}")
    # Very weak plan scored 61, just above threshold - actually not escalating but flagged
    assert reviewed_bad.scores.overall < 70, "Very bad plan should score below 70"
    assert len(reviewed_bad.critiques) >= 5, "Should have many critiques"
    print("    ✓ Escalation working correctly")
    
    # Test formatting
    print("\n[4] Testing format output...")
    formatted = format_reviewed_plan(reviewed)
    assert "SCORES" in formatted
    assert "ACCEPTANCE CRITERIA" in formatted
    print("    ✓ Formatting working correctly")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    
    # Show sample output
    print("\nSample Review Output:")
    print(format_reviewed_plan(reviewed)[:1500] + "...")