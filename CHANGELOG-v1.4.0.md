# Changelog v1.4.0 — Local Intelligence & Cost Optimization

**Release Date**: 2026-05-30  
**Codename**: "Local Intelligence"

---

## Summary

This release transforms the swarm from cloud-only to a intelligent hybrid system. Local llama.cpp models handle read-only, verifiable tasks at near-zero cost. Cloud models remain for high-risk, high-judgment work. Result: ~70% cost reduction on suitable workloads.

---

## New Skills

### skill-local-llama-runner-v1
- OpenAI-compatible llama.cpp server interface
- Three profiles: fast (8B), balanced (14B), overnight (30B)
- Health checks with memory pressure detection
- Structured JSON output with Pydantic validation
- Automatic cloud fallback with detailed logging
- ~1,800 lines Python

### skill-structured-output-guardian-v1
- Force reliable JSON from local models
- Two-step pattern: reason → package → validate
- Auto-retry with simplified schema
- Escalation after N failures
- ~900 lines Python

### skill-overnight-batch-engine-v1
- Cron-compatible job queue infrastructure
- Checkpoint/resume for long-running jobs
- Read-only safety enforcement
- Morning digest generation
- ~1,200 lines Python

### skill-hybrid-rag-v1
- Document ingestion to evidence packs
- Keyword + vector hybrid retrieval
- Corrective RAG with query rewriting
- Evidence grading (strong/partial/weak)
- ~1,500 lines Python (scaffold)

---

## Updated Skills

### skill-backend-interface
- Added model capability routing
- Task classifier for local vs cloud
- Risk-aware routing decisions

### skill-resource-awareness
- Expanded to cost-quality scheduling
- Tracks estimated cloud tokens avoided
- Local runtime metrics
- Failure rate tracking

### skill-hierarchical-orchestrator
- Added local inference worker role
- Capability-based task distribution
- Safety enforcement rules

### skill-versioning
- Added local/cloud shadow evaluation
- Compare outputs for quality/cost tradeoffs

### skill-newsletter-processor
- Added overnight local mode
- First-pass extraction runs local
- Final scoring escalates to cloud

### skill-idea-tracker
- Local deduplication and tagging
- Rough scoring runs local
- Final priority uses cloud

### skill-price-tracker-v1
- Local deal explanations
- Daily report drafts
- High-value recommendations escalate

### skill-codebase-understander-v1
- Passive local overnight scans
- Dead code detection
- Risky file identification

---

## Configuration

### New Config File
`configs/local-llama-profiles.yaml`
- Model endpoint definitions
- Routing policies
- Escalation thresholds
- Cost comparison settings

### Integration
Skills automatically load config from:
`~/.openclaw/config/local-llama-profiles.yaml`

---

## Cost Savings Model

| Task Type | Cloud Cost | Local Cost | Savings |
|-----------|------------|------------|---------|
| Summarization | $0.005/1K tokens | $0 | 100% |
| Extraction | $0.005/1K tokens | $0 | 100% |
| Newsletter processing | $0.02/email | $0 | 100% |
| Price tracking | $0.01/report | $0 | 100% |
| Codebase scan | $0.50/run | $0.02 (electricity) | 96% |

**Estimated savings**: 
- Newsletter processing: ~$15/month
- Price tracking: ~$25/month  
- Idea tracking: ~$10/month
- Overnight jobs: ~$30/month
- **Total: ~$80/month** on typical usage

---

## Safety Model

### Local Models May
- Read files, summarize, classify, extract
- Compare documents, dedupe, tag
- Draft reports and emails (without sending)
- Produce recommendations

### Local Models May NOT
- Delete/overwrite files without approval
- Send emails, make purchases
- Deploy code, modify credentials
- Run destructive shell commands

### Routing Logic
```python
def choose_model(task):
    if task.risk in ["destructive", "financial", "credential"]:
        return "cloud_leader"
    if task.deadline == "overnight" and task.requires_privacy:
        return "local_overnight"
    if task.type in ["classification", "extraction"]:
        return "local_fast"
    if task.type in ["summarization", "triage"]:
        return "local_balanced"
    return "cloud_leader"
```

---

## Migration Guide

### Existing Swarms
No breaking changes. Add config file, start llama.cpp servers, enable local mode incrementally.

### New Swarms
1. Clone repo
2. `./scripts/install-skills.sh`
3. Copy config template
4. Configure endpoints
5. Test with `python lib/llama_runner.py`

---

## Files Added

```
skills/
├── skill-local-llama-runner-v1/
│   ├── SKILL.md
│   ├── lib/
│   │   ├── __init__.py
│   │   ├── llama_runner.py (600+ lines)
│   │   ├── model_profiles.py
│   │   ├── health_monitor.py
│   │   └── benchmark.py
│   └── __init__.py
├── skill-structured-output-guardian-v1/
│   ├── SKILL.md
│   └── lib/
│       ├── output_guardian.py
│       ├── schemas.py
│       └── json_repair.py
├── skill-overnight-batch-engine-v1/
│   ├── SKILL.md
│   └── lib/
│       ├── batch_engine.py
│       ├── job_queue.py
│       └── morning_digest.py
└── skill-hybrid-rag-v1/
    ├── SKILL.md
    └── lib/
        ├── hybrid_rag.py
        ├── document_ingester.py
        └── retriever.py

configs/
└── local-llama-profiles.yaml
```

---

## Testing

### Quick Verification
```bash
# Test runner
cd skills/skill-local-llama-runner-v1
python3 -c "from lib.llama_runner import LocalLlamaRunner; r = LocalLlamaRunner(); print('OK')"

# Test health check (needs llama.cpp server)
python3 -c "
from lib.llama_runner import LocalLlamaRunner
r = LocalLlamaRunner(profile='fast')
print(r.health_check())
"
```

### Benchmark
```python
from skill_local_llama_runner import LocalLlamaRunner, BenchmarkRunner

runner = LocalLlamaRunner(profile="fast")
benchmark = BenchmarkRunner(runner)
result = benchmark.run_benchmark()
print(f"Tokens/sec: {result.tokens_per_sec}")
```

---

## Known Issues

1. **llama.cpp server must be running**: Not auto-started (use systemd)
2. **Port 8080-8082**: May conflict with other services
3. **Memory**: 30B model needs ~24GB RAM

---

## Future Work

- GPU acceleration support (CUDA/Rockchip NPU)
- Auto-scaling based on queue length
- Model warm-up optimization
- vLLM integration alternative

---

## Credits

- llama.cpp: @ggerganov
- Qwen3 models: @QwenLM
- OpenAI API spec: OpenAI

---

_Last Updated: 2026-05-30_
