#!/usr/bin/env python3
"""
Premortem Integration Hooks

Connects PremortemAnalyzer to:
- skill-architect-first (PlanReviewer)
- skill-estimation-engine (buffer adjustments)
- skill-consensus (debate context)

Author: RockClaw
Version: 1.0.0
"""

from typing import Dict, Any, Optional, List
from pathlib import Path


class PremortemIntegrations:
    """Integration helpers for premortem with other swarm skills."""
    
    @staticmethod
    def enhance_plan_reviewer(
        plan_reviewer_instance: Any,
        goal: str,
        steps: List[str],
        context: str = "",
        risk_tolerance: str = "medium"
    ) -> Optional[Dict[str, Any]]:
        """
        Auto-trigger premortem for PlanReviewer when conditions met.
        
        Args:
            plan_reviewer_instance: The PlanReviewer instance
            goal: Plan goal
            steps: Plan steps
            context: Additional context
            risk_tolerance: Risk tolerance level
        
        Returns:
            Premortem result or None if not triggered
        """
        from .premortem_analyzer import PremortemAnalyzer, DepthLevel
        
        # Determine if premortem needed
        needs_premortem = (
            len(steps) > 3 or  # Complex plans
            "production" in context.lower() or
            "revenue" in context.lower() or
            "customer" in context.lower() or
            any(s in " ".join(steps).lower() for s in [
                "migration", "database", "refactor", "architecture"
            ])
        )
        
        if not needs_premortem:
            return None
        
        depth = DepthLevel.STANDARD.value if len(steps) > 4 else DepthLevel.QUICK.value
        
        analyzer = PremortemAnalyzer()
        return analyzer.premortem(
            goal=goal,
            proposed_plan=steps,
            context=context,
            risk_tolerance=risk_tolerance,
            depth=depth
        )
    
    @staticmethod
    def adjust_estimate_for_risk(
        base_estimate: Dict[str, Any],
        premortem_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adjust estimation engine output based on premortem risks.
        
        Args:
            base_estimate: Original estimate from EstimationEngine
            premortem_analysis: Premortem result
        
        Returns:
            Risk-adjusted estimate
        """
        adjusted = dict(base_estimate)
        
        # Count tail risks
        tail_risk_count = len(premortem_analysis.get("tail_risks", []))
        
        # Add risk-adjusted buffer
        if tail_risk_count >= 2:
            base_hours = adjusted.get("total_estimated_hours", 0)
            risk_buffer = base_hours * 0.25  # +25% for multiple tail risks
            adjusted["risk_adjusted_hours"] = base_hours + risk_buffer
            adjusted["risk_buffer_percent"] = 25
            adjusted["risk_notes"] = f"+25% for {tail_risk_count} tail risk mitigations"
        elif tail_risk_count == 1:
            base_hours = adjusted.get("total_estimated_hours", 0)
            risk_buffer = base_hours * 0.15  # +15% for one tail risk
            adjusted["risk_adjusted_hours"] = base_hours + risk_buffer
            adjusted["risk_buffer_percent"] = 15
            adjusted["risk_notes"] = "+15% for tail risk mitigation"
        
        # Add premortem reference
        adjusted["premortem_id"] = premortem_analysis.get("analysis_id")
        
        return adjusted
    
    @staticmethod
    def add_to_consensus_debate(
        debate_context: Dict[str, Any],
        premortem_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add premortem insights to consensus debate.
        
        Args:
            debate_context: Context for SkillConsensus
            premortem_analysis: Premortem result
        
        Returns:
            Enhanced debate context
        """
        enhanced = dict(debate_context)
        
        # Build risk context for debate panel
        risk_context = {
            "most_likely_failure": premortem_analysis.get("most_likely_failure", {}).get("scenario"),
            "hidden_assumptions": [
                a["assumption"] for a in premortem_analysis.get("hidden_assumptions", [])[:3]
            ],
            "tail_risks": [
                r["scenario"] for r in premortem_analysis.get("tail_risks", [])[:2]
            ],
            "risk_score": premortem_analysis.get("risk_score"),
            "optimism_bias": premortem_analysis.get("optimism_bias_delta")
        }
        
        enhanced["premortem_risk_context"] = risk_context
        
        # Add prompts for specific personas
        if "persona_prompts" not in enhanced:
            enhanced["persona_prompts"] = {}
        
        enhanced["persona_prompts"]["conservative"] = (
            f"Pay special attention to tail risks: {', '.join(risk_context['tail_risks'][:2])}. "
            f"Most likely failure: {risk_context['most_likely_failure']}."
        )
        
        return enhanced
    
    @staticmethod
    def extract_critical_mitigations(
        premortem_analysis: Dict[str, Any],
        max_mitigations: int = 3
    ) -> List[str]:
        """
        Extract critical mitigations from analysis for immediate action.
        
        Args:
            premortem_analysis: Premortem result
            max_mitigations: Max number to return
        
        Returns:
            List of mitigation actions
        """
        mitigations = premortem_analysis.get("mitigations", [])
        critical = [
            m["action"] for m in mitigations 
            if m.get("priority") == "critical"
        ]
        return critical[:max_mitigations]
    
    @staticmethod
    def get_pre_deployment_checklist(
        premortem_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate pre-deployment checklist from EWIs.
        
        Args:
            premortem_analysis: Premortem result
        
        Returns:
            List of checklist items with severity
        """
        ewis = premortem_analysis.get("early_warning_indicators", [])
        checklist = []
        
        for ewi in ewis:
            if ewi.get("stage") in ["pre-deployment", "testing"]:
                checklist.append({
                    "check": f"Verify: {ewi['indicator']}",
                    "severity": ewi.get("severity", "medium"),
                    "threshold": ewi.get("threshold")
                })
        
        return checklist


def should_trigger_premortem(plan: Dict[str, Any]) -> bool:
    """
    Decision helper: should this plan get a premortem?
    
    Args:
        plan: Plan dict with goal, steps, risks, etc.
    
    Returns:
        True if premortem recommended
    """
    triggers = []
    
    # Complexity triggers
    if len(plan.get("steps", [])) > 3:
        triggers.append("many_steps")
    
    # Risk triggers
    if plan.get("risk_level") in ["high", "critical"]:
        triggers.append("high_risk")
    
    if len(plan.get("risks", [])) > 2:
        triggers.append("many_risks")
    
    # Context triggers
    goal = plan.get("goal", "").lower()
    if any(kw in goal for kw in ["production", "customer", "revenue", "migration", "refactor"]):
        triggers.append("high_impact_context")
    
    # Score trigger from PlanReviewer
    if plan.get("score", 0) < 75:
        triggers.append("low_score")
    
    return len(triggers) >= 1


def format_premortem_summary(analysis: Dict[str, Any], verbose: bool = False) -> str:
    """
    Format premortem result as human-readable summary.
    
    Args:
        analysis: Premortem result
        verbose: Include full details
    
    Returns:
        Formatted summary string
    """
    lines = [
        "",
        "=" * 60,
        "PREMORTEM ANALYSIS SUMMARY",
        "=" * 60,
        "",
        f"🎯 Goal: {analysis.get('goal', 'N/A')}",
        f"📊 Risk Score: {analysis.get('risk_score', 'N/A')}/100",
        f"⚠️  Most Likely Failure: {analysis.get('most_likely_failure', {}).get('scenario', 'N/A')}",
        "",
    ]
    
    if verbose:
        lines.extend([
            f"😊 Optimism Bias: +{analysis.get('optimism_bias_delta', 0)}%",
            "",
            "🔥 Tail Risks:",
        ])
        for risk in analysis.get("tail_risks", [])[:3]:
            lines.append(f"   - {risk.get('scenario', 'N/A')} ({risk.get('probability', 'N/A')})")
        
        lines.extend(["", "💡 Hidden Assumptions:"])
        for assumption in analysis.get("hidden_assumptions", [])[:3]:
            lines.append(f"   - {assumption.get('assumption', 'N/A')[:60]}...")
        
        lines.extend(["", "🛡️  Critical Mitigations:"])
        for m in analysis.get("mitigations", [])[:3]:
            if m.get("priority") == "critical":
                lines.append(f"   - {m.get('action', 'N/A')[:60]}...")
    else:
        # Concise version
        lines.extend([
            f"   {len(analysis.get('tail_risks', []))} tail risks | "
            f"{len(analysis.get('hidden_assumptions', []))} hidden assumptions | "
            f"{len(analysis.get('mitigations', []))} mitigations"
        ])
    
    lines.extend(["", "=" * 60])
    
    return "\n".join(lines)


if __name__ == "__main__":
    print("Premortem Integrations module ready for import")
    print("Import with: from skill_premortem_v1.lib.integrations import PremortemIntegrations")
