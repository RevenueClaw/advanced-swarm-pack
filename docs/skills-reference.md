# Skills Reference

Complete reference for all skills in the Advanced Swarm Pack.

> **Skill Naming Convention**: `skill-{kebab-case-description}`

---

## Core Skills

### skill-versioning

**Purpose**: Manage skill/workflow versions with safe deployment.

**Files**:
- `lib/version_manager.py` — Core versioning logic
- `cli.py` — Command-line interface

**Key Classes**:
```python
from skill_versioning import SkillVersionManager

vm = SkillVersionManager("my-skill")
vm.register_version("2.0.0", Path("/path/to/v2.0.0"))
vm.promote("2.0.0", rollout_percent=10)
```

**CLI Commands**:
```bash
python cli.py register my-skill 2.0.0 ./skills/my-skill/v2.0.0/
python cli.py list my-skill
python cli.py promote my-skill 2.0.0 --percent 10 --force
python cli.py rollback my-skill
```

**Status Values**: `development`, `shadow`, `staging`, `production`, `deprecated`, `rolled_back`

---

### skill-preference-learning

**Purpose**: Learn user preferences from interactions.

**Files**:
- `lib/preference_engine.py` — Main interface
- `lib/profile_manager.py` — Trait storage
- `lib/feedback_ingestor.py` — HITL processing

**Key Classes**:
```python
from preference_engine import PreferenceEngine

pe = PreferenceEngine("shayne")
pe.ingest_feedback(
    session_id="abc123",
    task_type="code_review",
    original_action="suggested changes",
    user_response="Always show the diff first"
)

# Query learned preferences
style = pe.get_communication_style()
# Returns: {"verbosity": "low", "code_first": True, ...}
```

**Learned Traits**:
- `communication.verbosity`: minimal, low, medium, high
- `communication.code_first`: bool
- `risk.automation_level`: manual, conservative, moderate, aggressive
- `pace.response_speed`: deliberate, balanced, fast

---

### skill-consensus

**Purpose**: Multi-agent debate for uncertain decisions.

**Files**:
- `lib/debate_orchestrator.py` — Main controller
- `lib/agent_personas.py` — Persona definitions

**Key Classes**:
```python
from debate_orchestrator import DebateOrchestrator
from agent_personas import AgentPersonas

orch = DebateOrchestrator()
result = orch.debate(
    question="Should we migrate databases?",
    context={"current": "Postgres", "target": "ClickHouse"}
)

# Get prompts for subagents
prompts = orch.get_debate_prompts("Should we X?", {})
```

**Personas**:
- **Conservative**: Risk-aware validator
- **Pragmatic**: Balanced decision-maker
- **Innovative**: Solution explorer

---

### skill-resource-awareness

**Purpose**: Cost tracking and backend routing.

**Files**:
- `lib/cost_tracker.py` — Token/cost accounting

**Key Classes**:
```python
from cost_tracker import CostTracker

tracker = CostTracker()
cost = tracker.record_usage(
    backend="openrouter",
    model="kimi-k2.5",
    input_tokens=5000,
    output_tokens=2000,
    latency_ms=1200
)

daily = tracker.get_daily_spend()
monthly = tracker.get_monthly_spend()
should_local = tracker.should_use_local()
```

**Pricing** (per 1M tokens):
- kimi-k2.5: $0.50 input, $2.00 output
- o1-preview: $15.00 input, $60.00 output
- Local Ollama: $0.00

**Budgets**:
- Daily: $5.00
- Monthly: $100.00

---

### skill-hierarchical-orchestrator

**Purpose**: Decompose goals and distribute to workers.

**Key Concepts**:
- Supervisor Agent: Goal → Subtasks
- Task Queue: Priority-based
- Worker Router: Capability matching
- Result Aggregator: Response synthesis

---

### skill-hitl

**Purpose**: Human-in-the-loop interaction.

**Features**:
- Structured feedback capture
- Classification: explicit, correction, confirmation, rejection, escalation
- Confidence delta tracking

---

### skill-backend-interface

**Purpose**: Unified backend API.

**Supports**:
- OpenRouter (cloud models)
- Ollama (local GPU)
- Capability-based routing
- Automatic fallback

---

## Support Skills

### skill-multi-modal

**Purpose**: Image/audio/video processing.

**Features**:
- Video frame extraction
- Audio transcription
- Image analysis

### skill-health-monitor

**Purpose**: System health and monitoring.

**Interval**: Every 30 minutes
**Checks**:
- Node connectivity
- Session health
- Orphaned session cleanup
- Critical alert thresholds

---

## Storage Locations

| Skill | Data Location |
|-------|--------------|
| versioning | `~/.openclaw/skills/skill-versioning/registry/` |
| preference-learning | `~/.openclaw/skills/skill-preference-learning/preferences/` |
| resource-awareness | `~/.openclaw/skills/skill-resource-awareness/cost_logs/` |
| consensus | `~/.openclaw/skills/skill-consensus/debate_logs/` |

All use JSON/JSONL with atomic writes (temp + rename).

---

## Testing

Each skill includes self-verification:

```bash
cd skills/skill-versioning/lib
python version_manager.py
# Runs verification tests

# Or run all
cd ~/.openclaw/workspace/skills
pytest */tests/ -v
```

---

## Contributing

See `docs/contributing.md` for skill development guidelines.
