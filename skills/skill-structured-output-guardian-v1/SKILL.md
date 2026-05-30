# skill-structured-output-guardian-v1

**v1.0.0** — Reliable JSON from local models

Part of v1.4.0 "Local Intelligence & Cost Optimization"

---

## Purpose

Force reliable, schema-compliant JSON from local llama.cpp models using validation, retry, and escalation.

---

## Features

- **Pydantic validation**: Type-safe output parsing
- **Two-step pattern**: Generate → Package → Validate
- **Auto-retry**: Simplify schema on failure
- **JSON repair**: Fix common formatting errors
- **Cloud escalation**: After configurable retries
- **Production metrics**: Track validation rates

---

## Quick Start

```python
from skill_structured_output_guardian import OutputGuardian
from pydantic import BaseModel

class MyResult(BaseModel):
    title: str
    confidence: float

guardian = OutputGuardian(max_retries=2)

result = guardian.generate_and_validate(
    prompt="Extract insights:",
    schema=MyResult,
    model_profile="fast"
)

if result.is_valid:
    print(f"Title: {result.data.title}")
else:
    print(f"Failed: {result.errors}")
    print(f"Escalated: {result.escalation_trigger}")
```

---

## Validation Flow

```
1. Generate with structured prompt
   ↓
2. Extract JSON from response
   ↓
3. Parse JSON
   ↓ Success → RETURN validated object
   ↓ Failure
4. Attempt repair
   ↓ Success → RETURN
   ↓ Failure  
5. Simplify schema
   ↓ Retry (max N times)
6. Escalate to cloud
```

---

## Schemas

### LocalTaskResult
Standard output format:
```python
{
  "task_id": "uuid",
  "status": "success",
  "confidence": 0.85,
  "evidence_grade": "B",
  "summary": "Executive summary...",
  "key_findings": [...],
  "citations": [...],
  "needs_human_review": False,
  "escalation_reason": null
}
```

See `lib/schemas.py` for all schemas.

---

## Escalation Triggers

| Trigger | When |
|---------|------|
| JSON_PARSE_FAILED | Can't extract valid JSON |
| VALIDATION_FAILED | JSON doesn't match schema |
| MAX_RETRIES_EXCEEDED | All attempts failed |
| LOW_CONFIDENCE | Confidence below threshold |

---

## Usage Patterns

### Decorator
```python
from skill_structured_output_guardian import validated

@validated(schema=MyResult, max_retries=2)
def generate_insights(text):
    return llm.complete(f"Analyze: {text}")

result = generate_insights("...")  # Returns ValidationResult
```

### Manual
```python
guardian = OutputGuardian()

prompt = "Summarize this article..."
schema = SummaryResult

result = guardian.generate_and_validate(
    prompt, schema, 
    model_profile="overnight"
)
```

---

## Files

- `lib/output_guardian.py` — Main guardian class
- `lib/schemas.py` — Pydantic models
- `lib/json_repair.py` — Repair utilities (optional)

---

## Requires

- Python 3.9+
- pydantic
- skill-local-llama-runner-v1

---

## Verification

```bash
cd skill-structured-output-guardian-v1
python3 -c "from skill_structured_output_guardian import OutputGuardian; g = OutputGuardian(); print('OK')"
```
