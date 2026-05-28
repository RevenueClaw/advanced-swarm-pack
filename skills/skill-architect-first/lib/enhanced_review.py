#!/usr/bin/env python3
"""
Enhanced Plan Review with Premortem and Codebase Understanding.

Extends PlanReviewer with:
- Automatic premortem analysis for high-risk plans
- Codebase context injection for development plans
- Risk score adjustments based on additional analysis

Author: RockClaw (v1.3.0 enhancements)
Version: 1.1.0
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add new skill paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skill-premortem-v1"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skill-codebase-understander-v1"))

try:
    from lib.premortem_analyzer import PremortemAnalyzer, DepthLevel
    PREMORTEM_AVAILABLE = True
except ImportError:
    PREMORTEM_AVAILABLE = False

try:
    from lib.codebase_analyzer import CodebaseAnalyzer
    from lib.integration import CodebaseContext
    CODEBASE_AVAILABLE = True
except ImportError:
    CODEBASE_AVAILABLE = False

from .plan_reviewer import PlanReviewer, ReviewedPlan, PlanScores


class EnhancedPlanReviewer(PlanReviewer):
    """
    Extended PlanReviewer with premortem and codebase understanding.
    
    Usage:
        reviewer = EnhancedPlanReviewer()
        reviewed = reviewer.review_with_enhancements(plan, repo_path="/path/to/code")
    
    The enhanced review adds:
    - Premortem analysis for plans scoring <75 or with >3 steps
    - Missing risk identification via future-failure simulation
    - Hidden assumption exposure
    - Codebase complexity context for dev plans
    - Artifact count estimates for development tasks
    """
    
    def __init__(self, log_dir=None, enable_premortem=True, enable_codebase=True):
        """
        Initialize enhanced reviewer.
        
        Args:
            log_dir: Where to store review logs
            enable_premortem: Whether to auto-trigger premortem analysis
            enable_codebase: Whether to include codebase context for dev plans
        """
        super().__init__(log_dir)
        self.enable_premortem = enable_premortem and PREMORTEM_AVAILABLE
        self.enable_codebase = enable_codebase and CODEBASE_AVAILABLE
        
        if self.enable_premortem:
            self._premortem = PremortemAnalyzer()
        else:
            self._premortem = None
        
        self._codebase_analyzer = None
    
    def review_with_enhancements(
        self,
        plan: Dict[str, Any],
        repo_path: Optional[str] = None,
        risk_tolerance: str = "medium"
    ) -> Dict[str, Any]:
        """
        Enhanced review with optional premortem and codebase analysis.
        
        Args:
            plan: Standard plan dict
            repo_path: Path to codebase (if applicable)
            risk_tolerance: low/medium/high
        
        Returns:
            Enhanced ReviewedPlan with additional fields:
            - premortem_analysis: (if triggered)
            - codebase_context: (if dev plan)
            - enhanced_recommendations: Combined list
            - adjusted_score: Score after enhancements
        """
        # Run base review
        reviewed = self.review(plan)
        
        enhanced_result = {
            "base_review": reviewed,
            "enrichments_applied": [],
            "adjusted_score": reviewed.scores.overall,
            "enhanced_recommendations": list(reviewed.recommendations),
            "premortem_triggered": False,
            "codebase_context_added": False
        }
        
        # Determine if premortem needed
        needs_premortem = (
            self._should_trigger_premortem(plan, reviewed.scores.overall)
        )
        
        if needs_premortem and self._premortem:
            # Run premortem analysis
            depth = DepthLevel.DEEP if len(plan.get("steps", [])) > 5 else DepthLevel.STANDARD
            
            try:
                premortem_result = self._premortem.premortem(
                    goal=plan.get("goal", ""),
                    proposed_plan=plan.get("steps", []),
                    context=plan.get("context", ""),
                    risk_tolerance=risk_tolerance,
                    depth=depth.value,
                    original_score=reviewed.scores.overall
                )
                
                enhanced_result["premortem_analysis"] = premortem_result
                enhanced_result["premortem_triggered"] = True
                enhanced_result["enrichments_applied"].append("premortem")
                
                # Adjust score based on premortem
                if premortem_result.get("adjusted_score"):
                    enhanced_result["adjusted_score"] = premortem_result["adjusted_score"]
                
                # Add critical mitigations to recommendations
                critical_mits = [
                    m["action"] for m in premortem_result.get("mitigations", [])
                    if m.get("priority") == "critical"
                ][:2]
                
                for mitigation in critical_mits:
                    enhanced_result["enhanced_recommendations"].append(
                        f"[CRITICAL MITIGATION] {mitigation}"
                    )
                
            except Exception as e:
                enhanced_result["premortem_error"] = str(e)
        
        # Add codebase context for dev plans
        if self._is_dev_plan(plan) and repo_path and self.enable_codebase:
            try:
                codebase_ctx = self._get_codebase_context(repo_path)
                
                if codebase_ctx:
                    enhanced_result["codebase_context"] = codebase_ctx.to_plan_context()
                    enhanced_result["codebase_context_added"] = True
                    enhanced_result["enrichments_applied"].append("codebase")
                    
                    # Add complexity warning if needed
                    if codebase_ctx.get_overall_complexity() == "very_high":
                        enhanced_result["enhanced_recommendations"].append(
                            "[COMPLEXITY WARNING] Very high complexity codebase. "
                            "Consider phased approach with additional testing."
                        )
                        # Slight score adjustment
                        if enhanced_result["adjusted_score"] > 85:
                            enhanced_result["adjusted_score"] = max(70, enhanced_result["adjusted_score"] - 5)
                    
                    # Add untested files warning
                    untested = codebase_ctx.find_untested_dependencies()
                    if len(untested) > 5:
                        enhanced_result["enhanced_recommendations"].append(
                            f"[TEST GAP] {len(untested)} files lack test coverage"
                        )
                
            except Exception as e:
                enhanced_result["codebase_error"] = str(e)
        
        return enhanced_result
    
    def _should_trigger_premortem(self, plan: Dict[str, Any], score: int) -> bool:
        """Determine if premortem analysis should be triggered."""
        # Score-based trigger
        if score < 75:
            return True
        
        # Complexity triggers
        steps = plan.get("steps", [])
        if len(steps) > 3:
            return True
        
        # Context triggers
        goal = plan.get("goal", "").lower()
        context = str(plan.get("context", "")).lower()
        
        high_risk_keywords = [
            "production", "migration", "refactor", "architecture",
            "revenue", "customer", "database", "payment", "security"
        ]
        
        if any(kw in goal or kw in context for kw in high_risk_keywords):
            return True
        
        # Existing risk flags
        if len(plan.get("risks", [])) > 2:
            return True
        
        return False
    
    def _is_dev_plan(self, plan: Dict[str, Any]) -> bool:
        """Check if plan involves code changes."""
        goal = plan.get("goal", "").lower()
        
        dev_keywords = [
            "implement", "refactor", "add feature", "code",
            "function", "class", "module", "build", "develop"
        ]
        
        return any(kw in goal for kw in dev_keywords)
    
    def _get_codebase_context(self, repo_path: str) -> Optional[CodebaseContext]:
        """Get or create codebase context."""
        if not CODEBASE_AVAILABLE:
            return None
        
        if self._codebase_analyzer is None:
            self._codebase_analyzer = CodebaseAnalyzer()
            
            # Try loading cached
            graph = self._codebase_analyzer.load_cached(repo_path)
            if graph is None:
                # Analyze on demand (may be slow)
                self._codebase_analyzer.analyze_repository(
                    repo_path, languages=["python"], depth="standard"
                )
        
        return CodebaseContext(self._codebase_analyzer, repo_path)
    
    def enhanced_format_output(self, enhanced_result: Dict[str, Any]) -> str:
        """Format enhanced review result for display."""
        base = enhanced_result["base_review"]
        lines = []
        
        lines.append("=" * 70)
        lines.append("ENHANCED PLAN REVIEW")
        lines.append("=" * 70)
        lines.append("")
        
        # Base review summary
        lines.append(f"🎯 Goal: {base.original_plan.get('goal', 'N/A')}")
        lines.append(f"📊 Base Score: {base.scores.overall}/100")
        lines.append(f"📈 Adjusted Score: {enhanced_result['adjusted_score']}/100")
        lines.append(f"✅ Proceed: {base.recommend_proceed}")
        lines.append("")
        
        # Enrichments
        if enhanced_result["enrichments_applied"]:
            lines.append("🧠 Enrichments Applied:")
            for enrichment in enhanced_result["enrichments_applied"]:
                if enrichment == "premortem":
                    lines.append("   • Premortem Analysis — Assumed failure surfaced additional risks")
                elif enrichment == "codebase":
                    lines.append("   • Codebase Context — Complexity analysis added")
            lines.append("")
        
        # Premortem summary if present
        if "premortem_analysis" in enhanced_result:
            pm = enhanced_result["premortem_analysis"]
            lines.append("─" * 70)
            lines.append("⚠️  PREMORTEM INSIGHTS")
            lines.append("─" * 70)
            lines.append(f"Most Likely Failure: {pm['most_likely_failure']['scenario']}")
            lines.append(f"Optimism Bias: +{pm['optimism_bias_delta']}%")
            lines.append(f"Tail Risks: {len(pm['tail_risks'])} identified")
            lines.append(f"Hidden Assumptions: {len(pm['hidden_assumptions'])} exposed")
            lines.append("")
        
        # Codebase context if present
        if "codebase_context" in enhanced_result:
            ctx = enhanced_result["codebase_context"]
            lines.append("─" * 70)
            lines.append("📦 CODEBASE CONTEXT")
            lines.append("─" * 70)
            lines.append(f"Complexity: {ctx['complexity']}")
            lines.append(f"Dependency Depth: {ctx['dependency_depth']}")
            lines.append(f"Modules: {ctx['total_modules']}, Functions: {ctx['total_functions']}, Classes: {ctx['total_classes']}")
            if ctx['untested_files']:
                lines.append(f"Untested Files: {len(ctx['untested_files'])} found")
            lines.append("")
        
        # Enhanced recommendations
        lines.append("📝 ENHANCED RECOMMENDATIONS")
        for rec in enhanced_result["enhanced_recommendations"][-5:]:  # Last 5
            lines.append(f"   • {rec}")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


def enhanced_review(
    plan: Dict[str, Any],
    repo_path: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for enhanced review."""
    reviewer = EnhancedPlanReviewer()
    return reviewer.review_with_enhancements(plan, repo_path)


# Backwards compatibility
if PREMORTEM_AVAILABLE:
    __all__ = ["EnhancedPlanReviewer", "enhanced_review"]
else:
    # Fallback to base PlanReviewer if premortem not available
    EnhancedPlanReviewer = PlanReviewer
    __all__ = ["EnhancedPlanReviewer"]


if __name__ == "__main__":
    print("Enhanced Plan Reviewer module")
    print(f"Premortem available: {PREMORTEM_AVAILABLE}")
    print(f"Codebase understanding available: {CODEBASE_AVAILABLE}")
