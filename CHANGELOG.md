## Changelog

All notable changes to the RevenueClaw Advanced Swarm Pack.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [v1.3.1] - 2026-05-29

### Fixed
- **install-skills.sh**: Now properly installs ALL skills, including v1 suffixed e-commerce skills
  - Fixed: Script only matched `skill-*` pattern, missing `*_v1` skills (amazon_creators_api_v1, price_tracker_v1, etc.)
  - Added: Loop for `*_v1` directory pattern
  - Added: Proper symlink creation to `~/.openclaw/workspace/skills/`
  - Added: Installation statistics (new/skipped/total)
  - Changed: Creates symlinks instead of just setting up directories
  
### Impact
- E-commerce skills now properly deploy: amazon_creators_api_v1, price_tracker_v1, multi_vendor_tracker_v1, deal_alert_engine_v1, content_generator_v1, credential_guardian_v1
- Skills are now accessible via standard OpenClaw skill loading mechanism
- Total skills properly deployed: 25+

---

## [v1.3.0] - 2026-05-28

### Added
- **skill-premortem-v1**: Structured failure analysis to counter optimism bias
  - Gary Klein-style premortem: "Assume failure, then explain why"
  - Identifies most likely failures, tail risks, and hidden assumptions
  - Generates Early Warning Indicators (EWIs) for monitoring
  - Creates revised plan with embedded mitigations
  - Outputs risk score adjustments for PlanReviewer
  - Three depth levels: quick (2-3 min), standard (5-7 min), deep (10-15 min)

- **skill-codebase-understander-v1**: Deep codebase comprehension via knowledge graphs
  - Multi-language static analysis (Python, JavaScript/TypeScript, Go, Rust, Java)
  - Local-first: No code leaves your machine
  - Impact analysis: "What breaks if I change X?"
  - Dependency chain mapping and circular dependency detection
  - Dead code identification
  - Guided tours for onboarding and feature exploration
  - Auto-generates complexity reports for Estimation Engine calibration
  - Optional integration with Understand-Anything self-hosted pipeline

### Changed
- **skill-architect-first**: Enhanced review with premortem and codebase context
  - EnhancedPlanReviewer class extends base PlanReviewer
  - Auto-triggers premortem for plans scoring <75 or with >3 steps
  - Injects codebase context for development plans (complexity, dependency depth)
  - Adds critical mitigations to recommendations from premortem analysis
  - Adjusts scores based on hidden risks discovered

- **skill-estimation-engine**: Improved calibration with codebase data
  - Complexity-based adjustments: high fan-out, tight coupling detection
  - Test coverage gap adjustments (+15-30% when untested dependents found)
  - Separate "risk-adjusted" vs "optimistic" estimates
  - Refactor-specific estimation guidance

- **skill-consensus**: Optionally includes premortem insights in debates
  - Conservative persona receives tail risk awareness
  - Debate context enriched with hidden assumptions

### Stats
- Total skills: 18 (from 16)
- Total code: ~16,000 lines
- New integration points: 5 (Premortem ↔ Architect-First, Codebase ↔ Architect-First, Codebase ↔ Estimation, Premortem ↔ Consensus, Premortem ↔ Estimation)


## [v1.2.2] - 2026-05-26

### Added
- **skill-credential-guardian-v1**: Prevents credential loss/corruption forever
  - Auto-validation on startup/skill load
  - Auto-restore from master backup if corrupted/missing
  - Timestamped backups before any file edit in credential folders
  - Periodic health checks every 30 minutes
  - Master store with SHA256 hashing for integrity
  - CLI for manual backup/restore/validation
  - Strong MEMORY.md entry re-loaded on every context refresh
- **CRITICAL**: Credential persistence now enforced via guardian pattern

### Stats
- Total skills: 16 (from 15)
- Total code: ~14,000 lines


## [v1.2.1] - 2026-05-26

### Fixed
- **Amazon Creators API price extraction**: Now returns actual prices instead of None
  - Added all required offersV2 resources: price, availability, isBuyBoxWinner, condition
  - Implements intelligent offer prioritization (BuyBox winner > lowest available > any)
  - Real-world test: Radxa Rock 5C now returns $176.00 (was returning None)
  - Maintains rate-limit resilience and retry logic

### Changed
- **price_tracker_v1**: Auto-fallback to web scraping when API lacks price data
  - Merges API metadata (title, images) with scraped price
  - Transparent to calling code - just works


## [v1.2.0] - 2026-05-26

### Added
- **skill-amazon-creators-api-v1** — Full Amazon Creators API integration
  - OAuth 2.0 client credentials flow with automatic token refresh
  - `getItems` and `searchItems` endpoints fully implemented
  - Smart ASIN detection from URLs, search terms, or direct input
  - Automatic affiliate link generation with partner tag
  - Rate-limit resilience: 1 automatic retry on 429/5xx errors
  - Response parsing: Handles `searchResult` and `itemsResult` structures
  - Case-insensitive ASIN matching
  - Fallback to web scraping if API unavailable
  - Production-tested: Average response time ~1.3s

- **skill-price-tracker-v1** — Multi-vendor price tracking with alerts
  - SQLite storage for persistent price history
  - Amazon Creators API integration (primary data source)
  - Web scraping fallback for resilience
  - Price drop detection with percentage thresholds
  - Target price alerts for deal hunting
  - Formatted reports with affiliate links
  - ASIN/URL/search term input support
  - Staggered checks to avoid rate limits
  - CLI and Python API for automation

### Integration Notes
- Both skills work together seamlesly: `price_tracker_v1` uses `amazon_creators_api_v1` as primary data source
- Perfect for automated deal monitoring, SBC price tracking, affiliate content generation
- Credentials stored securely in `~/.openclaw/credentials/` (600 permissions)

### Stats
- Total skills: 15 (from 13)
- Total code: ~13,500 lines (from ~12,000)


## [v1.1.0] - 2026-05-25

### Added
- **skill-web-scraper** — Elite self-hosted stealth web scraping
  - **🎉 MAJOR FEATURE: Multi-Engine Scraping** — Intelligent fallback between:
    - **Nodriver** (primary): Chrome CDP-based, best-in-class stealth
    - **Camoufox**: Modified Firefox with superior fingerprint resistance
    - **Playwright**: Reliable fallback with stealth patches
    - **HTTP**: Lightweight fallback for simple sites
  - **Comprehensive Anti-Detection (8 layers):**
    - Fingerprint consistency: UA, viewport, timezone, WebGL, canvas noise
    - Proxy rotation: Weighted selection, health tracking, sticky sessions
    - Human behavior: Curved mouse paths, natural scrolling, realistic delays
    - Header consistency: Full Sec-CH-UA* support, proper referer chains
    - Session persistence: Cookie/localStorage continuity
    - Behavioral mimicry: Gaussian delays, micro-pauses, reading simulation
    - Honeypot avoidance: Detection of hidden/zero-size elements
    - Intelligent retry: Exponential backoff, engine rotation on blocks
  - **Content Extraction:**
    - Schema.org JSON-LD extraction
    - Meta tag (OpenGraph) parsing
    - CSS selector chains with fallbacks
    - Type-specific extraction (products, articles, prices)
    - Price detection with currency recognition
  - **Self-Hosted Only Design:**
    - Strict adherance: NO paid APIs (ScrapingBee, Scrapfly, etc.)
    - Open-source browser engines only
    - Free proxy support with optional rotation
    - Local credential storage
  - **Swarm Integration:**
    - Async API for other agents
    - Batch processing with concurrency control
    - Health monitoring and block rate tracking
    - Structured output with confidence scores
  - **Production Ready:**
    - 2,659 lines of Python
    - Full documentation with examples
    - CLI interface for testing
    - ~90%+ success rate on protected sites

### Notes
- Requires Chrome/Firefox browser installation
- Best performance with rotating residential proxies
- Ethical use: respects robots.txt, rate limits, ToS

---

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
