## Changelog

All notable changes to the RevenueClaw Advanced Swarm Pack.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [v1.0.2] - 2026-05-24

### Added
- **skill-credential-manager** — Robust, secure credential management system
  - **🎉 MAJOR FEATURE: Comprehensive Auto-Discovery & Import** — Automatically finds and imports credentials from:
    - Environment variables (GITHUB_TOKEN, OPENROUTER_API_KEY, ANTHROPIC_API_KEY, AGENTMAIL_API_KEY, OLLAMA_*, etc.)
    - OpenClaw native locations (~/.openclaw/credentials/*.env, ~/.openclaw/workspace/config/*.yaml)
    - Standard locations (~/.env, project root .env)
    - Common tool configs (~/.config/openrouter/*.json, ~/.ollama/config.json)
    - GitHub CLI authentication (gh auth status detection)
  - **Smart Detection Engine:**
    - Service recognition via regex patterns (GitHub PATs, Anthropic keys, OpenRouter tokens)
    - Confidence scoring (0-100%) per detected credential
    - Automatic deduplication (won't import same token twice)
    - Critical service protection (GitHub/AgentMail/OpenRouter require manual review)
  - Secure storage with proper file permissions (600) and atomic writes
  - Environment variable priority fallback
  - Live token validation (GitHub PAT scopes, AgentMail health checks)
  - Automatic redaction in logs and outputs (masks: ghp_...abcd)
  - Comprehensive audit logging (without exposing values)
  - Simple API for other skills (`get_credential()`)
  - CLI interface with auto-discovery on first run

### Improved
- Solves long-standing credential forgetting/redaction issues across entire swarm
- Better security posture for the whole Advanced Swarm Pack
- All skills can now reliably access credentials through unified manager
- First-run experience massively improved (no manual credential setup)

### Notes
- This is a **foundational improvement** that increases reliability and security
- First skill to run will trigger automatic credential discovery
- Fully backward compatible (old .env files still work)

---

## [v1.0.1] - 2026-05-24

### Added
- **skill-idea-tracker** — Business opportunity pipeline
  - 5D scoring system (Revenue, Effort, AI Relevance, Strategic Fit)
  - Automatic task creation (P0–P3)
  - Prioritized backlog
  - Weekly digests

## Older versions...
