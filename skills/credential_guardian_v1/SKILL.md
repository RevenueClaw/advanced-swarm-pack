# Credential Guardian v1

Prevents credential loss/corruption through validation, backup, and auto-restore.

---

## Purpose

Never lose credentials again. The Credential Guardian actively monitors critical credential files (Amazon, GitHub, etc.) and automatically restores them from master backup if corrupted or missing.

---

## Core Features

### 1. Auto-Validation on Startup
```python
from credential_guardian_v1 import CredentialGuardian

guardian = CredentialGuardian(auto_validate=True)
# Automatically checks all credentials and restores if needed
```

### 2. Pre-Edit Backups
```python
# Before editing any credential file
backup_path = guardian.create_timed_backup(
    Path("~/.openclaw/credentials/amazon_creators.env"),
    reason="pre_edit"
)
# Creates: amazon_creators.env_20260526_143022_pre_edit
```

### 3. Auto-Restore from Master
If a credential file is:
- Missing
- Empty
- Corrupted
- Contains placeholder values

The guardian automatically restores from `.master_store.json`.

### 4. Periodic Health Checks
Runs every 30 minutes in background thread to ensure credentials remain valid.

---

## Usage

### Initialize Guardian
```python
guardian = CredentialGuardian()
```

### Validate Specific Credential
```python
is_valid, message = guardian.validate_credential("amazon_creators")
print(f"Status: {message}")
```

### Validate All Credentials
```python
results = guardian.validate_all_credentials()
```

### Backup After Successful Update
```python
with open("amazon_creators.env", "r") as f:
    content = f.read()

guardian.backup_to_master("amazon_creators", "amazon_creators.env", content)
```

### Get Status
```python
status = guardian.get_status()
print(f"Backed up credentials: {status['credentials_backed_up']}")
print(f"Total backups: {status['total_backups']}")
```

---

## Storage Locations

| Location | Purpose |
|----------|---------|
| `~/.openclaw/credentials/` | Live credential files |
| `~/.openclaw/credentials/.backups/` | Timestamped backups |
| `~/.openclaw/credentials/.master_store.json` | Master backup store |

---

## Monitored Credentials

- `amazon_creators.env` - Amazon Creators API
- `github.env` - GitHub PAT

Add more in `CRITICAL_CREDENTIALS` dict.

---

## CLI Commands

```bash
# Validate all credentials
python credential_guardian_v1.py --validate

# Show status
python credential_guardian_v1.py --status

# Manual backup
python credential_guardian_v1.py --backup ~/.openclaw/credentials/amazon_creators.env

# Manual restore
python credential_guardian_v1.py --restore amazon_creators
```

---

## Integration into Skills

Add this pattern to skills that use credentials:

```python
# At skill startup
try:
    from credential_guardian_v1 import CredentialGuardian
    guardian = CredentialGuardian(auto_validate=True)
    validated = guardian.validate_all_credentials()
    
    if not all(v[0] for v in validated.values()):
        print("Warning: Some credentials failed validation")
except ImportError:
    print("Warning: credential_guardian_v1 not available")
```

---

## Security

- Master store is 600 permissions (owner read/write only)
- Backups are 600 permissions
- No credentials logged to console
- Credentials stored encrypted at rest (in master store)
