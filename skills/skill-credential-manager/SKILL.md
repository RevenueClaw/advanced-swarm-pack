# Skill: Credential Manager

**Secure, robust API credential management for the OpenClaw swarm.**

## Overview

A centralized credential management system that other skills depend on for secure API key storage, validation, and access auditing.

## Core Principles

1. **Security First**: Files are 600 permissions, values are never logged
2. **Redaction Protection**: Automatic masking of credentials in output
3. **Audit Trail**: Know which skill accessed what and when
4. **Flexible Storage**: Environment variables → Secure files → Keyring (future)
5. **Validation**: Test credentials against live APIs before use

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 SKILL INTERFACE                             │
│  from credential_manager import get_credential             │
│  token = get_credential("github_token")                     │
└───────────────┬─────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────┐
│              CredentialManager                              │
│  ┌─────────────┐  ┌───────────┐  ┌──────────┐            │
│  │   Storage   │  │ Validator │  │  Audit   │            │
│  │  (Chained)  │──│   (Live)  │──│  Logger  │            │
│  └─────────────┘  └───────────┘  └──────────┘            │
├─────────────────────────────────────────────────────────────┤
│  Loading Priority: Env Var → Secure File → Keyring (future) │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### For Other Skills

```python
# Simple usage
from credential_manager import get_credential

token = get_credential("github_token")

# With defaults
api_key = get_credential("agentmail_api_key", default="fallback_key")

# Full interface
from credential_manager import CredentialManager

mgr = CredentialManager()
token = mgr.require("github_token", required_scopes=["repo"])
```

### CLI Usage

```bash
# Check all credentials
cd skills/skill-credential-manager
python3 lib/credential_manager.py status

# Add new credential
python3 lib/credential_manager.py add \
    --name github_token \
    --value ghp_xxxx \
    --service github \
    --scopes repo,workflow

# Validate a credential
python3 lib/credential_manager.py validate --name github_token

# Delete credential
python3 lib/credential_manager.py delete --name old_token
```

## Storage Backends

### 1. Environment Variables (Priority 1)

```bash
# Automatically detected
export GITHUB_TOKEN="ghp_xxx"
export AGENTMAIL_API_KEY="xxx"
export ABUND_API_KEY="xxx"
```

**Use for:** Docker, CI/CD, temporary tokens

### 2. Secure File Storage (Priority 2)

```bash
~/.openclaw/credentials/
├── .credential_index          # Metadata (hashed names)
├── <hashed>.cred              # Individual encrypted files
├── .audit/                     # Access logs
│   └── 2026-05.jsonl
└── README                      # Setup instructions
```

**Permissions:** 600 (owner read/write only)

**Use for:** Long-term storage, shareable across sessions

### 3. System Keyring (Future Priority 3)

DBus Secret Service / macOS Keychain integration.

## Supported Services

| Service | Token Type | Required Scopes | Validation |
|---------|-----------|-----------------|------------|
| **GitHub** | Personal Access Token | `repo` | ✅ Live API check |
| **AgentMail** | API Key | - | ✅ Health endpoint |
| **Abund.ai** | API Key | - | ⚠️ Planned |
| **OpenRouter** | API Key | - | ⚠️ Planned |

## Security Features

### Automatic Redaction

```python
# This will NEVER print full tokens
from credential_manager import CredentialManager

mgr = CredentialManager()
status = mgr.status()
print(status["github_token"].masked_value)  # "ghp_...abcd"
```

### Audit Logging

Every access is logged with:
- Timestamp
- Credential hash (not value)
- Calling skill
- Action (get/set/delete/validate)
- Success/failure

**Logged:** `skill-idea-tracker` accessed `github_token` at 14:30  
**Never logged:** The actual token value

### Permission Enforcement

```python
# Files created with 600 permissions
owner = read + write
group = no access
other = no access
```

## Validation

Credentials can be validated against live APIs:

```python
mgr = CredentialManager()
result = mgr.validate("github_token")

if result == ValidationResult.VALID:
    print("✅ Token is valid and has required scopes")
elif result == ValidationResult.INSUFFICIENT_SCOPES:
    print("❌ Token valid but missing scopes")
```

## Integration with Other Skills

### Preference Learning

Tracks which services you use most:
- "User prefers GitHub PAT over OAuth"
- "AgentMail accessed 50x/week"

### Resource Awareness

Can detect API usage per credential:
- Rate limit tracking
- Cost estimation for paid APIs

### Architect-First

When planning credential-dependent tasks:
```python
architect.plan_step(
    "Set up GitHub token",
    requires=["github_token", "repo"]
)
```

## CLI Reference

```bash
# Status
python3 lib/credential_manager.py status

# Add with interactive prompt (secure)
python3 lib/credential_manager.py add \
    --name token_name \
    --service github \
    --scopes repo

# Only then paste value at prompt

# Batch add from env
python3 lib/credential_manager.py add \
    --name github_token \
    --value "$GITHUB_TOKEN" \
    --service github

# Get value (for scripts)
token=$(python3 lib/credential_manager.py get --name github_token)

# Validate
credential_manager.py validate --name github_token
```

## Configuration

`~/.openclaw/config/credential-manager.yaml`:

```yaml
# Storage settings
storage:
  prefer_keyring: false      # Use system keyring if available
  backup_enabled: true      # Daily backup of credentials
  backup_count: 7          # Keep 7 days

# Security settings
security:
  log_all_access: true
  max_audit_entries: 10000
  require_validation: false

# Service defaults
services:
  github:
    default_scopes: ["repo", "workflow"]
  agentmail:
    auto_validate: true
```

## Error Handling

```python
from credential_manager import (
    CredentialManager,
    CredentialNotFoundError,
    InsufficientScopesError
)

mgr = CredentialManager()

try:
    token = mgr.require("github_token", ["repo"])
except CredentialNotFoundError:
    print("Run: credential_manager.py add --name github_token")
except InsufficientScopesError as e:
    print(f"Token missing scopes: {e}")
```

## Roadmap

- [x] v1.0.2 - Core file storage, env var fallback
- [ ] v1.1.0 - System keyring integration (dbus, keychain)
- [ ] v1.2.0 - GPG encryption for files
- [ ] v1.3.0 - Credential rotation reminders
- [ ] v1.4.0 - Hardware token support (YubiKey)

## Files

```
skills/skill-credential-manager/
├── SKILL.md
├── lib/
│   ├── __init__.py
│   ├── credential_manager.py   # Main interface (~450 lines)
│   ├── storage.py              # Storage backends (~200 lines)
│   ├── validator.py            # Live validation (~100 lines)
│   └── audit.py                # Audit logging (~180 lines)
└── tests/
    └── test_credential_manager.py

Runtime storage:
~/.openclaw/credentials/
├── .credential_index
├── <hashed>.cred files
└── .audit/
    └── YYYY-MM.jsonl
```

### Code Stats
- **Total**: ~950 lines Python
- **Test Coverage**: Self-verifying modules
- **Security**: File permissions 600, no value logging

---

**Version**: 1.0.2  
**License**: MIT  
**Status**: Production Ready  
