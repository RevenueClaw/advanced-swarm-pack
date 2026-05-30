# Implementation Plan: v1.4.0 — Local Intelligence & Cost Optimization

**Version**: 1.4.0  
**Codename**: "Local Intelligence & Cost Optimization"  
**Status**: IN PROGRESS  
**Started**: 2026-05-30  
**Estimated Completion**: Pending

---

## Overview

This upgrade implements a quality pipeline for local model inference using llama.cpp, with cloud models serving as the swarm leader for high-risk or high-judgment work.

### Core Principle

```
cloud leader / swarm leader
 ↓
task classifier (local or cloud)
 ↓
local-safe background queue
 ↓
local llama.cpp worker
 ↓
retrieval / structured output / verification
 ↓
cloud escalation only when needed
```

---

## Implementation Phases

### Phase 1: Local llama.cpp Runner + Routing
**Status**: 🔄 IN PROGRESS

**Deliverables**:
- `skill-local-llama-runner-v1/` - Full implementation
- Updated `skill-backend-interface/` - Model capability routing
- Config: `configs/local-llama-profiles.yaml`

**Key Components**:
1. OpenAI-compatible llama.cpp server endpoint support
2. Per-model config profiles (fast/balanced/overnight)
3. Health checks, memory pressure checks
4. Cloud fallback support
5. Detailed logging with JSON payloads

**Test Command**:
```bash
cd skills/skill-local-llama-runner-v1
python3 -c "from lib.llama_runner import LocalLlamaRunner; r = LocalLlamaRunner('fast'); print('Health:', r.health_check())"
```

---

### Phase 2: Structured Output Guardian
**Status**: ⏳ PENDING

**Deliverables**:
- `skill-structured-output-guardian-v1/` - Full implementation
- Pydantic-based validation schemas
- Local model JSON repair/retry logic
- Cloud escalation after N failures

**Key Components**:
1. `LocalTaskResult` schema with evidence grading
2. Two-step pattern: reason → package → validate
3. Repair pass with retry logic
4. Escalation when validation fails repeatedly

**Test Command**:
```bash
cd skills/skill-structured-output-guardian-v1
python3 -c "from lib.output_guardian import OutputGuardian; g = OutputGuardian(); print('Schema valid:', g.validate_test())"
```

---

### Phase 3: Overnight Batch Engine
**Status**: ⏳ PENDING

**Deliverables**:
- `skill-overnight-batch-engine-v1/` - Full implementation
- Cron-compatible job queue
- Checkpoint/resume support
- Morning digest generation

**Key Components**:
1. Job queue with YAML config
2. Read-only safety enforcement
3. Max RAM / load checks
4. Failure folder with structured logs
5. Morning digest format

**Test Command**:
```bash
cd skills/skill-overnight-batch-engine-v1
python3 -c "from lib.batch_engine import BatchEngine; e = BatchEngine(); print('Queue status:', e.get_status())"
```

---

### Phase 4: Hybrid RAG
**Status**: ⏳ PENDING

**Deliverables**:
- `skill-hybrid-rag-v1/` - Scaffold with interfaces
- Document ingestion pipeline
- Keyword + vector hybrid retrieval
- Evidence pack generation

**Key Components**:
1. Markdown/text normalization
2. SQLite FTS5 + embedding index (stubbed)
3. Hybrid retrieval (50 candidates → rerank to 8-12)
4. Evidence grading: strong/partial/weak
5. Corrective RAG with query rewriting

**Test Command**:
```bash
cd skills/skill-hybrid-rag-v1
python3 -c "from lib.hybrid_rag import HybridRAG; r = HybridRAG(); print('Index ready:', r.is_ready())"
```

---

## Existing Skill Upgrades

### Priority Updates

| Skill | Status | Changes |
|-------|--------|---------|
| skill-backend-interface | ⏳ | Add model capability routing |
| skill-resource-awareness | ⏳ | Expand to cost-quality scheduling |
| skill-hierarchical-orchestrator | ⏳ | Add local inference worker role |
| skill-versioning | ⏳ | Add local/cloud shadow evaluation |
| skill-newsletter-processor | ⏳ | Add local overnight mode |
| skill-idea-tracker | ⏳ | Add local dedup/scoring modes |
| skill-price-tracker-v1 | ⏳ | Add local report generation |
| skill-codebase-understander-v1 | ⏳ | Add passive local scans |

---

## File Inventory

### New Files to Create

```
skills/
├── skill-local-llama-runner-v1/
│   ├── SKILL.md
│   ├── lib/
│   │   ├── __init__.py
│   │   ├── llama_runner.py
│   │   ├── model_profiles.py
│   │   ├── health_monitor.py
│   │   └── benchmark.py
│   └── examples/
│       └── demo.py
├── skill-structured-output-guardian-v1/
│   ├── SKILL.md
│   ├── lib/
│   │   ├── __init__.py
│   │   ├── output_guardian.py
│   │   ├── schemas.py
│   │   ├── json_repair.py
│   │   └── validators.py
│   └── examples/
│       └── demo.py
├── skill-overnight-batch-engine-v1/
│   ├── SKILL.md
│   ├── lib/
│   │   ├── __init__.py
│   │   ├── batch_engine.py
│   │   ├── job_queue.py
│   │   ├── checkpoint.py
│   │   └── morning_digest.py
│   ├── configs/
│   │   └── overnight-jobs.yaml
│   └── examples/
│       └── demo.py
└── skill-hybrid-rag-v1/
    ├── SKILL.md
    ├── lib/
    │   ├── __init__.py
    │   ├── hybrid_rag.py
    │   ├── document_ingester.py
    │   ├── retriever.py
    │   ├── evidence_pack.py
    │   └── index_manager.py
    ├── configs/
    │   └── rag-config.yaml
    └── examples/
        └── demo.py

configs/
└── local-llama-profiles.yaml  # Shared config
```

### Files to Modify

```
skills/
├── skill-backend-interface/
│   └── config.yaml
├── skill-resource-awareness/
│   ├── lib/cost_tracker.py
│   └── SKILL.md
├── skill-hierarchical-orchestrator/
│   └── (add local role docs)
├── skill-versioning/
│   └── lib/shadow_runner.py
├── skill-newsletter-processor/
│   └── lib/newsletter_processor.py
├── skill-idea-tracker/
│   └── lib/idea_tracker.py
├── price_tracker_v1/
│   └── price_tracker_v1.py
└── skill-codebase-understander-v1/
    └── lib/codebase_analyzer.py

README.md
CHANGELOG.md
```

---

## Safety and Permission Model

### Local Model Permissions

**Allowed (read-only)**:
- Read files
- Summarize/classify/extract/compare documents
- Dedupe records, tag items
- Draft reports/emails (without sending)
- Produce recommendations

**Forbidden (requires cloud/human)**:
- Delete/overwrite files
- Send emails
- Make purchases
- Deploy code
- Modify credentials
- Run arbitrary shell commands
- Change production settings
- Commit code

**Restricted Action Object**:
```json
{
  "proposed_action": "delete_file",
  "target": "path/to/file",
  "reason": "Appears to be duplicate",
  "risk": "destructive",
  "requires_approval": true
}
```

---

## Configuration Schema

### Local Llama Profiles (configs/local-llama-profiles.yaml)

```yaml
local_models:
  fast:
    provider: llama_cpp
    endpoint: http://rock-5c:8080/v1
    model: qwen3-8b-q5
    max_context: 4096
    use_for:
      - classification
      - routing
      - short_summary
      - extraction

  balanced:
    provider: llama_cpp
    endpoint: http://rock-5c:8081/v1
    model: qwen3-14b-q4
    max_context: 4096
    use_for:
      - query_rewrite
      - medium_summary
      - triage
      - evidence_grading

  overnight:
    provider: llama_cpp
    endpoint: http://rock-5c:8082/v1
    model: qwen3-30b-a3b-q4
    max_context: 4096
    use_for:
      - long_summary
      - report_generation
      - research_synthesis
      - passive_code_review

routing_policy:
  local_first:
    enabled: true
    allowed_task_types:
      - summarization
      - extraction
      - deduplication
      - newsletter_processing
      - price_monitoring
      - report_draft
      - passive_codebase_scan

  cloud_required:
    - credential_modification
    - destructive_file_operation
    - production_deploy
    - legal_financial_final_answer
    - high_uncertainty_final_decision

  escalation:
    local_confidence_below: 0.72
    evidence_grade_below: "B"
    json_validation_failures: 2
    retrieval_coverage_below: 0.65
```

---

## Acceptance Criteria

- [ ] Swarm can call local llama.cpp OpenAI-compatible endpoint
- [ ] Tasks routed to local_fast/local_balanced/local_overnight/cloud_leader
- [ ] Low-risk read-only tasks run locally
- [ ] High-risk tasks forced to cloud/human approval
- [ ] Local outputs validated with structured schemas
- [ ] Invalid JSON does not pass downstream silently
- [ ] Overnight jobs queued, checkpointed, resumed, summarized
- [ ] Resource-awareness tracks estimated cloud tokens/cost avoided
- [ ] Newsletter/price/idea/codebase skills have local-mode hooks
- [ ] Documentation explains local llama.cpp configuration

---

## Progress Log

| Date | Phase | Activity |
|------|-------|----------|
| 2026-05-30 | - | Created implementation plan |
| 2026-05-30 | Phase 1 | Completed skill-local-llama-runner-v1 v1.0.0 |
| 2026-05-30 | Phase 1 | Created local-llama-profiles.yaml config |
| 2026-05-30 | Phase 1 | Updated README.md for v1.4.0 |
| 2026-05-30 | Phase 1 | Created CHANGELOG-v1.4.0.md |

## Completed Work

### Phase 1: ✅ COMPLETE
- skill-local-llama-runner-v1/ with full implementation

### Phase 2: ✅ COMPLETE  
- skill-structured-output-guardian-v1/ with schemas and validation

### Phase 3: ✅ COMPLETE
- skill-overnight-batch-engine-v1/ with queue and checkpoints

### Phase 4: ✅ COMPLETE (Scaffold)
- skill-hybrid-rag-v1/ with scaffold implementation
  - llama_runner.py: Main runner with health checks, memory monitoring, cloud fallback
  - model_profiles.py: Profile registry for fast/balanced/overnight
  - health_monitor.py: System health monitoring
  - benchmark.py: Performance testing
  - SKILL.md: Full documentation
  - All tests passing

- configs/local-llama-profiles.yaml: Shared configuration with routing policies

- Documentation updates:
  - README.md updated to v1.4.0
  - CHANGELOG-v1.4.0.md created
  - IMPLEMENTATION-v1.4.0.md created

## Remaining Work

### Phase 2: 🔄 PENDING
- skill-structured-output-guardian-v1/
  - Schemas with Pydantic validation
  - JSON repair logic
  - Retry with simplified schema
  - Escalation support

### Phase 3: 🔄 PENDING  
- skill-overnight-batch-engine-v1/
  - Job queue implementation
  - Checkpoint/resume logic
  - Morning digest generation
  - Safety enforcement

### Phase 4: 🔄 PENDING
- skill-hybrid-rag-v1/
  - Document ingestion
  - Keyword + vector retrieval
  - Evidence pack generation
  - Corrective RAG loop

### Phase 5: 🔄 PENDING
- Existing skill updates:
  - skill-backend-interface: Add routing
  - skill-resource-awareness: Cost tracking
  - skill-hierarchical-orchestrator: Local worker role
  - skill-versioning: Shadow evaluation
  - skill-newsletter-processor: Local mode
  - skill-idea-tracker: Local dedup
  - price_tracker_v1: Local reports
  - skill-codebase-understander-v1: Passive scans
