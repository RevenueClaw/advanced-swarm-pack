# Comprehensive Skills Reference

Complete guide to all 10 skills in the Advanced Swarm Pack.

---

## Core Orchestration

### skill-hierarchical-orchestrator

**Purpose**: Decomposes complex goals and distributes tasks across the swarm.

**Key Capabilities**:
- Task decomposition into subtasks
- Worker assignment by capability matching
- Automatic rerouting on node failure
- Result aggregation from multiple workers

**Integration**: Base skill used by all other planning skills.

---

## Planning & Execution

### skill-architect-first

**Purpose**: Production-grade planning discipline with self-critique.

**Key Files**:
- `lib/plan_reviewer.py` — Core review engine (699 lines)
- `lib/planning_modes.py` — Mode selection (368 lines)
- `lib/orchestrator_integration.py` — Execution flow (288 lines)
- `lib/integration_connector.py` — HITL/Versioning/Preferences (175 lines)

**Usage**:
```python
from skill_architect_first import PlanReviewer
reviewer = PlanReviewer()
reviewed = reviewer.review({
    "goal": "Implement feature",
    "steps": ["Step 1", "Step 2"],
    "risks": ["Risk A"]
})
print(reviewed.scores.overall)  # 0-100
```

**5 Dimensional Scoring**:
1. **Clarity** (25%): Goal specificity, SMART criteria
2. **Risk Assessment** (30%): Known issues, rollback plan present
3. **Completeness** (20%): Steps detailed, dependencies clear
4. **Feasibility** (15%): Time estimates realistic
5. **Testability** (10%): Success criteria defined

**Tiered Modes**:
- **FAST**: ≤2 subtasks, low risk → skip review
- **STANDARD**: 2-5 subtasks, medium risk → review, auto-approve if ≥70
- **ARCHITECT_FIRST**: 5+ subtasks, high risk, novel → mandatory review, escalate if <60

**Escalation Triggers**:
- Score < 60/100
- 2+ critical issues
- Execution confidence < 50%

---

### skill-estimation-engine

**Purpose**: Accurate time estimation with historical calibration.

**Key Files**:
- `lib/estimation_engine.py` — Core engine (450 lines)
- `lib/architect_integration.py` — Planning integration (127 lines)

**Usage**:
```python
from skill_estimation_engine import EstimationEngine, TaskCategory

engine = EstimationEngine()
estimate = engine.estimate(
    task="Implement feature",
    subtasks=[("Design", 1.5), ("Code", 3.0)],
    category=TaskCategory.CODING,
    is_novel=True
)
# estimate['total_estimated_hours'] with buffers applied
```

**Buffer Rules**:
- Novel tasks: +50%
- Standard tasks: +30%
- Known tasks: +20%
- Minimum: +10%

**Calibration**:
- Per-category tracking (coding, research, infrastructure, etc.)
- Automatic buffer recommendations based on historical accuracy
- Confidence scores based on variance
- Stores in `~/.openclaw/skills/skill-estimation-engine/history/`

---

### skill-calculation-verifier

**Purpose**: Eliminates math hallucinations with Python-backed verification.

**Key Files**:
- `lib/calculation_verifier.py` — Verification engine (350 lines)

**Usage**:
```python
from skill_calculation_verifier import CalculationVerifier

verifier = CalculationVerifier()

# Simple
result = verifier.verify("12 * 5")
# → Method: mental, Confidence: 95%

# Complex
result = verifier.verify("234.5 * 123.67", use_tool=True)
# → Method: python, Confidence: 99%
```

**Complexity Levels**:
1. **TRIVIAL** (< 12): Mental calculation (98% confidence)
2. **SIMPLE** (< 100): Mental calculation (95% confidence)
3. **MODERATE** (larger): Calculator with steps (90% confidence)
4. **COMPLEX** (floats/advanced): Python interpreter (99% confidence)
5. **USE_TOOL**: Forced Python execution (99% confidence)

**Integrates with**: `skill-estimation-engine` for verifying subtask calculations during planning.

---

## Intelligence & Reasoning

### skill-consensus

**Purpose**: Multi-agent debate for high-stakes decisions.

**Key Files**:
- `lib/debate_orchestrator.py` — Main controller (288 lines)
- `lib/agent_personas.py` — Persona definitions (100 lines)

**Usage**:
```python
from skill_consensus import DebateOrchestrator

orch = DebateOrchestrator()
prompts = orch.get_debate_prompts(
    question="Should we migrate databases?",
    context={"current": "Postgres", "proposed": "ClickHouse"}
)
# Returns prompts for 3 agents: Conservative, Pragmatic, Innovative
```

**Trigger Conditions**:
- Risk score > 0.6
- Multiple valid approaches
- User rejected similar previous suggestions
- Novel situation (no learned pattern)

**Debate Flow**:
1. Conservative presents risks
2. Innovative presents opportunities
3. Each critiques others
4. Pragmatic synthesizes final recommendation

---

### skill-preference-learning

**Purpose**: Long-term learning of user preferences from interactions.

**Key Files**:
- `lib/preference_engine.py` — Main interface (202 lines)
- `lib/profile_manager.py` — Trait storage (492 lines)
- `lib/feedback_ingestor.py` — HITL processing (503 lines)

**Usage**:
```python
from skill_preference_learning import PreferenceEngine

pe = PreferenceEngine("shayne")

# Learn from feedback
pe.ingest_feedback(
    session_id="abc123",
    task_type="code_review",
    original_action="suggested edit",
    user_response="Always show the diff first"
)

# Query preferences
style = pe.get_communication_style()
# Returns: {"verbosity": "low", "code_first": True, ...}
```

**Learned Traits**:
- Communication: verbosity, detail_level, code_first
- Risk tolerance: automation_level, confirm_destructive
- Pace: response_speed, batching_preference
- Planning: time_tolerance, overhead_preferences

**Storage**: `~/.openclaw/skills/skill-preference-learning/preferences/{user_id}-profile.json`

---

## Resource Management

### skill-resource-awareness

**Purpose**: Cost tracking and intelligent backend routing.

**Key Files**:
- `lib/cost_tracker.py` — Token/cost accounting (350 lines)

**Usage**:
```python
from skill_resource_awareness import CostTracker

tracker = CostTracker()

# Record usage
cost = tracker.record_usage(
    backend="openrouter",
    model="kimi-k2.5",
    input_tokens=5000,
    output_tokens=2000,
    latency_ms=1200
)

# Check spending
daily = tracker.get_daily_spend()
monthly = tracker.get_monthly_spend()

# Should we switch to local?
should_local = tracker.should_use_local()
```

**Pricing** (per 1M tokens):
- kimi-k2.5: $0.50 input, $2.00 output
- o1-preview: $15.00 input, $60.00 output
- Local Ollama: $0.00

**Budgets**:
- Daily: $5.00
- Monthly: $100.00
- Fallback threshold: 80%

---

### skill-backend-interface

**Purpose**: Unified API for OpenRouter vs Ollama backends.

**Key Files**:
- `config.yaml` — Backend configuration

**Configuration**:
```yaml
backends:
  openrouter:
    enabled: true
    default_model: "openrouter/moonshotai/kimi-k2.5"
    
  ollama:
    enabled: true
    endpoint: "http://YOUR_GPU_NODE_IP:11434"  # e.g., "http://192.168.1.30:11434"
    default_model: "mistral:7b"  # Heavy reasoning
    vision_model: "llava:7b"       # Multimodal
    fast_model: "llama3.2:3b"      # Quick responses
```

**Routing Logic**:
- Default to OpenRouter (cloud models, full capability)
- Switch to Ollama when:
  - Cost budget exceeded
  - Simple, low-stakes request
  - OpenRouter rate limited
  - User explicitly requests local

---

## Deployment & Safety

### skill-versioning

**Purpose**: Safe deployment with shadow testing.

**Key Files**:
- `lib/version_manager.py` — Core versioning (699 lines)
- `lib/shadow_runner.py` — Parallel execution (368 lines)

**Usage**:
```python
from skill_versioning import SkillVersionManager

vm = SkillVersionManager("my-skill")

# Register versions
vm.register_version("1.0.0", path="/path/to/v1.0.0")
vm.register_version("2.0.0", path="/path/to/v2.0.0", status=VersionStatus.SHADOW)

# Shadow test
result = vm.execute_with_shadow(
    task="test query",
    shadow_version="2.0.0",
    compare_fn=lambda a, b: similarity(a, b)
)

# Promote
vm.promote("2.0.0", rollout_percent=10)  # 10% → 50% → 100%
```

**Status Lifecycle**:
```
DEVELOPMENT → SHADOW → STAGING → PRODUCTION → DEPRECATED
```

**Shadow Testing**:
- Production version returns result to user
- Shadow version runs invisibly, results logged
- Minimum 50 successful shadow runs before promotion
- 90% acceptance rate required

---

## Output & Visualization

### skill-visual-reports

**Purpose**: On-demand visual dashboards and diagrams.

**Key Files**:
- `lib/visual_reporter.py` — Main reporter (570 lines)

**Report Types**:
- `swarm_health` — HTML dashboard with node status, tasks, costs
- `orchestration_flow` — Mermaid flowchart of data flow
- `agent_hierarchy` — Mermaid org chart
- `task_dag` — Mermaid execution flow
- `last_24h_activity` — Plotly timeline with cost overlay
- `cost_analysis` — Plotly pie chart by model
- `latency_analysis` — Plotly bar chart comparison

**Usage**:
```python
from skill_visual_reports import VisualReporter

reporter = VisualReporter()

# Generate report
path = reporter.generate_report("swarm_health")
# Saves to ~/.openclaw/reports/YYYY-MM-DD_HH-MM-type.html

# Outputs SCP command for download
# scp rock@rock-desktop:/path/to/report.html ~/Downloads/
# open ~/Downloads/report.html
```

---

## Data Processing

### skill-newsletter-processor

**Purpose**: Extract business ideas from email newsletters.

**Key Files**:
- `lib/newsletter_processor.py` — Extraction engine (350 lines)

**Supported Sources**:
- Side Hustle Nation (nick@sidehustlenation.com)
- Easy to add more via `NEWSLETTER_SOURCES` config

**Usage**:
```python
from skill_newsletter_processor import NewsletterProcessor

processor = NewsletterProcessor()

# Process last 7 days
ideas = processor.process_newsletters(since_days=7)

# Get high-value ideas
high_ideas = processor.get_high_relevance_ideas(limit=10)
```

**Cron Integration**:
- Runs every 2 days at 7:00 AM EDT
- Before `income-automation-audit` job
- Extracted ideas feed into income generation workflow

**Storage**:
- Ideas: `~/.openclaw/workspace/newsletter-ideas/extracted-ideas.jsonl`
- Summary: `~/.openclaw/workspace/newsletter-ideas/ideas-summary.json`

---

## Quick Reference Table

| Skill | Lines | Status | Complexity |
|-------|-------|--------|------------|
| skill-vendor | 699 | ✅ Verified | High |
| skill-architect-first | 1,530 | ✅ Verified | Very High |
| skill-estimation-engine | 577 | ✅ Verified | Medium |
| skill-calculation-verifier | 350 | ✅ Verified | Low |
| skill-consensus | 388 | ✅ Verified | Medium |
| skill-preference-learning | 1,197 | ✅ Verified | High |
| skill-resource-awareness | 350 | ✅ Verified | Low |
| skill-backend-interface | 50 | ✅ Verified | Low |
| [skill-visual-reports | 570 | ✅ Verified | Medium |
| skill-newsletter-processor | 350 | ✅ Verified | Medium |

**Total**: ~6,061 lines of production Python code

---

## Integration Map

```
                          Core Skills
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
   Planning Layer    Execution Layer      Intelligence Layer
         │                    │                    │
   ┌─────────┐        ┌─────────┐        ┌─────────┐
   │Architect│        │         │        │         │
   │  First  │◄───────┤Backend  │◄───────┤Consensus│
   │         │        │Interface│        │         │
   ├─────────┤        ├─────────┤        ├─────────┤
   │Estima-  │        │Resource │        │Prefer-  │
   │  tion   │        │Awareness│        │  ence   │
   ├─────────┤        ├─────────┤        │Learning│
   │Calcula-│        │Version- │        ├─────────┤
   │  tion   │        │  ing    │        │ News-   │
   │Verifier │        └─────────┘        │ letter  │
   └─────────┘                            │Processor│
                                          └─────────┘
                                             │
                                        ┌─────────┐
                                        │ Visual  │
                                        │ Reports │
                                        └─────────┘
```

All skills integrate through shared `~/.openclaw/workspace/` directory structure and common Python import patterns.