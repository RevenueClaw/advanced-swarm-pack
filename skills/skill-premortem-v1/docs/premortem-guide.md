# Premortem Analysis Guide

## What is a Premortem?

A premortem is a simple but powerful technique to overcome optimism bias in planning.

Instead of asking "What could go wrong?" (prospective thinking), a premortem asks:

> **"Imagine it's 6 months from now. The plan has failed spectacularly. What happened?"**

This subtle shift activates our ability to construct narratives about the future, which is
different from simply listing risks. We naturally think in stories, and the premortem
leverages this to surface hidden failure modes.

## Why It Works

### 1. Overcoming Optimism Bias

Research by Gary Klein and others shows that teams consistently underestimate:
- Time to completion (planning fallacy)
- Likelihood of problems
- Impact of external factors

By assuming failure has occurred, we short-circuit the "this time will be different" thinking.

### 2. Surfacing Hidden Assumptions

We make hundreds of unstated assumptions every day:
- "The API won't change"
- "The team will stay stable"
- "We'll have resources when needed"

These assumptions usually work — until they don't. The premortem explicitly tests them.

### 3. Creating Actionable Outputs

Unlike generic "risk analysis," a good premortem produces:
- **Most Likely Failure**: The single biggest risk to address
- **Tail Risks**: Black swans that need mitigation
- **Early Warning Indicators**: Signals to watch for
- **Mitigation Steps**: Concrete actions to prevent/survive failure

## When to Use Premortem

| Scenario | Recommendation |
|----------|----------------|
| Simple task (<2 steps) | Skip premortem |
| Standard task (2-3 steps) | Quick premortem (2 min) |
| Complex task (>3 steps) | Standard premortem |
| Production deployment | Standard/Deep premortem |
| Revenue-critical work | Always run premortem |
| Novel territory | Deep premortem |
| Database migrations | Deep premortem + backup verification |
| Customer-facing changes | Standard premortem |

## The Process

### Quick Premortem (2-3 minutes)
1. State the goal clearly
2. Assume it has failed in 6 months
3. Identify the single most likely failure
4. List 2 additional failure modes
5. Identify 3 hidden assumptions
6. Set 2 early warning indicators

### Standard Premortem (5-7 minutes)
1-4. Same as quick
5. Identify 5 hidden assumptions
6. Identify 2 tail risks
7. Set 4 early warning indicators
8. Design 3-4 mitigations
9. Revise plan with mitigations embedded

### Deep Premortem (10-15 minutes)
Full standard premortem plus:
- Analyze dependencies more thoroughly
- Consider second-order effects
- Design redundant mitigations
- Plan fallback strategies

## Integration with Swarm Skills

### Architect-First Planning

The PlanReviewer auto-triggers premortem when:
- Plan score <75
- More than 3 steps
- Keywords detected ("production", "migration", "revenue")

The premortem result feeds into:
- Risk score adjustment (+5 to +15 points if well-mitigated)
- Enhanced rollback plan based on failure modes
- Acceptance criteria enriched with EWIs
- Critical mitigations added to first steps

### Estimation Engine

Tail risks from premortem automatically add buffers:
- 2+ tail risks: +25% to estimates
- 1 tail risk: +15% to estimates
- Hidden assumptions not validated: +10%

This is *on top of* baseline buffers (novel=+50%, standard=+30%, known=+20%).

### Consensus & Debate

Premortem provides the conservative persona with evidence:
> "The premortem identified these tail risks that we should consider..."

This grounds abstract worries in concrete failure scenarios.

## Understanding the Output

### Risk Score (0-100)

- **0-30**: Dangerous — multiple unmitigated catastrophic risks
- **30-50**: Risky — significant work needed before proceeding
- **50-70**: Moderate — address key mitigations
- **70-85**: Good — standard monitoring sufficient
- **85-100**: Excellent — well protected

### Optimism Bias Delta

How much longer might this actually take than estimated? Use this to sanity-check
estimation engine output.

- <10%: Good estimate quality
- 10-25%: Typical underestimation
- 25-40%: Significant optimism present
- >40%: Major planning gaps, consider restructuring

### Early Warning Indicators

Watch these like a hiker watches weather signs:
- **Critical**: Stop and address immediately
- **High**: Prioritize fixing soon
- **Medium**: Track and monitor

## Examples

### Example 1: API Integration (E-commerce)

**Goal**: Add Amazon affiliate product search

**Most Likely Failure**: Rate limits exceeded during peak hours
**Tail Risk**: Affiliate account suspended for TOS violation
**Hidden Assumption**: Assumes Amazon API remains free/accessible

**Mitigation**:
1. Circuit breaker + exponential backoff (critical)
2. Cached fallback data (high)
3. Rate limit dashboard monitoring (medium)

**EWI**: API error rate >1% for 3 consecutive calls

### Example 2: Database Migration

**Goal**: Migrate users table to new schema

**Most Likely Failure**: Migration runs too long, blocks deploy
**Tail Risk**: Data corruption during migration
**Hidden Assumption**: All data conforms to expected schema

**Mitigation**:
1. Test migration on production-sized dump first (critical)
2. 3-2-1 backup before migration (critical)
3. Time-bounded migration with rollback tested (critical)

**EWI**: Migration running >30 min (threshold: 20 min buffer planned)

## Anti-Patterns

### ❌ Don't: Treat It as Doom and Gloom

Premortem isn't pessimism for pessimism's sake. It's finding problems so you can fix
them, not just complain about them.

### ❌ Don't: Ignore the Results

If you run a premortem but don't change the plan, you've wasted time. Either the
mitigations get built into the plan, or you're accepting risk knowingly.

### ❌ Don't: Over-Engineer for Tail Risks

Yes, prepare for tail risks, but don't let low-probability events paralyze progress.
"3-2-1 backups" don't cost much; "5 levels of redundant failover" probably do.

### ✅ Do: Embed Mitigations in Plan

Don't just list mitigations as "nice to have" — they should be explicit steps
in the revised plan.

### ✅ Do: Set Realistic EWIs

An early warning indicator that triggers too often becomes noise, and one that
triggers too late is useless. Calibrate carefully.

### ✅ Do: Revisit Post-Execution

After the plan completes (success or failure), compare what actually happened
to what the premortem predicted. This calibration improves future premortems.

## Troubleshooting

### "I keep getting the same generic results"

- Tune the context parameter with domain-specific details
- Use deeper analysis level
- Focus on specific steps rather than the overall goal
- Include more constraints (budget, timeline, resources)

### "Risk score is always too low/high"

The risk score is directional, not absolute. Compare relative scores between plans
rather than treating the number as gospel.

### "Mitigations seem generic"

- Add domain context to identify more specific mitigations
- Look at your actual past project failures for patterns
- Cross-reference with historical data from Estimation Engine

## References

- Gary Klein, "Performing a Project Premortem" (Harvard Business Review)
- Daniel Kahneman, "Thinking, Fast and Slow" (Chapter on Planning Fallacy)
- Nate Silver, "The Signal and the Noise" (Chapter on Overconfidence)
