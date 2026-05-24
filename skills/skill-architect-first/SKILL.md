# Architect-First Planning

Implements the Architect-First discipline for high-quality planning with self-critique, scoring, and rollback planning.

## Philosophy

**80/20 Planning Rule:** Spend ~80% of time understanding and planning before committing to execution (20%).

This approach:
- Catches problems early when they're cheap to fix
- Forces clear thinking before action
- Creates safety nets (rollback plans)
- Integrates with HITL for escalation

## Core Components

### PlanReviewer

Main class that reviews plans before execution.

```python
from lib.plan_reviewer import PlanReviewer

reviewer = PlanReviewer()
reviewed = reviewer.review({
    "goal": "Implement feature X",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "risks": ["Risk A", "Risk B"],
    "success_criteria": ["Criterion 1", "Criterion 2"]
})

if reviewed.recommend_proceed:
    execute_plan(reviewed)
else:
    should_escalate, reason = reviewer.should_escalate(reviewed)
    if should_escalate:
        ask_human_for_guidance(reviewed.critiques)
```

### Scoring Dimensions

| Dimension | Weight | Checks |
|-----------|--------|--------|
| Clarity | 25% | SMART goal, specificity |
| Risk Assessment | 30% | Risks identified, rollback present |
| Completeness | 20% | Steps detailed, dependencies clear |
| Feasibility | 15% | Time estimates, resources |
| Testability | 10% | Success criteria defined |

### Scoring Thresholds

- **90-100 (Excellent):** Proceed with confidence
- **70-89 (Good):** Proceed with minor improvements
- **50-69 (Acceptable):** Needs revision before proceeding
- **<50 (Needs Revision):** Do not proceed, escalate

### Automatic Escalation Triggers

- Score <60/100
- 2+ critical issues
- Execution confidence <50%

## Usage in Hierarchical Orchestrator

The PlanReviewer integrates at the planning phase:

```python
def handle_complex_task(goal, complexity):
    # Generate draft plan
    draft = generate_plan(goal)
    
    # Review if medium+ complexity
    if complexity >= Complexity.MEDIUM:
        reviewed = plan_reviewer.review(draft)
        
        if not reviewed.recommend_proceed:
            should_escalate, reason = reviewer.should_escalate(reviewed)
            if should_escalate:
                return escalate_to_user(reviewed)
    
    # Execute with acceptance criteria from review
    return execute_plan(reviewed.original_plan, 
                       acceptance=reviewed.acceptance_criteria)
```

## Files

- `lib/plan_reviewer.py` - Core review engine (699 lines)
- `plans/plan-reviews.jsonl` - Review history

## Output Format

Each review includes:
- 5-dimensional scoring
- Self-critiques with severity levels
- Generated acceptance criteria
- Rollback plan with triggers
- proceed/don't proceed recommendation
