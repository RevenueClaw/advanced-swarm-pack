# Premortem Analysis (v1)

Counter optimism bias and surface hidden risks with structured "future failure" analysis.

## Philosophy

**Gary Klein Premortem:** Imagine the plan has already failed spectacularly in 6 months. Now explain how and why.

This technique:
- Short-circuits optimism bias by assuming failure
- Surfaces hidden risks through narrative construction  
- Reveals unstated assumptions by examining failure paths
- Creates early warning indicators before they're visible
- Builds anti-fragility through preemptive mitigation

## Core Components

### Standalone Premortem

```python
from lib.premortem_analyzer import PremortemAnalyzer

analyzer = PremortemAnalyzer()
analysis = analyzer.premortem(
    goal="Implement feature X",
    proposed_plan=["Step 1", "Step 2", "Step 3"],
    context="Customer-facing production system",
    risk_tolerance="low",  # low, medium, high
    depth="deep"  # quick, standard, deep
)

print(f"Risk Score: {analysis['risk_score']}")
print(f"Failure Modes: {len(analysis['failure_modes'])}")
```

### Integration with Architect-First

Auto-trigger premortem in PlanReviewer for:
- Score <75 plans needing extra scrutiny
- Risk flags present in initial review
- Plans with >3 tasks or high complexity

```python
from lib.premortem_analyzer import PremortemAnalyzer

# In PlanReviewer.review():
if scores.overall < 75 or len(plan.get('risks', [])) > 2:
    premortem_analysis = self.premortem.premortem(
        goal=plan['goal'],
        proposed_plan=plan['steps'],
        context=context,
        risk_tolerance=risk_tolerance,
        depth="standard"
    )
    reviewed_plan.premortem_analysis = premortem_analysis
```

## Output Structure

### Failure Modes

```json
{
  "most_likely_failure": {
    "scenario": "Third-party API rate limits cause cascading failures",
    "probability": "high",
    "impact": "customer-facing outage",
    "root_cause": "No rate limiting strategy or fallback defined"
  },
  "tail_risks": [
    {
      "scenario": "Database corruption during migration",
      "probability": "low",
      "impact": "catastrophic",
      "mitigation": "Pre-migration backup + rollback tested"
    }
  ],
  "hidden_assumptions": [
    "Assumes API remains stable during migration",
    "Assumes team availability for 2 weeks",
    "Assumes no major customer escalations"
  ]
}
```

### Revised Plan with Mitigations

```json
{
  "revised_steps": [
    {
      "step": "Implement API rate limiter",
      "mitigation_for": "Most Likely Failure",
      "priority": "critical"
    },
    {
      "step": "Test fallback to cached data",
      "mitigation_for": "API dependency risk",
      "priority": "high"
    }
  ],
  "risk_adjusted_score": {
    "original": 68,
    "post_premortem": 85,
    "adjustment_delta": 17,
    "confidence": "high"
  }
}
```

### Early Warning Indicators (EWIs)

```json
{
  "early_warning_indicators": [
    {
      "indicator": "API response time >2s",
      "threshold": "3 consecutive requests",
      "action": "Enable fallback mode, alert on-call",
      "stage": "deployment"
    },
    {
      "indicator": "Test coverage below 80%",
      "threshold": "any module",
      "action": "Block merge, require additional tests",
      "stage": "pre-deployment"
    }
  ]
}
```

## Depth Levels

| Level | Time | Best For |
|-------|------|----------|
| **quick** | 2-3 min | Simple tasks, low risk |
| **standard** | 5-7 min | Most plans, medium complexity |
| **deep** | 10-15 min | High stakes, novel territory, >5 tasks |

## Integration Points

### skill-architect-first
- Auto-trigger for score <75 or plans with risk flags
- Risk score adjustment for PlanReviewer
- Adds EWIs to acceptance criteria
- Updates rollback plan based on uncovered risks

### skill-estimation-engine
- Adjust time estimates for mitigation work
- Add buffers for tail-risk scenarios
- Create separate "risk-adjusted" vs "optimistic" estimates

### skill-consensus
- Include premortem analysis in debate context
- Debate panel can challenge failure scenarios
- Risk appetite alignment with human/organizational tolerance

## Files

- `lib/premortem_analyzer.py` - Core analysis engine (~550 lines)
- `lib/integrations.py` - Hooks for Architect-First, Estimation Engine, Consensus
- `docs/premortem-guide.md` - When and how to use premortems
- `examples/sample-analyses.json` - Real-world premortem examples

## Quick Reference

```python
# Quick inline use
from lib.premortem_analyzer import PremortemAnalyzer
pa = PremortemAnalyzer()
result = pa.analyze_risk("Launch new pricing page", 
                        steps=["Design", "Build", "Test"],
                        depth="quick")

# Integration with PlanReviewer
# (Auto-injected when score <75 or risk flags present)

# Get early warning indicators for monitoring
ewis = pa.generate_ewis(analysis, stage="deployment")
```

## Risk Score Adjustment

Post-premortem, the PlanReviewer risk assessment score is recalibrated:

- **If majority of failure modes have mitigations**: Score *increases* (plan is stronger)
- **If catastrophic tail risks discovered**: Score *decreases* (hidden danger found)
- **If EWIs actionable**: Score *increases* (early detection capability)

Typical adjustments: -15 to +20 points Final score capped at 95 (premortem itself isn't perfect)
