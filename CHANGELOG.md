# Changelog

All notable changes to the Advanced Swarm Pack will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-alpha] - 2026-05-24

### Added (Foundation Release)

This is the initial public release of the Advanced Swarm Pack, representing ~3 months of iterative development.

#### Core Systems

- **Hierarchical Task Orchestration** (`skill-hierarchical-orchestrator/`)  
  Supervisor-agent pattern with automatic task decomposition and worker assignment.

- **Skill Versioning + Shadow Testing** (`skill-versioning/`)  
  - Semantic versioning (major.minor.patch)
  - Shadow mode runs new versions invisibly alongside production
  - Graduated promotion (0% → 10% → 50% → 100%)
  - Instant rollback to previous stable version
  - Atomic JSON persistence

- **User Preference Learning** (`skill-preference-learning/`)  
  - Persistent user profiles with confidence scoring
  - Automatic extraction from HITL feedback (12 explicit patterns)
  - Workflow pattern recognition
  - Decision helpers for runtime integration
  - Feedback classification: explicit, correction, confirmation, rejection, escalation

- **Multi-Agent Consensus** (`skill-consensus/`)  
  - 3-persona debate panel: Conservative, Pragmatic, Innovative
  - Automatic debate triggers (risk >0.6, confidence <0.7, novel situations)
  - Structured synthesis with caveats

- **Resource + Cost Awareness** (`skill-resource-awareness/`)  
  - OpenRouter cost tracking per model
  - Daily/monthly budget enforcement ($5/$100)
  - Auto-fallback to Ollama when budget exceeded
  - Latency monitoring

- **Health Monitoring** (`skill-health-monitor/`)  
  - 30-minute health checks
  - Session state monitoring
  - Automated orphaned session cleanup
  - Critical alert thresholds

- **HITL (Human-in-the-Loop)** (`skill-hitl/`)  
  - Structured feedback capture
  - Feedback type classification
  - Confidence delta tracking

- **Backend Interface** (`skill-backend-interface/`)  
  - Unified API for OpenRouter vs Ollama
  - Capability-based routing
  - Error handling and fallback

- **Multi-Modal Support** (`skill-multi-modal/`)  
  - Image, audio, video handling
  - Frame extraction from video
  - Audio transcription

#### Documentation

- Complete README.md with Before/After comparison
- Installation guide (INSTALL.md)
- Architecture documentation
- Skills reference
- Troubleshooting guide

#### Verification

- All skills include self-verification (`python skill.py` runs tests)
- No claims without evidence
- Validation on every feature
- Production-ready defaults

### Known Limitations (Alpha)

- Shadow testing: needs real-world usage to tune thresholds
- Ollama integration: tested locally, pending multi-node verification
- Consensus: Prompt framework complete, subagent spawning pending
- Preference learning: Confidence decay not yet implemented

### Hardware Tested

- Radxa Rock 5B (32GB RAM) - Leader node
- HP Omen 17t (16GB RAM, RTX 3060) - GPU worker
- Raspberry Pi 5 (8GB) - Light worker

### Requirements

- OpenClaw >= 2026.5.18
- Python >= 3.10
- Linux (ARM64 or x86_64)

---

## [0.9.0] - 2026-05-15

### Internal Testing

- Multi-node staging environment
- Load testing for orchestration
- Cost tracking validation

## [0.5.0] - 2026-04-01

### Major Refactor

- Migrated from monolithic to modular skill architecture
- Added versioning infrastructure
- Implemented preference learning v1

## [0.1.0] - 2026-02-01

### Initial Development

- Single-node OpenClaw setup
- Basic agent spawning experiments
- Session corruption incident (motivation for stability focus)
