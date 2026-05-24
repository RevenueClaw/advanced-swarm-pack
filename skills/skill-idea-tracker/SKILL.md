# Skill: Idea Tracker

**Extract business opportunities and convert the best ones into prioritized, trackable tasks.**

## Overview

The Idea Tracker is a complete business opportunity pipeline that transforms newsletters, emails, and other sources into actionable income tasks. It scores, prioritizes, and escalates high-value ideas automatically.

## Core Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    EXTRACT      │────▶│    SCORE        │────▶│    TRACK        │
│  (Multi-source) │     │ (Value/Effort) │     │ (Task creation) │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                           │
                                     ┌─────────────────────┼─────────────────────┐
                                     │                     │                     │
                                     ▼                     ▼                     ▼
                              ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
                              │  P0 ($5K+)  │      │ P1 ($2-5K)  │      │ P2 ($1-2K)  │
                              │    🔴       │      │    🟠       │      │    🟡       │
                              └─────────────┘      └─────────────┘      └─────────────┘
```

## Features

### Multi-Source Extraction
- **AgentMail**: Newsletters, business opportunity emails
- **API Integrations**: abund.ai, toku.agency job feeds
- **Manual Entry**: Direct idea capture via CLI

### Intelligent Scoring (5D Framework)
1. **Revenue Potential**: Monthly earnings estimate
2. **Startup Cost**: Initial investment required
3. **Effort Level**: Time/energy commitment
4. **AI Relevance**: Alignment with AI/agent capabilities
5. **Strategic Fit**: Match to current skills/resources

### Automatic Task Creation
Ideas meeting thresholds become tasks via task-manager:

| Revenue | Priority | Task Created | Escalation |
|---------|----------|--------------|------------|
| $5,000+ | P0 🔴 | Yes | Immediate notification |
| $2,000-5K | P1 🟠 | Yes | Weekly digest |
| $1,000-2K | P2 🟡 | Yes | Weekly digest |
| <$1,000 | P3 🟢 | No | Logged only |

### Preference Learning Integration
Tracks:
- Which ideas you pursue vs reject
- Estimated vs actual effort
- Your preferred business types
- Time-to-value preferences

Learns your patterns to improve future scoring.

## Quick Start

```python
from lib.idea_tracker import IdeaTracker

tracker = IdeaTracker()

# Process AgentMail inbox
report = tracker.process_inbox()

# View prioritized backlog
tracker.show_backlog(top_n=10)

# Get task-ready ideas
ideas = tracker.get_prioritized_backlog(min_score=70)
```

## CLI Usage

```bash
# Process all sources
cd ~/.openclaw/workspace/skills/skill-idea-tracker
python3 lib/idea_tracker.py process-all

# Process specific source
python3 lib/idea_tracker.py process --source agentmail
python3 lib/idea_tracker.py process --source abund

# View backlog
python3 lib/idea_tracker.py backlog --top 10

# Manual idea entry
python3 lib/idea_tracker.py add --name "Crypto Arbitrage Bot" \
    --revenue "$3000/mo" \
    --startup-cost "Low" \
    --effort "Medium"

# Dry run (preview only)
python3 lib/idea_tracker.py process --dry-run
```

## Configuration

`~/.openclaw/config/idea-tracker.yaml`:

```yaml
# Thresholds
task_creation_threshold:
  revenue_monthly: 1000  # Minimum $/mo to create task
  ai_relevance: 50     # AI alignment score 0-100
  effort_max: "High"   # Skip if effort > this

# Automatic processing
auto_cleanup: true          # Delete processed emails
archive_enabled: true       # Save email metadata

# Notifications
notify_on_p0: true          # Immediate for $5000+ ideas
weekly_digest_day: "Sunday"
digest_time: "09:00"

# Sources
disabled_sources: []
  # - "sms_spam"
  # - "linkedin_sales"

# Scoring weights
scoring_weights:
  revenue: 0.35
  effort: 0.20
  ai_relevance: 0.25
  strategic_fit: 0.20
```

## Integrations

### Architect-First
When processing ideas:
```python
# Ideas above P0 threshold trigger architect review
if idea.score > 85:
    plan = architect_first.analyze(
        idea=idea,
        mode=ArchitectureMode.STANDARD
    )
    idea.set_architecture_plan(plan)
```

### Estimation Engine
```python
# Auto-estimate effort for task creation
effort = estimation_engine.estimate(
    task_type="business_idea",
    description=idea.description
)
idea.estimated_hours = effort.predicted_hours
```

### Preference Learning
```python
# Track outcomes to improve scoring
tracker.record_outcome(
    idea_id=idea.id,
    outcome="pursued",  # or rejected, stalled
    actual_effort=actual_hours,
    actual_revenue=actual_monthly
)
```

## Storage

```
~/.openclaw/workspace/idea-tracker/
├── backlog/
│   ├── ideas.jsonl          # All tracked ideas
│   ├── scored/              # Scored ideas by month
│   └── tasks-created.json   # Link ideas → task IDs
├── sources/
│   ├── agentmail/
│   │   └── processed.jsonl  # Processed emails
│   └── abund/
│       └── opportunities.json
├── preferences/
│   └── user-profile.json    # Learned preferences
└── reports/
    └── weekly-digests/      # Digest history
```

## Swarm Integration

```python
# Spawn idea review subagent
sessions_spawn(
    agentId="idea-reviewer",
    task="Review P0 ideas from tracker and suggest next steps",
    runtime="subagent"
)

# Integration with consensus for borderline ideas
if 60 < idea.score < 80:
    verdict = consensus.debate([
        "Should we pursue this idea?",
        f"Revenue: {idea.revenue}",
        f"Effort: {idea.effort}"
    ])
    idea.add_consensus(verdict)
```

## API Reference

### IdeaTracker Class

```python
class IdeaTracker:
    def process_inbox(self, source: str = "all", 
                     since_days: int = 7) -> ProcessingReport
    
    def add_idea(self, idea: Idea) -> TrackedIdea
    
    def score_idea(self, idea: Idea) -> ScoreResult
    
    def get_prioritized_backlog(self, 
                              min_score: int = 60,
                              max_effort: str = "High") -> List[Idea]
    
    def create_task(self, idea: Idea) -> Optional[Task]
    
    def show_backlog(self, top_n: int = 10)
    
    def record_outcome(self, idea_id: str, 
                      outcome: str,
                      actual_revenue: Optional[int] = None)
```

### Idea Data Model

```python
@dataclass
class Idea:
    id: str
    source: str              # "agentmail", "abund", "manual"
    name: str
    description: str
    revenue_potential: str     # "$3000/mo"
    startup_cost: str         # "Low/Medium/High"
    effort_level: str         # "Low/Medium/High"
    
    # Scoring
    revenue_score: int         # 0-100
    effort_score: int         # 0-100 (lower is better)
    ai_relevance: int         # 0-100
    strategic_fit: int        # 0-100
    total_score: int          # Weighted composite
    
    # Tracking
    status: str               # new/scored/tasked/pursued/rejected
    task_id: Optional[str]
    created_at: datetime
    pursued_at: Optional[datetime]
```

## Testing

```bash
# Run self-verification
cd ~/.openclaw/workspace/skills/skill-idea-tracker
python3 tests/test_idea_tracker.py

# Test integration
cd ~/.openclaw/workspace/release/advanced-swarm-pack
python3 scripts/test_all_skills.py
```

## Release Notes (v1.0.1)

**New Skill**: Idea Tracker
- Complete business opportunity pipeline
- Multi-source extraction (AgentMail, APIs)
- Intelligent scoring with preference learning
- Automatic task creation with P0/P1/P2 priorities
- Weekly digest system
- Swarm integration (Architect, Estimation, Consensus)

## Roadmap

- [ ] toku.agency job feed integration
- [ ] Notion/Obsidian sync for idea documentation
- [ ] Revenue projection calculator
- [ ] Automated market research on promising ideas
- [ ] Skill marketplace: import/export idea templates

---

**Version**: 1.0.1  
**License**: MIT  
**Status**: Production Ready
