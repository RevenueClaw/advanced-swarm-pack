# Versioning Demo: Safe Skill Updates

This example shows how to safely deploy a new version of a skill using shadow testing.

## Scenario

You want to update `skill-memory-v2` from v1.0.0 to v2.0.0 but don't want to break production.

## Step-by-Step

### 1. Prepare New Version

```bash
# Create new version directory
mkdir -p ~/.openclaw/workspace/skills/skill-memory-v2/versions/v2.0.0

# Copy updated files
cp -r ~/updated-skill-files/* ~/.openclaw/workspace/skills/skill-memory-v2/versions/v2.0.0/

# Verify structure
ls ~/.openclaw/workspace/skills/skill-memory-v2/versions/v2.0.0/
# Should show: SKILL.md, lib/, tests/
```

### 2. Register Shadow Version

```python
from skill_versioning import SkillVersionManager, VersionStatus

vm = SkillVersionManager("skill-memory-v2")

# Register as SHADOW (runs invisibly)
vm.register_version(
    version="2.0.0",
    path=Path("~/.openclaw/workspace/skills/skill-memory-v2/versions/v2.0.0/"),
    status=VersionStatus.SHADOW
)

print("Shadow version registered ✓")
```

### 3. Enable Shadow Testing

The system now runs both versions:
- **Production** (v1.0.0): Returns results to users
- **Shadow** (v2.0.0): Runs invisibly, logs comparisons

```python
# During normal operation, execute with shadow comparison
result = vm.execute_with_shadow(
    task="search query about OpenClaw",
    shadow_version="2.0.0",
    prod_executor=memory_v1_search,
    shadow_executor=memory_v2_search,
    compare_fn=lambda a, b: jaccard_similarity(a, b)
)

# Returns production result, but logs shadow comparison
```

### 4. Monitor Shadow Results

Check shadow acceptance over time:

```python
from skill_versioning import ShadowRunner

runner = ShadowRunner()
stats = runner.get_acceptance_stats("2.0.0", hours=48)

print(f"""
Shadow Version 2.0.0 Stats (48 hours):
- Total Tests: {stats['total_tests']}
- Accepted: {stats['accepted']}
- Rejected: {stats['rejected']}
- Acceptance Rate: {stats['acceptance_rate']:.1%}
- Avg Similarity: {stats['avg_similarity']:.3f}
- Avg Latency Delta: {stats['avg_latency_delta_ms']:.0f}ms
""")
```

### 5. Promote to Staging (10% traffic)

After 50+ successful shadow runs with >90% acceptance:

```python
# Promote to staging (10% of real traffic)
vm.promote("2.0.0", rollout_percent=10)

# Now v2.0.0 handles 10% of production traffic
# Monitor for errors, latency, user feedback
```

Health checks automatically validate before promotion:
- Minimum 50 shadow tests
- >90% acceptance rate
- No errors in last 24h
- Similarity >0.85 average

### 6. Gradual Rollout

Increase traffic gradually:

```python
# 25% traffic
vm.promote("2.0.0", rollout_percent=25)

# 50% traffic
vm.promote("2.0.0", rollout_percent=50)

# 100% traffic (full production)
vm.promote("2.0.0", rollout_percent=100)
```

### 7. Rollback if Needed

If problems detected, instant rollback:

```python
# Emergency rollback
rolled_to = vm.rollback()

# Or rollback to specific version
vm.rollback(to_version="1.0.0")

print(f"Rolled back to version: {rolled_to}")
```

### 8. Verify Production

```python
# Check current production version
prod = vm.get_production_version()
print(f"Production: {prod.version}")

# List all versions
for v in vm.list_versions():
    print(f"  {v.version}: {v.status.value} ({v.rollout_percent}%)")
```

## Confidence Thresholds

| Condition | Required | Actual |
|-----------|----------|--------|
| Min shadow runs | 50 | 67 |
| Acceptance rate | 90% | 94.1% |
| Avg similarity | 0.85 | 0.91 |
| Errors 24h | <5 | 0 |
| **Status** | | **✓ PROMOTION APPROVED** |

## CLI Alternative

```bash
# Register version
python skills/skill-versioning/cli.py register skill-memory-v2 2.0.0 ./v2.0.0/

# List versions
python skills/skill-versioning/cli.py list skill-memory-v2

# Promote
python skills/skill-versioning/cli.py promote skill-memory-v2 2.0.0 --percent 10

# Check stats
python skills/skill-versioning/cli.py stats skill-memory-v2 --shadow-version 2.0.0

# Rollback (if needed)
python skills/skill-versioning/cli.py rollback skill-memory-v2
```

## Key Takeaway

Shadow testing lets you validate new versions with **zero user impact**. You get:
- Confidence in changes before production exposure
- Performance comparisons (latency, quality)
- Instant rollback if issues arise
- Gradual rollout control

**Production deployments should be boring.** Shadow testing makes them safe.
