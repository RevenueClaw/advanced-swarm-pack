#!/usr/bin/env python3
"""
PremortemAnalyzer — Structured failure analysis to counter optimism bias.

Implements Gary Klein-style premortem: Assume failure has occurred,
then construct narrative explaining how and why.

Author: RockClaw
Version: 1.0.0
"""

import json
import hashlib
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum


class RiskTolerance(Enum):
    """Risk tolerance levels for premortem analysis."""
    LOW = "low"      # Conservative: even small risks matter
    MEDIUM = "medium"  # Balanced: focus on significant risks
    HIGH = "high"    # Aggressive: only catastrophic risks matter


class DepthLevel(Enum):
    """Analysis depth for premortem."""
    QUICK = "quick"      # 2-3 min
    STANDARD = "standard"  # 5-7 min
    DEEP = "deep"        # 10-15 min


class FailureProbability(Enum):
    """Probability classification for failures."""
    CERTAIN = "certain"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNLIKELY = "unlikely"


class ImpactLevel(Enum):
    """Impact severity classification."""
    CATASTROPHIC = "catastrophic"
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@dataclass
class FailureMode:
    """A single failure scenario."""
    scenario: str
    probability: str
    impact: str
    root_cause: str
    contributing_factors: List[str]
    stage: str  # When it likely occurs


@dataclass
class TailRisk:
    """Low-probability, high-impact tail risk."""
    scenario: str
    probability: str
    impact: str
    trigger_condition: str
    mitigation: Optional[str] = None


@dataclass
class HiddenAssumption:
    """An unstated assumption that could cause failure."""
    assumption: str
    why_it_matters: str
    validation_strategy: str
    risk_if_wrong: str


@dataclass
class EarlyWarningIndicator:
    """Signal that the failure mode is materializing."""
    indicator: str
    threshold: str
    action: str
    stage: str
    severity: str


@dataclass
class Mitigation:
    """A specific action to prevent or reduce a failure."""
    action: str
    targets_failure: str
    effort: str  # small, medium, large
    effectiveness: str  # high, medium, low
    priority: str  # critical, high, medium, low


@dataclass
class RevisedStep:
    """An amended step with embedded risk mitigation."""
    original_step: str
    revised_step: str
    embeds_mitigation: str
    priority: str


@dataclass
class PremortemResult:
    """Complete premortem analysis result."""
    analysis_id: str
    goal: str
    risk_tolerance: str
    depth: str
    timestamp: str
    
    # Core analyses
    most_likely_failure: FailureMode
    failure_modes: List[FailureMode]
    tail_risks: List[TailRisk]
    hidden_assumptions: List[HiddenAssumption]
    
    # Outputs
    early_warning_indicators: List[EarlyWarningIndicator]
    mitigations: List[Mitigation]
    revised_plan: List[RevisedStep]
    
    # Risk assessment
    risk_score: int  # 0-100 (higher = safer after mitigation)
    optimism_bias_delta: int  # How far off was original optimism?
    
    # Plan adjustment
    original_score: Optional[int] = None
    adjusted_score: Optional[int] = None
    confidence_in_adjustment: Optional[str] = None
    
    # Metadata
    agent_version: str = "1.0.0"


class PremortemAnalyzer:
    """
    Performs structured premortem analysis on plans.
    
    Usage:
        analyzer = PremortemAnalyzer()
        result = analyzer.premortem(
            goal="Launch SBC price tracker",
            proposed_plan=["Build scraper", "Set up DB", "Deploy"],
            context="Production system with customers",
            risk_tolerance="medium",
            depth="standard"
        )
    """
    
    # Common failure patterns by domain
    DOMAIN_FAILURE_PATTERNS: Dict[str, List[str]] = {
        "software": [
            "Third-party API changes break integration",
            "Rate limiting causes cascading failures",
            "Database migration corrupts production data",
            "Dependency update introduces breaking change",
            "Memory leak causes production outage",
            "Race condition in concurrent code",
            "Configuration drift between environments",
            "Security vulnerability discovered post-launch",
            "Test coverage gaps hide critical bugs",
            "Scalability assumptions prove wrong"
        ],
        "data": [
            "Data source becomes unreliable or stops",
            "Schema change breaks downstream pipelines",
            "Data quality degrades silently",
            "ETL job runs too long, blocks imports",
            "Historical data missing/inconsistent",
            "Aggregation logic produces wrong results",
            "Privacy compliance issue discovered",
            "Storage costs exceed budget"
        ],
        "infrastructure": [
            "Service unavailable during peak hours",
            "Certificate expires without renewal",
            "Disk space runs out silently",
            "Network partition creates split-brain",
            "Backup fails silently for weeks",
            "Monitoring misses critical alerts",
            "Deployment pipeline breaks",
            "Credential rotation causes auth failures"
        ],
        "business": [
            "Key team member becomes unavailable",
            "Dependencies from other teams delayed",
            "Requirements change mid-project",
            "Budget cuts force scope reduction",
            "Legal/compliance issues block launch",
            "Customer demand lower than expected",
            "Competitor launches similar feature first",
            "Integration partner changes API/terms"
        ],
        "e-commerce": [
            "Amazon API rate limits exceeded",
            "Affiliate tracking fails silently",
            "Price data stale/incorrect",
            "Alert spam causes notification fatigue",
            "User churn from alert frequency",
            "Scraped site blocks IP/rate-limits",
            "Data integrity affects deal credibility",
            "Affiliate commission structure changes"
        ]
    }
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize the premortem analyzer.
        
        Args:
            storage_dir: Where to store analysis history (default: ~/.openclaw/premortems/)
        """
        self.storage_dir = storage_dir or Path.home() / ".openclaw" / "premortems"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_analysis_id(self, goal: str, timestamp: str) -> str:
        """Generate unique analysis ID."""
        content = f"{goal}-{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _detect_domain(self, goal: str, steps: List[str]) -> str:
        """Detect the domain of the plan for context."""
        combined_text = f"{goal} {' '.join(steps)}".lower()
        
        domain_keywords = {
            "software": ["code", "feature", "api", "database", "deploy", "build", "test", "migration"],
            "data": ["pipeline", "etl", "analytics", "report", "csv", "dataset", "warehouse"],
            "infrastructure": ["server", "host", "cloud", "certificate", "backup", "monitor"],
            "e-commerce": ["price", "product", "amazon", "scrape", "deal", "affiliate", "inventory"],
            "business": ["launch", "feature", "requirement", "stakeholder", "customer", "revenue"]
        }
        
        scores = {}
        for domain, keywords in domain_keywords.items():
            scores[domain] = sum(1 for kw in keywords if kw in combined_text)
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else "software"
    
    def _analyze_most_likely_failure(
        self,
        goal: str,
        steps: List[str],
        context: str,
        domain: str
    ) -> FailureMode:
        """Analyze the single most likely failure scenario."""
        
        # High-probability failure based on step count and complexity
        failure_scenarios = [
            {
                "scenario": f"Underestimated complexity in '{steps[1] if len(steps) > 1 else 'implementation'}' leading to schedule slip",
                "probability": FailureProbability.HIGH.value,
                "impact": ImpactLevel.MODERATE.value,
                "root_cause": "Optimism bias on familiar-looking tasks",
                "factors": ["Similar tasks have overrun before", "Edge cases not considered"]
            },
            {
                "scenario": f"Dependencies required by '{steps[2] if len(steps) > 2 else 'later steps'}' unavailable when needed",
                "probability": FailureProbability.HIGH.value,
                "impact": ImpactLevel.HIGH.value,
                "root_cause": "External dependencies assumed but not confirmed",
                "factors": ["Third-party schedules not aligned", "No explicit dependency tracking"]
            },
            {
                "scenario": "Integration issues between components discovered late",
                "probability": FailureProbability.MEDIUM.value,
                "impact": ImpactLevel.CRITICAL.value,
                "root_cause": "Components developed in isolation without integration testing",
                "factors": ["Interface assumptions mismatched", "Late discovery of integration complexity"]
            }
        ]
        
        # Add domain-specific scenarios
        if domain in self.DOMAIN_FAILURE_PATTERNS:
            for pattern in self.DOMAIN_FAILURE_PATTERNS[domain][:2]:
                failure_scenarios.append({
                    "scenario": pattern,
                    "probability": FailureProbability.MEDIUM.value,
                    "impact": ImpactLevel.HIGH.value,
                    "root_cause": f"Common {domain} failure pattern",
                    "factors": ["Insufficient validation of assumption", "No fallback strategy"]
                })
        
        # Select most likely based on context clues
        selected = failure_scenarios[0]
        
        if "time" in context.lower() or "schedule" in context.lower():
            selected = failure_scenarios[0]  # Schedule slip
        elif "depend" in context.lower() or "third" in context.lower():
            selected = failure_scenarios[1]  # Dependency failure
        elif "integration" in context.lower():
            selected = failure_scenarios[2]  # Integration issues
        
        return FailureMode(
            scenario=selected["scenario"],
            probability=selected["probability"],
            impact=selected["impact"],
            root_cause=selected["root_cause"],
            contributing_factors=selected["factors"],
            stage="middle"  # Most failures happen mid-project
        )
    
    def _analyze_additional_failures(
        self,
        goal: str,
        steps: List[str],
        context: str,
        depth: DepthLevel,
        domain: str
    ) -> List[FailureMode]:
        """Analyze additional failure modes beyond the most likely."""
        failures = []
        
        # Number of failures based on depth
        count = {
            DepthLevel.QUICK: 2,
            DepthLevel.STANDARD: 4,
            DepthLevel.DEEP: 6
        }.get(depth, 3)
        
        # Domain-specific patterns
        domain_patterns = self.DOMAIN_FAILURE_PATTERNS.get(domain, [])
        
        common_failures = [
            {
                "scenario": "Scope creep adds unplanned work",
                "prob": FailureProbability.HIGH.value,
                "impact": ImpactLevel.MODERATE.value,
                "root": "Boundary between in/out of scope not defined",
                "stage": "late"
            },
            {
                "scenario": "Key stakeholder feedback invalidates approach",
                "prob": FailureProbability.MEDIUM.value,
                "impact": ImpactLevel.CRITICAL.value,
                "root": "Insufficient stakeholder alignment upfront",
                "stage": "middle"
            },
            {
                "scenario": "Technical debt from rushed early implementation",
                "prob": FailureProbability.MEDIUM.value,
                "impact": ImpactLevel.HIGH.value,
                "root": "Speed prioritized over quality in initial phases",
                "stage": "late"
            },
            {
                "scenario": "Testing reveals fundamental flaw in design",
                "prob": FailureProbability.LOW.value,
                "impact": ImpactLevel.CRITICAL.value,
                "root": "Design review skipped or inadequately thorough",
                "stage": "late"
            },
            {
                "scenario": "Team member availability changes during project",
                "prob": FailureProbability.MEDIUM.value,
                "impact": ImpactLevel.HIGH.value,
                "root": "Bus factor of 1 on critical knowledge",
                "stage": "middle"
            }
        ]
        
        # Add domain-specific failures
        for pattern in domain_patterns[:3]:
            common_failures.append({
                "scenario": pattern,
                "prob": FailureProbability.MEDIUM.value,
                "impact": ImpactLevel.HIGH.value,
                "root": f"Pattern from {domain} domain",
                "stage": "middle"
            })
        
        # Select diverse failures
        selected = random.sample(common_failures, min(count, len(common_failures)))
        
        for f in selected:
            failures.append(FailureMode(
                scenario=f["scenario"],
                probability=f["prob"],
                impact=f["impact"],
                root_cause=f["root"],
                contributing_factors=["Timeline pressure", "Inadequate planning"],
                stage=f["stage"]
            ))
        
        return failures
    
    def _identify_tail_risks(
        self,
        goal: str,
        context: str,
        depth: DepthLevel,
        domain: str
    ) -> List[TailRisk]:
        """Identify low-probability, catastrophic tail risks."""
        risks = []
        
        tail_risk_candidates = [
            {
                "scenario": "Complete data loss during migration",
                "prob": FailureProbability.UNLIKELY.value,
                "impact": ImpactLevel.CATASTROPHIC.value,
                "trigger": "Migration script runs without proper backup"
            },
            {
                "scenario": "Security breach exposing customer data",
                "prob": FailureProbability.UNLIKELY.value,
                "impact": ImpactLevel.CATASTROPHIC.value,
                "trigger": "Vulnerability in third-party dependency"
            },
            {
                "scenario": "Key supplier/partnership terminates unexpectedly",
                "prob": FailureProbability.LOW.value,
                "impact": ImpactLevel.CRITICAL.value,
                "trigger": "Contract renewal fails"
            },
            {
                "scenario": "Regulatory action halts operations",
                "prob": FailureProbability.UNLIKELY.value,
                "impact": ImpactLevel.CATASTROPHIC.value,
                "trigger": "Compliance requirement missed"
            },
            {
                "scenario": "Competitor launches superior solution simultaneously",
                "prob": FailureProbability.LOW.value,
                "impact": ImpactLevel.CRITICAL.value,
                "trigger": "Market timing coincidence"
            }
        ]
        
        # Domain-specific tail risks
        if domain == "e-commerce":
            tail_risk_candidates.append({
                "scenario": "Amazon affiliate account revoked for TOS violation",
                "prob": FailureProbability.LOW.value,
                "impact": ImpactLevel.CRITICAL.value,
                "trigger": "Scraping behavior flagged as policy violation"
            })
            tail_risk_candidates.append({
                "scenario": "Price data inaccuracy leads to legal liability",
                "prob": FailureProbability.LOW.value,
                "impact": ImpactLevel.CRITICAL.value,
                "trigger": "User makes purchase decision based on incorrect price"
            })
        
        # Select based on depth
        count = {
            DepthLevel.QUICK: 1,
            DepthLevel.STANDARD: 2,
            DepthLevel.DEEP: 3
        }.get(depth, 2)
        
        selected = tail_risk_candidates[:count]  # Take highest impact first
        
        for r in selected:
            risks.append(TailRisk(
                scenario=r["scenario"],
                probability=r["prob"],
                impact=r["impact"],
                trigger_condition=r["trigger"],
                mitigation=None
            ))
        
        return risks
    
    def _expose_hidden_assumptions(
        self,
        goal: str,
        steps: List[str],
        context: str,
        depth: DepthLevel
    ) -> List[HiddenAssumption]:
        """Expose unstated assumptions that could cause failure."""
        assumptions = []
        
        # Common assumptions that often prove false
        assumption_candidates = [
            {
                "assumption": "Current technology choices remain optimal throughout project",
                "why": "Better solutions may emerge or current ones deprecated",
                "validate": "Monthly tech landscape review",
                "risk": "Technical debt or forced migration mid-project"
            },
            {
                "assumption": "Team has required skills for all planned tasks",
                "why": "Underestimating learning curve on unfamiliar technologies",
                "validate": "Skills audit + training buffer",
                "risk": "Tasks taking 2-3x longer than estimated"
            },
            {
                "assumption": "External dependencies remain available and unchanged",
                "why": "APIs, services, and libraries evolve",
                "validate": "Monitor deprecation notices, have fallback options",
                "risk": "Last-minute architecture changes required"
            },
            {
                "assumption": "Stakeholder priorities remain stable",
                "why": "Business priorities shift in response to market",
                "validate": "Weekly stakeholder sync",
                "risk": "Mid-project scope changes or cancellation"
            },
            {
                "assumption": "Performance at scale matches current testing",
                "why": "Real load patterns differ from synthetic tests",
                "validate": "Load test with realistic traffic patterns",
                "risk": "Production performance unacceptable"
            },
            {
                "assumption": "No competing projects consuming shared resources",
                "why": "Resource contention with other teams",
                "validate": "Resource availability commitment from management",
                "risk": "Timeline slips due to unavailable resources"
            },
            {
                "assumption": "Regulatory/compliance environment remains stable",
                "why": "New regulations can impose unexpected requirements",
                "validate": "Legal review of pending regulations",
                "risk": "Launch blocked by compliance requirements"
            }
        ]
        
        # Select based on depth
        count = {
            DepthLevel.QUICK: 3,
            DepthLevel.STANDARD: 5,
            DepthLevel.DEEP: 7
        }.get(depth, 5)
        
        selected = assumption_candidates[:count]
        
        for a in selected:
            assumptions.append(HiddenAssumption(
                assumption=a["assumption"],
                why_it_matters=a["why"],
                validation_strategy=a["validate"],
                risk_if_wrong=a["risk"]
            ))
        
        return assumptions
    
    def _generate_early_warnings(
        self,
        failure_modes: List[FailureMode],
        tail_risks: List[TailRisk],
        steps: List[str]
    ) -> List[EarlyWarningIndicator]:
        """Create early warning indicators for monitoring."""
        ewis = []
        
        # Generic early warning indicators
        generic_ewis = [
            {
                "indicator": "Timeline variance exceeds 20%",
                "threshold": "Any major task",
                "action": "Escalate to stakeholders, consider scope reduction",
                "stage": "any",
                "severity": "high"
            },
            {
                "indicator": "Test coverage below 80%",
                "threshold": "Any module",
                "action": "Block merge, require additional tests",
                "stage": "development",
                "severity": "critical"
            },
            {
                "indicator": "Critical bug open >48 hours",
                "threshold": "Any P0/P1 issue",
                "action": "Emergency team huddle, potential rollback",
                "stage": "testing",
                "severity": "critical"
            },
            {
                "indicator": "Dependency version conflicts",
                "threshold": "Any incompatibility detected",
                "action": "Pin versions, evaluate alternatives",
                "stage": "development",
                "severity": "high"
            },
            {
                "indicator": "Performance degradation >30%",
                "threshold": "Any key metric",
                "action": "Performance profiling, optimization sprint",
                "stage": "testing",
                "severity": "high"
            },
            {
                "indicator": "Stakeholder feedback delays >1 week",
                "threshold": "Any review checkpoint",
                "action": "Executive escalation, async approval process",
                "stage": "any",
                "severity": "medium"
            }
        ]
        
        # Add failure-mode specific EWIs
        for failure in failure_modes:
            if "API" in failure.scenario or "rate" in failure.scenario.lower():
                generic_ewis.append({
                    "indicator": "API response time >2s or error rate >1%",
                    "threshold": "3 consecutive requests",
                    "action": "Enable fallback mode, alert on-call",
                    "stage": "production",
                    "severity": "critical"
                })
            if "database" in failure.scenario.lower():
                generic_ewis.append({
                    "indicator": "Query performance degradation",
                    "threshold": "P95 >500ms",
                    "action": "Optimize queries, add indexes",
                    "stage": "testing",
                    "severity": "high"
                })
            if "integration" in failure.scenario.lower():
                generic_ewis.append({
                    "indicator": "Integration test failures",
                    "threshold": "Any failure",
                    "action": "Halt feature work, fix integration first",
                    "stage": "testing",
                    "severity": "critical"
                })
        
        for ewi in generic_ewis[:8]:  # Cap at 8 EWIs
            ewis.append(EarlyWarningIndicator(
                indicator=ewi["indicator"],
                threshold=ewi["threshold"],
                action=ewi["action"],
                stage=ewi["stage"],
                severity=ewi["severity"]
            ))
        
        return ewis
    
    def _design_mitigations(
        self,
        failure_modes: List[FailureMode],
        tail_risks: List[TailRisk],
        hidden_assumptions: List[HiddenAssumption]
    ) -> List[Mitigation]:
        """Design specific mitigations for identified risks."""
        mitigations = []
        
        # Failure mode mitigations
        for failure in failure_modes[:3]:  # Top 3 failures
            mitigations.append(Mitigation(
                action=f"Regular checkpoint on: {failure.root_cause}",
                targets_failure=failure.scenario,
                effort="medium",
                effectiveness="medium",
                priority="high" if failure.probability in ["certain", "high"] else "medium"
            ))
        
        # Tail risk mitigations
        for risk in tail_risks:
            if "backup" in risk.scenario.lower() or "data" in risk.scenario.lower():
                mitigations.append(Mitigation(
                    action="Implement 3-2-1 backup strategy + tested restore",
                    targets_failure=risk.scenario,
                    effort="medium",
                    effectiveness="high",
                    priority="critical"
                ))
            elif "security" in risk.scenario.lower():
                mitigations.append(Mitigation(
                    action="Security audit + dependency vulnerability scanning",
                    targets_failure=risk.scenario,
                    effort="large",
                    effectiveness="high",
                    priority="critical"
                ))
            elif "rate" in risk.scenario.lower() or "limit" in risk.scenario.lower():
                mitigations.append(Mitigation(
                    action="Implement circuit breaker + exponential backoff",
                    targets_failure=risk.scenario,
                    effort="small",
                    effectiveness="high",
                    priority="critical"
                ))
        
        # Assumption validation mitigations
        for assumption in hidden_assumptions[:2]:
            mitigations.append(Mitigation(
                action=f"Validate: {assumption.validation_strategy}",
                targets_failure=assumption.assumption,
                effort="small",
                effectiveness="medium",
                priority="medium"
            ))
        
        return mitigations
    
    def _revise_plan_with_mitigations(
        self,
        steps: List[str],
        mitigations: List[Mitigation],
        failure_modes: List[FailureMode]
    ) -> List[RevisedStep]:
        """Revised plan with embedded mitigations."""
        revised = []
        
        for i, step in enumerate(steps):
            # Find relevant mitigations
            relevant = [m for m in mitigations if i < 2 or m.priority == "critical"]
            
            if relevant and i == 0:
                # Add validation checkpoint to first step
                mitigation_text = f"[Validate assumptions: {relevant[0].action}]"
                revised.append(RevisedStep(
                    original_step=step,
                    revised_step=f"{step} {mitigation_text}",
                    embeds_mitigation=relevant[0].action,
                    priority="high"
                ))
            elif relevant and i == len(steps) - 1:
                # Add verification to last step
                mitigation_text = f"[Verify against: {relevant[0].targets_failure}]"
                revised.append(RevisedStep(
                    original_step=step,
                    revised_step=f"{step} {mitigation_text}",
                    embeds_mitigation=relevant[0].action,
                    priority="high"
                ))
            else:
                revised.append(RevisedStep(
                    original_step=step,
                    revised_step=step,
                    embeds_mitigation="",
                    priority="medium"
                ))
        
        # Insert additional critical mitigation steps
        critical_mitigations = [m for m in mitigations if m.priority == "critical"]
        for i, m in enumerate(critical_mitigations[:2]):
            revised.insert(1 + i, RevisedStep(
                original_step="",
                revised_step=f"[MITIGATION] {m.action} — prevents: {m.targets_failure[:50]}...",
                embeds_mitigation=m.action,
                priority="critical"
            ))
        
        return revised
    
    def _calculate_risk_score(
        self,
        failure_modes: List[FailureMode],
        tail_risks: List[TailRisk],
        hidden_assumptions: List[HiddenAssumption],
        mitigations: List[Mitigation]
    ) -> int:
        """Calculate overall risk score (0-100, higher is safer)."""
        
        # Base score
        score = 50
        
        # Deduct for failures (weighted by probability)
        prob_weights = {"certain": -15, "high": -10, "medium": -5, "low": -2, "unlikely": -1}
        for failure in failure_modes:
            score += prob_weights.get(failure.probability, -5)
        
        # Deduct for tail risks (high impact)
        for risk in tail_risks:
            score += prob_weights.get(risk.probability, -2) * 2  # Tail risks weighted more
        
        # Deduct for unvalidated assumptions
        score -= len(hidden_assumptions) * 3
        
        # Add back for mitigations
        for m in mitigations:
            eff_weights = {"high": 8, "medium": 5, "low": 2}
            score += eff_weights.get(m.effectiveness, 5)
        
        # Clamp to 0-100
        return max(0, min(100, score))
    
    def _calculate_optimism_bias(self, proposed: List[str], failures: List[FailureMode]) -> int:
        """Estimate how far off typical optimism might be."""
        # Simple heuristic: more steps = more opportunity for underestimation
        if len(proposed) <= 2:
            return len(failures) * 10  # Small projects still have bias
        else:
            return min(50, len(proposed) * 8 + len(failures) * 5)
    
    def premortem(
        self,
        goal: str,
        proposed_plan: List[str],
        context: str = "",
        risk_tolerance: str = "medium",
        depth: str = "standard",
        original_score: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute full premortem analysis.
        
        Args:
            goal: The goal or project description
            proposed_plan: List of planned steps/actions
            context: Additional context (domain, constraints, stakeholders)
            risk_tolerance: low/medium/high
            depth: quick/standard/deep
            original_score: Optional original PlanReviewer score for delta
        
        Returns:
            Complete premortem analysis as dictionary
        """
        depth_enum = DepthLevel(depth)
        tolerance_enum = RiskTolerance(risk_tolerance)
        timestamp = datetime.utcnow().isoformat()
        
        domain = self._detect_domain(goal, proposed_plan)
        
        # Run all analyses
        most_likely = self._analyze_most_likely_failure(goal, proposed_plan, context, domain)
        failures = self._analyze_additional_failures(goal, proposed_plan, context, depth_enum, domain)
        failures = [most_likely] + failures  # Most likely first
        
        tail_risks = self._identify_tail_risks(goal, context, depth_enum, domain)
        assumptions = self._expose_hidden_assumptions(goal, proposed_plan, context, depth_enum)
        ewis = self._generate_early_warnings(failures, tail_risks, proposed_plan)
        mitigations = self._design_mitigations(failures, tail_risks, assumptions)
        revised = self._revise_plan_with_mitigations(proposed_plan, mitigations, failures)
        
        # Calculate scores
        risk_score = self._calculate_risk_score(failures, tail_risks, assumptions, mitigations)
        optimism_delta = self._calculate_optimism_bias(proposed_plan, failures)
        
        # Calculate adjusted score if original provided
        adjusted_score = None
        confidence = None
        if original_score is not None:
            # If we have good mitigations, score should improve
            mitigation_effectiveness = sum(1 for m in mitigations if m.effectiveness == "high")
            if mitigation_effectiveness >= 2:
                adjusted_score = min(95, original_score + 15)
                confidence = "high"
            else:
                adjusted_score = min(95, original_score + 5)
                confidence = "medium"
        
        # Build result
        result = PremortemResult(
            analysis_id=self._generate_analysis_id(goal, timestamp),
            goal=goal,
            risk_tolerance=risk_tolerance,
            depth=depth,
            timestamp=timestamp,
            most_likely_failure=most_likely,
            failure_modes=failures,
            tail_risks=tail_risks,
            hidden_assumptions=assumptions,
            early_warning_indicators=ewis,
            mitigations=mitigations,
            revised_plan=revised,
            risk_score=risk_score,
            optimism_bias_delta=optimism_delta,
            original_score=original_score,
            adjusted_score=adjusted_score,
            confidence_in_adjustment=confidence
        )
        
        # Cache result
        self._cache_result(result)
        
        return asdict(result)
    
    def _cache_result(self, result: PremortemResult) -> None:
        """Cache analysis result to storage."""
        cache_file = self.storage_dir / f"{result.analysis_id}.json"
        with open(cache_file, 'w') as f:
            json.dump(asdict(result), f, indent=2)
    
    def get_cached_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis by ID."""
        cache_file = self.storage_dir / f"{analysis_id}.json"
        if cache_file.exists():
            with open(cache_file) as f:
                return json.load(f)
        return None
    
    def analyze_risk(self, goal: str, steps: List[str], **kwargs) -> Dict[str, Any]:
        """Quick alias for premortem with quick defaults."""
        kwargs.setdefault("depth", "quick")
        return self.premortem(goal=goal, proposed_plan=steps, **kwargs)
    
    def generate_ewis(self, analysis: Dict[str, Any], stage: str = "any") -> List[Dict[str, Any]]:
        """Extract early warning indicators for a specific stage."""
        all_ewis = analysis.get("early_warning_indicators", [])
        if stage == "any":
            return all_ewis
        return [e for e in all_ewis if e.get("stage") == stage or e.get("stage") == "any"]
    
    def format_for_architect(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Format premortem output for Architect-First PlanReviewer integration."""
        return {
            "risk_adjustment": {
                "original_score": analysis.get("original_score"),
                "adjusted_score": analysis.get("adjusted_score"),
                "confidence": analysis.get("confidence_in_adjustment"),
                "optimism_bias_delta": analysis.get("optimism_bias_delta")
            },
            "additional_risks": [f["scenario"] for f in analysis.get("failure_modes", [])],
            "tail_risks": [f["scenario"] for f in analysis.get("tail_risks", [])],
            "hidden_assumptions": [a["assumption"] for a in analysis.get("hidden_assumptions", [])],
            "ewis_for_acceptance_criteria": [
                f"{e['indicator']} (threshold: {e['threshold']})"
                for e in analysis.get("early_warning_indicators", [])[:4]
            ],
            "mitigation_steps": [m["action"] for m in analysis.get("mitigations", []) if m["priority"] == "critical"],
            "revised_plan": analysis.get("revised_plan", [])
        }


def demo():
    """Run a demo premortem analysis."""
    print("=" * 60)
    print("PREMORTEM ANALYSIS DEMO")
    print("=" * 60)
    
    analyzer = PremortemAnalyzer()
    
    result = analyzer.premortem(
        goal="Launch ChipRadar price tracking alerts",
        proposed_plan=[
            "Integrate Amazon API for price data",
            "Build alert notification system",
            "Deploy to production with monitoring"
        ],
        context="Production system with affiliate revenue, e-commerce domain",
        risk_tolerance="medium",
        depth="standard",
        original_score=72
    )
    
    print(f"\n🎯 Goal: {result['goal']}")
    print(f"📊 Risk Score: {result['risk_score']}/100")
    print(f"😊 Optimism Bias Delta: +{result['optimism_bias_delta']}%")
    
    if result['adjusted_score']:
        print(f"📈 Score Adjustment: {result['original_score']} → {result['adjusted_score']} ({result['confidence_in_adjustment']})")
    
    print(f"\n⚠️  Most Likely Failure:")
    print(f"   {result['most_likely_failure']['scenario']}")
    print(f"   Root cause: {result['most_likely_failure']['root_cause']}")
    
    print(f"\n🔥 Tail Risks ({len(result['tail_risks'])} identified):")
    for risk in result['tail_risks'][:2]:
        print(f"   - {risk['scenario']} ({risk['probability']} probability)")
    
    print(f"\n💡 Hidden Assumptions ({len(result['hidden_assumptions'])} identified):")
    for assumption in result['hidden_assumptions'][:3]:
        print(f"   - {assumption['assumption'][:70]}...")
    
    print(f"\n🛡️  Critical Mitigations ({len(result['mitigations'])} total):")
    critical_mits = [m for m in result['mitigations'] if m['priority'] == 'critical']
    for m in critical_mits[:3]:
        print(f"   - {m['action'][:70]}...")
    
    print(f"\n✅ Early Warning Indicators ({len(result['early_warning_indicators'])} generated)")
    print(f"📝 Analysis ID: {result['analysis_id']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()
