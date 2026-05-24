# Estimation Engine

Time estimation with historical tracking, calibration, and automatic buffers.

## Quick Start

```python
from lib.estimation_engine import EstimationEngine, TaskCategory

engine = EstimationEngine()

# Generate estimate
estimate = engine.estimate(
    task="Implement feature X",
    subtasks=[
        ("Design", 1.5),
        ("Implementation", 3.0),
        ("Testing", 1.0)
    ],
    category=TaskCategory.CODING,
    is_novel=True
)

print(f"Estimate: {estimate['total_estimated_hours']} hours")
print(f"Range: {estimate['range_estimate']['most_likely']}-{estimate['range_estimate']['worst_case']}")

# Record actual time for calibration
engine.record_actual(
    estimate_id=estimate['estimate_id'],
    actual_hours=9.5,
    category="coding"
)
```

## Buffer Rules

| Task Type | Buffer |
|-----------|--------|
| Novel (new territory) | +50% |
| Standard (normal work) | +30% |
| Known (done before) | +20% |
| Minimum | +10% |

## Calibration

The system tracks historical predictions vs actual time:
- Per-category calibration scores
- Automatic buffer recommendations
- Confidence scores based on variance

**Storage:** `~/.openclaw/workspace/skills/skill-estimation-engine/history/`

## Integration

Connects to Architect-First planning:
```python
from lib.architect_integration import create_planning_estimate

estimate = create_planning_estimate(draft_plan)
```

## Categories

- `CODING`: Software development
- `RESEARCH`: Investigation and learning
- `DOCUMENTATION`: Docs and writing
- `INFRASTRUCTURE`: Systems and deployment
- `DEBUGGING`: Troubleshooting
- `PLANNING`: Analysis and design