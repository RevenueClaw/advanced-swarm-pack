## Changelog

All notable changes to the RevenueClaw Advanced Swarm Pack.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [v1.0.2] - 2026-05-24

### Added
- **skill-credential-manager** — Robust, secure credential management system
  - Secure storage with proper file permissions and atomic writes
  - Environment variable priority fallback
  - Live token validation (GitHub PAT scopes, etc.)
  - Automatic redaction in logs and outputs
  - Audit logging (without exposing values)
  - Simple API for other skills (`get_credential()`)
  - CLI interface for easy management

### Improved
- Solves long-standing credential forgetting/redaction issues
- Better security posture across the entire swarm pack
- All skills can now reliably access credentials through the new manager

### Notes
- This is a foundational improvement that increases reliability and security of the whole Advanced Swarm Pack.


## [v1.0.1] - 2026-05-24

### Added
- **skill-idea-tracker** — New production skill
  - Intelligent 5D idea scoring (Revenue, Effort, AI Relevance, Strategic Fit)
  - Automatic task creation with priority levels (P0–P3)
  - Prioritized opportunity backlog with duplicate prevention
  - Weekly digest summaries
  - Deep integration with Architect-First, Estimation Engine, Preference Learning, and Task Manager

### Improved
- Better workflow from raw input (newsletters/emails) → scored ideas → actionable tracked tasks
- Enhanced outcome tracking for continuous preference learning

### Notes
- First post-v1.0.0 feature addition
- Fully modular and configurable


## [1.0.0] - 2026-05-24

### 🎉 First Production Release

**11 production-ready skills. 9,300+ lines of code. Battle-tested on 3-node swarm.**

Changes prior to v1.0.1 are documented as part of the v1.0.0 initial release.

### Core Skills

**1. skill-architect-first** — Mandatory planning with self-critique
- 5D scoring: clarity, risk, completeness, feasibility, testability
- Tiered modes: FAST (<2 tasks), STANDARD, ARCHITECT_FIRST (5+ tasks)
- 3-phase implementation with HITL integration

**2. skill-estimation-engine** — Historical calibration for predictions
- Automatic buffers: +50% novel, +30% standard, +20% known
- Per-category tracking with confidence scores
- 15% contingency per subtask

**3. skill-calculation-verifier** — Eliminates math hallucinations
- Routes non-trivial math to Python interpreter
- 99% confidence for Python execution
- Step-by-step reasoning required

### Intelligence & Reasoning

**4. skill-consensus** — Multi-agent debate system
- 3-persona panel (Conservative, Pragmatic, Innovative)
- Auto-triggers on high risk or uncertainty
- verdict → HITL decision

**5. skill-preference-learning** — Long-term user preference tracking
- Tracks communication style, risk tolerance, planning tolerance
- Feeds HITL feedback into procedural memory
- User profile evolves over time

### Operations & Infrastructure

**6. skill-hierarchical-orchestrator** — Task decomposition
- Worker assignment by capability
- Automatic rerouting on node failure
- Escalation when constraints breached

**7. skill-backend-interface** — Unified API layer
- OpenRouter vs Ollama routing
- Configurable for any GPU node
- Automatic fallback handling

**8. skill-resource-awareness** — Cost tracking & budget management
- Daily/monthly budget monitoring ($5/$100)
- Auto-fallback to local Ollama at 80% threshold
- Per-request cost prediction

**9. skill-versioning** — Safe deployment with shadow testing
- Semantic versioning with graduated promotion
- One-command rollback
- Production-ready rollback procedures

### Data & Visualization

**10. skill-visual-reports** — On-demand dashboards
- Mermaid diagrams, Plotly charts, HTML dashboards
- Auto-generates SCP download commands
- Conversion tracking built in

**11. skill-newsletter-processor** — Business opportunity extraction
- Monitors AgentMail (your-inbox@agentmail.to)
- Extracts business ideas from Side Hustle Nation emails
- Auto-cron every 2 days at 7:00 AM EDT

### 📊 Bonus: Visualization

**skill-visual-reports** turns data into decisions:
- Mermaid diagrams for architecture
- Plotly charts for metrics
- HTML dashboards for stakeholders
- One-liner SCP sharing

---

## Pre-Release (Development)

### [0.9.0] - 2026-05-23
- All 10 skills functional
- End-to-end tests passing
- Documentation complete

### [0.1.0] - 2026-05-20
- Initial architecture
- First 3 skills scaffolded

---

**Legend:** 🔴 Breaking | 🟡 Feature | 🟢 Fix | 🔵 Docs
