# skill-local-llama-runner-v1

**v1.0.0** — Local llama.cpp model runner for OpenClaw swarms

Part of v1.4.0 "Local Intelligence & Cost Optimization" upgrade.

---

## Purpose

Run local llama.cpp models through OpenAI-compatible endpoints for cost-effective, privacy-preserving inference.

---

## Features

- **OpenAI-compatible API**: Works with llama.cpp server
- **Profile-based models**: fast / balanced / overnight
- **Health monitoring**: Automatic model availability checks
- **Memory pressure detection**: Safe operation under resource constraints
- **Structured output**: JSON validation with Pydantic schemas
- **Cloud fallback**: Escalate to cloud on failure
- **Detailed logging**: Token usage, latency, errors

---

## Quick Start

```python
from skill_local_llama_runner import LocalLlamaRunner

# Initialize with profile
runner = LocalLlamaRunner(profile="fast")

# Check health
if runner.is_healthy():
    result = runner.complete(
        prompt="Summarize this document...",
        max_tokens=500,
        temperature=0.2
    )
    print(result.text)
    print(f"Tokens: {result.completion_tokens}")
    print(f"Time: {result.wall_time_ms}ms")
```

---

## Profiles

| Profile | Model | Use For | Endpoint |
|---------|-------|---------|----------|
| **fast** | qwen3-8b-q5 | Classification, routing, extraction | :8080/v1 |
| **balanced** | qwen3-14b-q4 | Summaries, triage, deduplication | :8081/v1 |
| **overnight** | qwen3-30b-a3b-q4 | Reports, synthesis, code review | :8082/v1 |

**Note**: Configure endpoints in `~/.openclaw/config/local-llama-profiles.yaml`

---

## Configuration

```yaml
local_models:
  fast:
    provider: llama_cpp
    endpoint: http://rock-5c:8080/v1
    model: qwen3-8b-q5
    max_context: 4096
    timeout: 30
    use_for:
      - classification
      - routing
      - short_summary
```

---

## Structured Output

```python
from pydantic import BaseModel

class SummaryResult(BaseModel):
    title: str
    key_points: list[str]

result = runner.complete(
    prompt="Summarize: ...",
    schema=SummaryResult,
    validate_json=True
)

# result.json_valid indicates if schema matched
```

---

## Cloud Fallback

```python
def cloud_fallback(**kwargs):
    # Your cloud API call here
    return {"text": result, "tokens": count}

runner = LocalLlamaRunner(
    profile="fast",
    cloud_fallback_fn=cloud_fallback
)

# Automatically escalates if local fails
result = runner.complete(
    prompt="...",
    allow_cloud_fallback=True
)
# result.fallback_used will be True if cloud was used
```

---

## Health & Monitoring

```python
# Health check
health = runner.health_check()
# Returns: {"status": "healthy", "response_time_ms": 120, ...}

# Memory pressure
mem = runner.check_memory_pressure()
# Returns: {"under_pressure": False, "available_mb": 24000, ...}

# Stats
stats = runner.get_stats()
# Returns: requests, tokens, fallbacks, etc.
```

---

## Logging

All completions logged to:
`~/.openclaw/logs/local-llama/completions_YYYY-MM-DD.jsonl`

Log format:
```json
{
  "profile": "fast",
  "model": "qwen3-8b-q5",
  "runtime": "llama.cpp",
  "prompt_tokens": 100,
  "completion_tokens": 50,
  "wall_time_sec": 0.82,
  "json_valid": true,
  "fallback_used": false
}
```

---

## Files

- `lib/llama_runner.py` — Main runner class
- `lib/model_profiles.py` — Profile management
- `lib/health_monitor.py` — System health
- `lib/benchmark.py` — Performance testing

---

## Requirements

- Python 3.9+
- requests
- pyyaml
- psutil
- pydantic (optional, for structured output)

---

## Verification

```bash
cd skill-local-llama-runner-v1
python3 -c "from lib.llama_runner import LocalLlamaRunner; r = LocalLlamaRunner(); print('OK')"
```
