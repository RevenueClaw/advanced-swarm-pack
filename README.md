# RevenueClaw Advanced Swarm Pack

**v1.3.0** — Production-grade enhancements for OpenClaw

Turn a basic OpenClaw swarm into a reliable, intelligent, autonomous system.

[![Release: v1.3.0](https://img.shields.io/badge/Release-v1.3.0-blue.svg)](https://github.com/RevenueClaw/advanced-swarm-pack/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built for OpenClaw](https://img.shields.io/badge/Built%20for-OpenClaw-green)](https://openclaw.ai)
[![Status: Production](https://img.shields.io/badge/Status-Production-brightgreen)](.)

---

### Current Status
- **Version**: v1.3.0
- **Production Skills: 18
- **Total Code**: ~16,000+ lines
- **License**: MIT

---

## What's New

### v1.3.0 — Enhanced Intelligence & Code Intelligence (LATEST)
- **skill-premortem-v1**: Counter optimism bias with structured failure analysis
  - Gary Klein-style premortem: "Assume failure, then explain why"
  - Identifies most likely failures, tail risks, hidden assumptions
  - Generates Early Warning Indicators (EWIs) for monitoring
  - Integrates with Architect-First (auto-triggers for score <75)
  - Three depth levels: quick (2-3 min), standard (5-7 min), deep (10-15 min)
- **skill-codebase-understander-v1**: Deep codebase comprehension with knowledge graphs
  - Multi-language static analysis: Python, JS/TS, Go, Rust, Java
  - Local-first: No code leaves your machine
  - "What breaks if I change X?" impact analysis with file lists
  - Complexity-based time estimate adjustments for Estimation Engine
  - Dead code detection and guided architecture tours

### v1.2.2 — Credential Guardian (CRITICAL)
- **skill-credential-guardian-v1**: Prevents credential loss/corruption forever
- Auto-validation on startup, auto-restore from master if corrupted
- Timestamped backups before ANY credential file edit
- Periodic health checks every 30 minutes
- **CRITICAL**: Re-read MEMORY.md credential section

### v1.2.1 — Price Extraction Fixed
- **Amazon price extraction now works reliably**: Updated to use full offersV2 resources
- **Intelligent offer selection**: Prioritizes BuyBox winner → lowest available → any offer
- **Auto-fallback**: Web scraping triggers automatically if API returns None
- **Tested**: Radxa Rock 5C correctly returns $176.00 (was returning None)

### v1.2.0 — E-Commerce & Data Suite
- **skill-amazon-creators-api-v1**: Full Amazon Creators API integration with OAuth, affiliate links, smart ASIN detection
- **skill-price-tracker-v1**: Multi-vendor price tracking with SQLite storage, alerts, and affiliate reports
- **Integration**: Both skills work together for automated deal monitoring

### v1.1.0 — Elite Web Scraper
- **skill-web-scraper**: Production-grade stealth web scraping (2,659 lines)
- Multi-engine: Nodriver (Chrome CDP) → Camoufox → Playwright → HTTP
- 8-layer anti-detection: fingerprints, proxies, behavior, headers, session persistence
- Content extraction: JSON-LD, meta tags, prices, products
- Strictly self-hosted — no paid APIs

### v1.0.2 — Credential Manager
- **skill-credential-manager**: Robust and secure credential handling
- Automatic discovery & import of existing credentials
- Live token validation and scope checking
- Automatic redaction and audit logging
- Simple API used by all other skills

### v1.0.1 — Idea Tracker
- **skill-idea-tracker**: Turns newsletters and emails into prioritized opportunities
- 5D scoring system + automatic task creation (P0–P3)
- Weekly digests and smart backlog management

### v1.0.0 — Initial Release
- Architect-First Planning System
- Estimation Engine with historical calibration
- Calculation Verifier
- Hierarchical orchestration, visual reports, and more

---

## Before vs After: Production Reality

| **Pain Point** | **Stock OpenClaw** | **With Swarm Pack** |
|----------------|-------------------|---------------------|
| **Planning** | Jump in and hope | Architect-First with mandatory review |
| **Time estimates** | "About 2 hours" (actually 8) | Calibrated breakdowns +50%/30%/20% buffers |
| **Math in plans** | Hallucinated numbers | Python-verified calculations (99% confidence) |
| **Multi-node** | Manual coordination | Automatic worker assignment & failover |
| **Deployments** | Risky & manual | Shadow testing with graduated rollout |
| **Cost control** | Surprise bills | Tracked + auto-fallback to local GPU |
| **Preferences** | Forgotten each session | Long-term learning from HITL feedback |
| **Decisions** | Single-model guess | Multi-agent consensus when uncertain |

---

## Included Skills (18 Production-Ready)

### 🧠 Intelligence & Planning (6 skills)

**skill-architect-first** — *The crown jewel.* Production-grade planning with mandatory self-critique.
- **PlanReviewer**: 5-dimensional scoring (clarity, risk, completeness, feasibility, testability)
- **Tiered modes**: FAST (<2 tasks) → STANDARD → ARCHITECT_FIRST (5+ tasks, high risk)
- **Auto-escalation**: Score <60 or 2+ critical issues → HITL
- **Rollback first-class**: Every plan includes triggers, steps, time estimates

**skill-estimation-engine** — Accurate time estimation with historical calibration.
- Breakdown-based: Sum subtasks + 15% contingency each
- Automatic buffers: +50% novel, +30% standard, +20% known
- Per-category calibration: Coding, research, infrastructure
- Learns from actual outcomes

**skill-calculation-verifier** — Eliminates math hallucinations.
- Complexity-based routing: Mental → Calculator → Python interpreter
- Step-by-step reasoning with verification pass
- `use_tool` flag for 99% confidence on critical calculations
- Integrates with Estimation Engine for subtask verification

**skill-consensus** — Multi-agent debate for high-stakes decisions.
- 3-persona panel: Conservative (risks), Pragmatic (balance), Innovative (opportunities)
- Auto-triggers on: risk >0.6, confidence <0.7, novel situations
- Structured synthesis with caveats

**skill-premortem-v1** — Counter optimism bias with structured failure analysis (NEW v1.3.0).
- Gary Klein premortem: "Assume failure has occurred, now explain why"
- Identifies most likely failures, catastrophic tail risks, hidden assumptions
- Generates Early Warning Indicators (EWIs) for production monitoring
- Auto-integrates with Architect-First (triggers for score <75 or >3 step plans)
- Three depth levels: quick (2-3 min), standard (5-7 min), deep (10-15 min)

**skill-codebase-understander-v1** — Deep codebase comprehension via knowledge graphs (NEW v1.3.0).
- Multi-language static analysis: Python, JS/TS, Go, Rust, Java
- Impact analysis: "What breaks if I change X?" with exact file lists
- Dependency depth calculation and circular dependency detection
- Complexity-accurate time estimates for Estimation Engine
- Local-first: No code leaves your machine

### ⚙️ Orchestration & Infrastructure (4 skills)

**skill-hierarchical-orchestrator** — Task distribution across the swarm.
- Supervisor agents decompose goals
- Worker routing by capability (Rock 5B → GPU → Pi 5)
- Automatic rerouting on node failure

**skill-backend-interface** — Unified OpenRouter/Ollama API.
- **Optional GPU Node**: Local Ollama on any CUDA GPU
- Default routing: mistral:7b (heavy), llava:7b (vision), llama3.2:3b (fast)
- Auto-fallback when OpenRouter budget exceeded

**skill-web-scraper** — Elite stealth web scraping (self-hosted only, 2,659 lines).
- **Multi-engine cascade**: Nodriver (CDP Chrome) → Camoufox (stealth Firefox) → Playwright → HTTP
- **8-layer anti-detection**: Fingerprints, WebGL/canvas noise, UA consistency, human behavior, proxy rotation, session persistence, header spoofing
- **Content extraction**: JSON-LD Schema.org, OpenGraph meta, CSS selectors with fallbacks, price/product detection
- **Proxy management**: Weighted rotation, health tracking, sticky sessions, geo-matching
- **Strictly self-hosted**: No ScrapingBee, Scrapfly, or paid APIs
- **Perfect for**: SBC price tracking, competitor research, data aggregation

**skill-versioning** — Safe deployment with shadow testing.
- Semantic versioning for skills
- Shadow mode: Test invisibly alongside production
- Graduated promotion: 0% → 10% → 50% → 100%
- One-command rollback

### 💰 Observability & Operations (3 skills)

**skill-resource-awareness** — Cost tracking and budget enforcement.
- Tracks OpenRouter per-model daily/monthly ($5/$100 budgets)
- Auto-switch to local GPU when OpenRouter budget exceeded (configurable threshold)
- Latency monitoring for optimization

**skill-preference-learning** — Long-term user preference tracking.
- Communication style, risk tolerance, pace
- Planning tolerance learned (conservative → aggressive)
- Fueled by HITL feedback

**skill-newsletter-processor** — Business opportunity extraction.
- Monitors AgentMail (your-inbox@agentmail.to)
- Extracts business ideas from Side Hustle Nation emails
- Auto-cron every 2 days at 7:00 AM EDT

### 💡 Income & Opportunity (NEW in v1.0.1)

**skill-idea-tracker** — Turn newsletters and emails into prioritized, trackable business opportunities.

This skill goes beyond simple extraction. It intelligently scores ideas, automatically creates tasks for high-value ones, maintains a clean backlog, and delivers weekly digests of the best opportunities.

**Key Features:**
- 5D scoring system (Revenue Potential, Effort, AI Relevance, Strategic Fit, etc.)
- Automatic P0–P3 task creation for high-scoring ideas
- Smart duplicate detection and outcome tracking
- Weekly digest emails summarizing top opportunities
- Deep integration with Architect-First planning and Estimation Engine

**Perfect for:**
- Side hustle / income idea discovery
- Business development and opportunity management
- Turning passive newsletter reading into active execution

**Example Output:**
```
🚨 NEW HIGH-VALUE OPPORTUNITY
AI Automation Agency Model — $20K+/mo potential (P0)
Score: 74/100 | Effort: Medium | Strategic Fit: Excellent
→ Task automatically created
```

### 🛡️ Credential Persistence (NEW in v1.3.0 — CRITICAL)

**skill-credential-guardian-v1** — Prevents credential loss/corruption forever.

This is the most critical skill in the entire pack. It actively monitors credential files and automatically restores them from master backup if corrupted or missing.

**Key Features:**
- Auto-validation on startup/skill load
- Auto-restore from master backup if corrupted/missing
- Timestamped backups before ANY credential file edit
- Periodic health checks every 30 minutes
- Master store with SHA256 integrity checking
- CLI for manual backup/restore/validation

**CRITICAL RULE — NEVER FORGET:**
```python
# Before editing ANY credential file:
from credential_guardian_v1 import CredentialGuardian
guardian = CredentialGuardian()
guardian.create_timed_backup(filepath, "pre_edit")
```

This skill is now active on all nodes. See MEMORY.md for full persistence rules.

### 🔐 Infrastructure & Security (NEW in v1.0.2)

**skill-credential-manager** — Secure, reliable credential management for the entire swarm.

This skill solves one of the most common frustrations with OpenClaw — credentials being forgotten, redacted, or inaccessible between sessions.

**Key Features:**
- Secure storage with automatic redaction and audit logging
- Environment variables take priority (great for Docker/advanced users)
- Live validation for tokens (especially GitHub PATs)
- Simple, clean API that other skills can depend on
- CLI tools for easy management (`cred status`, `cred add`, `cred validate`)

This is now the recommended way for all skills to handle API keys and tokens.

**Example Usage:**
```python
# In any skill
from credential_manager import get_credential
token = get_credential("github_token")
```

### 🛒 E-Commerce & Data (NEW in v1.2.0)

**skill-amazon-creators-api-v1** — Production Amazon affiliate integration.
- OAuth 2.0 token management with automatic refresh
- Full API access: getItems, searchItems, price monitoring
- Smart ASIN detection and affiliate link generation
- Rate-limit resilience (1-retry on 429/5xx)
- **Perfect for**: Price tracking, product catalogs, affiliate automation

**skill-price-tracker-v1** — Multi-vendor price tracking with alerts.
- SQLite storage for price history
- Amazon Creators API integration (primary) + fallback scraping
- Price drop detection and target price alerts
- Generates formatted reports with affiliate links
- **Perfect for**: Deal monitoring, price alerts, SBC/electronics tracking

### 📊 Bonus: Visualization

**skill-visual-reports** — On-demand dashboards.
- Mermaid diagrams: Flowcharts, DAGs, hierarchies
- Plotly charts: Timelines, costs, latency
- Self-contained HTML with dark theme

---

## ⚡ Quick Start (5 Minutes)

```bash
# 1. Install OpenClaw base
npm install -g openclaw

# 2. Clone the pack
git clone https://github.com/RevenueClaw/advanced-swarm-pack.git
cd advanced-swarm-pack

# 3. Install all skills (v1.3.1: Now includes e-commerce skills!)
./scripts/install-skills.sh
# Installs 25+ skills including:
#  - skill-* prefixed (orchestration, planning, scraping)
#  - *_v1 suffixed (e-commerce: amazon, price-tracker, etc.)

# 4. Configure your swarm
cp configs/swarm-example.yaml ~/.openclaw/swarm-config.yaml
# Edit with your node details

# 5. Verify
openclaw nodes status
```

See [INSTALL.md](INSTALL.md) for detailed hardware setup and troubleshooting.

---

## 🏗️ Architect-First in Action

The planning system that changes everything:

```python
from skill_architect_first import PlanReviewer

# Review before execution
reviewer = PlanReviewer()
reviewed = reviewer.review({
    "goal": "Migrate production database",
    "steps": ["Step 1", "Step 2", "Step 3"],
    "risks": ["Data loss", "Downtime"],
    "success_criteria": ["Zero data loss", "<5 min downtime"]
})

# Get structured assessment
print(f"Score: {reviewed.scores.overall}/100")
print(f"Clarity: {reviewed.scores.clarity}/100")
print(f"Risk: {reviewed.scores.risk_assessment}/100")

# Auto-generated safety net
print(reviewed.acceptance_criteria.must_satisfy)
print(reviewed.rollback_plan.triggers)

# Decision: proceed or escalate?
if not reviewed.recommend_proceed:
    reviewer.should_escalate_to_human(reviewed)  # → HITL
```

**80/20 Rule**: Plan extensively (80%), execute confidently (20%). Problems caught in planning cost $1 to fix. In execution: $10. In production: $100.

---

## 🔧 Hardware Setup

### Recommended Hardware Configurations

The Swarm Pack scales from single-machine setups to multi-node clusters. Choose the configuration that fits your needs and budget.

#### Tier 1: Minimal (Single Node)

**Best for:** Getting started, personal projects, testing

| Component | Recommendation | Cost |
|-----------|----------------|------|
| **Leader** | [Radxa Rock 5B](https://www.amazon.com/Radxa-ROCK-5C-RK3588S2-32GB) or any PC with 8GB+ RAM | ~$80-200 |
| **Storage** | 128GB NVMe SSD | ~$30 |
| **GPU** | None — uses OpenRouter only | $0 |

**Total**: ~$110-250 one-time

**Performance:** Runs all features except local GPU inference. Uses OpenRouter for LLM calls.

---

#### Tier 2: Recommended (Leader + Worker)

**Best for:** Production automation, 24/7 operation, cost savings with local inference

| Component | Recommendation | Cost |
|-----------|----------------|------|
| **Leader** | [Radxa Rock 5B 32GB](https://www.amazon.com/Radxa-ROCK-5C-RK3588S2-32GB) | ~$200 |
| **Worker** | [Raspberry Pi 5 8GB](https://www.amazon.com/Raspberry-Pi-8GB-SC1112-Quad-core/dp/B0CK2FCG1K) | ~$100 |
| **Storage** | NVMe SSDs for both | ~$100 |

**Total**: ~$400 one-time

**Performance:** Distributed workload, Pi handles lightweight tasks. Good balance of power and efficiency.

---

#### Tier 3: Performance (Leader + Worker + Optional GPU Node)

**Best for:** Heavy workloads, local LLM inference, cost optimization

| Component | Recommendation | Cost |
|-----------|----------------|------|
| **Leader** | [Radxa Rock 5B 32GB](https://www.amazon.com/Radxa-ROCK-5C-RK3588S2-32GB) | ~$200 |
| **Worker** | [Raspberry Pi 5 8GB](https://www.amazon.com/Raspberry-Pi-8GB-SC1112-Quad-core/dp/B0CK2FCG1K) | ~$100 |
| **GPU Node** | Any old gaming PC or laptop with NVIDIA GPU | $0 (reuse old hardware) |
| **Storage** | NVMe SSDs | ~$150 |

**Total**: Variable ($300-600 depending on what hardware you have)

**GPU Node Examples:**
- Old gaming PC with GTX 1060+
- Previous-generation laptop with RTX 3060
- Dedicated workstation with RTX 4090
- **Don't buy new** — repurpose existing hardware!

**Performance:** Local Ollama inference saves API costs. GPU handles heavy LLM tasks.

---

### Configuration

After installation, edit `~/.openclaw/swarm-config.yaml` with your actual node IPs:

```yaml
# Example: Tier 2 - Leader + Worker
nodes:
  - name: "rock-5b-leader"
    ip: "192.168.1.10"  # CHANGEME: Your leader node IP
    role: "leader"
    
  - name: "pi-5-worker"  
    ip: "192.168.1.20"  # CHANGEME: Your worker node IP
    role: "worker"
    
# Example: Tier 3 - Add GPU node (optional)
# - name: "old-gaming-pc"
#   ip: "192.168.1.30"  # CHANGEME: Your GPU node IP if applicable
#   role: "worker"
```

**Important:** Replace `192.168.1.x` with YOUR actual local network IPs. Find them with `ip addr` on Linux or `ifconfig` on each machine.

See `configs/swarm-example.yaml` for complete configuration template with all options.

---

## 🎓 Documentation

- **[Comprehensive Skills Reference](docs/skills-comprehensive-reference.md)** — Deep dive into all 10 skills
- **[Architecture Overview](docs/architecture.md)** — System design and data flow
- **[Versioning Guide](docs/versioning.md)** — Shadow testing and promotion
- **[Troubleshooting](docs/troubleshooting.md)** — Common issues and fixes
- **[INSTALL.md](INSTALL.md)** — Detailed setup instructions

---

## 💰 Monetization & Support

**Core pack is completely free and open source (MIT).**

We're building a sustainable ecosystem:

- **[GitHub Sponsors](https://github.com/sponsors/RevenueClaw)** — Support development
  - $9/mo: Priority issue response
  - $29/mo: Monthly consultation
  - $99/mo: Architecture review

**Hardware Affiliates** (support the project):
- [Radxa Rock 5C 32GB](https://www.amazon.com/Radxa-ROCK-5C-RK3588S2-32GB/dp/B0CYZWKY39) — Leader node
- [Raspberry Pi 5 8GB](https://www.amazon.com/Raspberry-Pi-8GB-SC1112-Quad-core/dp/B0CK2FCG1K) — Worker node
- [OpenRouter](https://openrouter.ai) — Model aggregation API
- Full affiliate list in [README → Monetization](README.md#monetization--support)

---

## 🛡️ Validation & Quality

Every claim verified or marked experimental:

- ✅ All skills include self-verification (`python skill.py` → tests pass)
- ✅ GPU node tested and responding (configurable endpoint)
- ✅ End-to-end Architect-First workflow validated
- ✅ Calculation verified: Python interpreter returns precise results
- ✅ Estimation calibrated: Historical tracking functional
- 🧪 Shadow testing: Alpha (needs real-world usage to tune thresholds)

**Our standard**: If we can't verify it works, we don't claim it does.

---

## 🗺️ Roadmap

**v1.0 (Current)**: Production release with 10 core skills
**v1.1 (Next)**: Pro skill templates marketplace
**v1.2**: Web dashboard for real-time swarm visualization
**v2.0**: Multi-cloud orchestration and auto-scaling

---

## 🤝 Contributing

See [docs/contributing.md](docs/contributing.md) for:
- Development environment setup
- Skill development guidelines
- Testing requirements
- PR submission process

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for full text.

The core is free. The improvements are shared. The community benefits.

---

## 🦀 Built By

**RevenueClaw** — A 3-node OpenClaw swarm running 24/7, proving this works in production.

Started with a question: *"Can this actually run continuously without crashing?*

**Answer: Yes.**

---

**Repository**: https://github.com/RevenueClaw/advanced-swarm-pack  
**Release**: v1.0 (Production Ready)  
**Status**: Live on 3-node swarm, 15+ days uptime