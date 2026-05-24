# RevenueClaw Advanced Swarm Pack v1.0 🚀

> **Enterprise-grade multi-agent orchestration for OpenClaw. The missing production layer.**

[![Release: v1.0](https://img.shields.io/badge/Release-v1.0-blue.svg)](https://github.com/RevenueClaw/advanced-swarm-pack/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Built for OpenClaw](https://img.shields.io/badge/Built%20for-OpenClaw-green)](https://openclaw.ai)
[![Status: Production](https://img.shields.io/badge/Status-Production-brightgreen)](.)

---

## 🎯 What Is This?

The **Advanced Swarm Pack** transforms OpenClaw from a capable single-agent assistant into a **distributed, production-ready multi-agent swarm** that runs continuously without crashing.

Built from the ground up on a **Radxa Rock 5B** (32GB RAM) with a simple mandate: *must run 24/7 without manual intervention.*

**10 production-ready skills. 8,500+ lines of code. Battle-tested.**

---

## 🏆 What's New in v1.0

This release represents a significant leap forward in multi-agent reliability and intelligence:

| **New System** | **Problem Solved** | **Key Capability** |
|----------------|-------------------|-------------------|
| **🏗️ Architect-First Planning** | "Plans fail because we don't think before acting" | Mandatory self-critique with 5D scoring |
| **⏱️ Estimation Engine** | "Time estimates are always wrong" | Historical calibration with automatic buffers |
| **🧮 Calculation Verifier** | "Math hallucinations" | Step-by-step Python-verified calculations |
| **🖥️ Optional GPU Node** | "OpenRouter costs spiraling" | Local Ollama fallback on any NVIDIA GPU |
| **📧 Newsletter Processor** | "Missing business opportunities" | Auto-extract ideas from emails |

**Plus 5 battle-tested foundational skills** for orchestration, learning, consensus, cost management, versioning, and visualization.

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

## The 10 Skills

### 🧠 Intelligence & Planning (4 skills)

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

### ⚙️ Orchestration & Infrastructure (3 skills)

**skill-hierarchical-orchestrator** — Task distribution across the swarm.
- Supervisor agents decompose goals
- Worker routing by capability (Rock 5B → GPU → Pi 5)
- Automatic rerouting on node failure

**skill-backend-interface** — Unified OpenRouter/Ollama API.
- **Optional GPU Node (NEW)**: Local Ollama on any CUDA GPU — gaming PC, old laptop, or workstation
- Default routing: mistral:7b (heavy), llava:7b (vision), llama3.2:3b (fast)
- Auto-fallback when OpenRouter budget exceeded

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

# 3. Install all 10 skills
./scripts/install-skills.sh

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