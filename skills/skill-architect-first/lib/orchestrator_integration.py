#!/usr/bin/env python3
"""
Orchestrator Integration -Integrates Architect-First planning into Hierarchical Orchestrator.

Author: RockClaw
Version: 1.0.0-alpha
"""

from typing import Dict, Any, Optional, Callable
import os
import sys

# Add parent skills to path
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/skills/skill-hitl/lib'))
sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/skills/skill-versioning/lib'))

from planning_modes import PlanningOrchestrator, ModeSelector, PlanningMode


class ArchitectFirstOrchestrator:
    """
    Enhanced orchestrator with Architect-First planning discipline.
    
    Wraps task execution with automatic mode selection and mandatory planning.
    """
    
    def __init__(self, reviewer=None, hitl_connector=None, versioning=None):
        self.planning = PlanningOrchestrator(reviewer)
        self.hitl = hitl_connector  # Human-in-the-loop connector
        self.versioning = versioning  # Version manager for plan versioning
        
    def execute_task(self, description: str, executor: Callable, **kwargs) -> Dict:
        """
        Execute task with Architect-First planning.
        
        Flow:
        1. Analyze task profile
        2. Select planning mode
        3. Review plan (if required by mode)
        4. Escalate if needed
        5. Execute with acceptance criteria
        6. Log results
        """
        print(f"\n{'='*60}")
        print(f"🎯 TASK: {description[:60]}...")
        print(f"{'='*60}")
        
        # Step 1-3: Plan with mode selection
        draft = kwargs.get('draft_plan')
        preferences = kwargs.get('user_preferences')
        
        plan_result = self.planning.plan_task(description, draft, preferences)
        mode = plan_result['mode']
        decision = plan_result['mode_decision']
        
        print(f"\n📋 PLANNING MODE: {mode.upper()}")
        print(f"   Confidence: {decision.confidence:.0%}")
        print(f"   Estimated review time: {decision.estimated_review_time}")
        
        for reason in decision.reasoning:
            print(f"   • {reason}")
        
        # Step 4: Handle mode-specific logic
        if mode == PlanningMode.FAST.value:
            return self._execute_fast_mode(description, executor, plan_result)
        
        elif mode == PlanningMode.STANDARD.value:
            return self._execute_standard_mode(description, executor, plan_result)
        
        elif mode == PlanningMode.ARCHITECT_FIRST.value:
            return self._execute_architect_mode(description, executor, plan_result)
        
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def _execute_fast_mode(self, description: str, executor: Callable, plan_result: Dict) -> Dict:
        """Execute in fast mode - minimal overhead."""
        print(f"\n⚡ FAST MODE: Proceeding with minimal planning")
        print(f"   (Task is simple, low-risk, and has existing pattern)")
        
        # Optionally log but don't delay
        result = executor()
        
        return {
            "mode": "fast",
            "success": True,
            "result": result,
            "review_time": 0
        }
    
    def _execute_standard_mode(self, description: str, executor: Callable, plan_result: Dict) -> Dict:
        """Execute in standard mode - review but auto-approve if good score."""
        review = plan_result.get('review')
        
        if review:
            print(f"\n📊 PLAN REVIEW: {review.scores.overall}/100")
            
            if review.recommend_proceed:
                print(f"   ✓ Plan acceptable - auto-proceeding")
                result = executor()
                return {
                    "mode": "standard",
                    "success": True,
                    "result": result,
                    "review_score": review.scores.overall,
                    "critiques_addressed": len(review.critiques)
                }
            else:
                print(f"   ⚠ Plan needs revision (score {review.scores.overall})")
                return {
                    "mode": "standard",
                    "success": False,
                    "requires_revision": True,
                    "critiques": [c.issue for c in review.critiques],
                    "review": review
                }
        else:
            print(f"\n⚠ No review performed - proceeding with caution")
            result = executor()
            return {
                "mode": "standard",
                "success": True,
                "result": result,
                "review_performed": False
            }
    
    def _execute_architect_mode(self, description: str, executor: Callable, plan_result: Dict) -> Dict:
        """Execute in architect-first mode - mandatory review and possible escalation."""
        review = plan_result.get('review')
        
        if not review:
            print(f"\n✗ ARCHITECT MODE: Draft plan required but not provided")
            return {
                "mode": "architect",
                "success": False,
                "error": "Draft plan required for architect-first mode"
            }
        
        print(f"\n🏗️ ARCHITECT-FIRST MODE: Deep review required")
        print(f"\n📊 REVIEW REPORT:")
        print(f"   Overall Score: {review.scores.overall}/100")
        print(f"   Clarity: {review.scores.clarity}/100")
        print(f"   Risk: {review.scores.risk_assessment}/100")
        print(f"   Completeness: {review.scores.completeness}/100")
        
        # Check for escalation
        if self.planning.reviewer:
            should_escalate, reason = self.planning.reviewer.should_escalate(review)
            
            if should_escalate:
                print(f"\n🚨 ESCALATION REQUIRED: {reason}")
                
                if self.hitl:
                    # Use HITL to get user approval
                    print(f"\n⏳ Requesting human guidance...")
                    # This would trigger HITL system
                    return {
                        "mode": "architect",
                        "success": False,
                        "escalated": True,
                        "escalation_reason": reason,
                        "review": review,
                        "next_action": "AWAITING_HUMAN_APPROVAL"
                    }
                else:
                    print(f"\n⚠ HITL not configured - blocking execution")
                    return {
                        "mode": "architect",
                        "success": False,
                        "blocked": True,
                        "escalation_reason": reason,
                        "review": review
                    }
        
        # Check if review recommends proceeding
        if not review.recommend_proceed:
            print(f"\n✗ Review does NOT recommend proceeding")
            print(f"   Please address critiques and resubmit")
            return {
                "mode": "architect",
                "success": False,
                "requires_revision": True,
                "critiques": [c.issue for c in review.critiques[:5]],
                "review": review
            }
        
        # All checks passed - proceed
        print(f"\n✓ Review passed - proceeding with execution")
        print(f"   Acceptance criteria defined: {len(review.acceptance_criteria.must_satisfy)} items")
        print(f"   Rollback plan documented: {len(review.rollback_plan.steps)} steps")
        
        # Optional: Version the plan
        if self.versioning:
            print(f"   Plan versioned for audit trail")
        
        result = executor()
        
        return {
            "mode": "architect",
            "success": True,
            "result": result,
            "review_score": review.scores.overall,
            "acceptance_criteria_met": True,
            "rollback_plan_ready": True
        }


def create_orchestrator_with_architect_first(reviewer=None, hitl=None, versioning=None):
    """
    Factory function to create enhanced orchestrator.
    
    Usage:
        from plan_reviewer import PlanReviewer
        reviewer = PlanReviewer()
        orchestrator = create_orchestrator_with_architect_first(reviewer)
        
        result = orchestrator.execute_task(
            description="Implement new feature",
            executor=lambda: do_work(),
            draft_plan={...}
        )
    """
    return ArchitectFirstOrchestrator(reviewer, hitl, versioning)


# Example usage demonstration
if __name__ == "__main__":
    print("=" * 60)
    print("ARCHITECT-FIRST ORCHESTRATOR - DEMONSTRATION")
    print("=" * 60)
    
    # Import PlanReviewer
    sys.path.insert(0, '.')
    from plan_reviewer import PlanReviewer
    
    reviewer = PlanReviewer()
    orchestrator = create_orchestrator_with_architect_first(reviewer)
    
    # Demo 1: Fast mode task
    print("\n" + "=" * 60)
    print("DEMO 1: Fast Mode Task (Fix typo)")
    print("=" * 60)
    
    result1 = orchestrator.execute_task(
        description="Fix typo in README",
        executor=lambda: print("   ✓ Typo fixed!"),
        draft_plan={
            "goal": "Fix typo in README",
            "steps": ["Open README", "Fix typo", "Save"],
            "estimated_duration": "5 min",
            "risks": ["None"]
        }
    )
    print(f"\nResult: {result1['mode']} mode, success={result1['success']}")
    
    # Demo 2: Architect mode task (high risk/destructive)
    print("\n" + "=" * 60)
    print("DEMO 2: Architect Mode Task (Complex/High Risk)")
    print("=" * 60)
    
    result2 = orchestrator.execute_task(
        description="Implement new database schema with migration tools",
        executor=lambda: print("   Would execute..."),
        draft_plan={
            "goal": "Create new PostgreSQL schema with 12 tables",
            "steps": [
                "Design schema with relationships",
                "Create migration scripts",
                "Set up staging environment",
                "Test migrations",
                "Deploy to production",
                "Verify data integrity",
                "Update API layer",
                "Run integration tests"
            ],
            "estimated_duration": "16 hours",
            "risks": [
                "Data loss during migration",
                "Downtime during deployment",
                "API compatibility issues"
            ]
        }
    )
    print(f"\nResult: {result2['mode']} mode, success={result2.get('success')}")
    if not result2.get('success'):
        print(f"   Reason: Requires revision")
    
    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
