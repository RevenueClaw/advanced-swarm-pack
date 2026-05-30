# skill-overnight-batch-engine-v1

**v1.0.0** — Queue and process overnight batch jobs

Part of v1.4.0 "Local Intelligence & Cost Optimization"

---

## Purpose

Process low-urgency, read-only jobs overnight using local models to maximize cost savings.

---

## Features

- **Persistent queue**: Jobs survive restarts
- **Memory/load checks**: Won't run if system stressed
- **Checkpoint/resume**: Long jobs can resume
- **Safety enforcement**: Destructive ops blocked
- **Morning digest**: Human-readable summaries
- **Cloud fallback**: On failure or low confidence

---

## Quick Start

```python
from skill_overnight_batch_engine import BatchEngine, JobConfig

engine = BatchEngine()

# Queue a job
engine.queue_job(JobConfig(
    name="newsletter_digest",
    skill="skill-newsletter-processor",
    model_profile="overnight",
    fallback="cloud_if_failed"
))

# Run all queued jobs
results = engine.run_batch()
```

---

## Directory Structure

```
~/.local_swarm/
├── jobs/          # Queued job configs
├── outputs/       # Job outputs
├── checkpoints/   # Resume state
├── failed_jobs/   # Failed job logs
├── logs/          # Execution logs
└── morning_digests/  # Generated digests
```

---

## Job Config

```yaml
name: newsletter_digest
skill: skill-newsletter-processor
model_profile: overnight
fallback: cloud_if_failed  # never, cloud_if_failed, cloud_if_confidence_low
schedule: "0 2 * * *"
enabled: true
max_runtime_minutes: 60
cooldown_minutes: 5
requires_privacy: true
params:
  source: newsletter_inbox
```

---

## Safety Rules

Local batch jobs may:
- Read files, summarize, extract
- Compare, dedupe, tag
- Draft reports

Blocked (escalates):
- Delete/overwrite files
- Send emails
- Make purchases
- Deploy code
- Modify credentials
- Run destructive shell commands

---

## Required Config

`~/.local_swarm/overnight-jobs.yaml`

```yaml
jobs:
  - name: newsletter_digest
    skill: skill-newsletter-processor
    model_profile: local_balanced
    fallback: cloud_if_failed
    schedule: "0 2 * * *"
  
  - name: price_tracking_report
    skill: skill-price-tracker-v1
    model_profile: local_fast
    fallback: never
    schedule: "30 2 * * *"
```

---

## Tests

```bash
cd skill-overnight-batch-engine-v1
python3 lib/batch_engine.py
```

---

## Requires

- Python 3.9+
- psutil
- pyyaml
- skill-local-llama-runner-v1
