# User Preference Learning

Learns and persists user preferences from interactions.

## Quick Start

```python
from lib.preference_engine import PreferenceEngine

pe = PreferenceEngine("shayne")
pe.learn_trait("communication.verbosity", "low", 0.8, "explicit_feedback")
style = pe.get_communication_style()
```

## Complex Coding Preferences (v1.3.0+)

Built-in defaults for production-grade coding:

```python
pe = PreferenceEngine("shayne")

# Get all coding preferences
coding_prefs = pe.get_coding_preferences()
# Returns:
# {
#   "path_resolution": "runtime",      # Never resolve at import-time
#   "file_operations": "atomic",         # temp file + rename only
#   "backup_required": True,             # Always backup before edit
#   "logging_pattern": "runtime_paths",  # Log actual paths, not assumed
#   "docker_aware": True,                # Consider volumes, startup order
#   "import_time_safe": True             # No DB/network on import
# }

# Get safe edit checklist
checklist = pe.get_safe_edit_checklist()
# Returns structured checklist for:
#   - mandatory (backups, atomic writes, integrity)
#   - for_docker (syntax check, health verify, volume inspect)
#   - for_python (no import-time DB, runtime path resolution)
```

### Preference Injection

These preferences automatically flow into:
- **skill-architect-first**: Included in plan context
- **skill-codebase-understander**: Guides analysis priorities
- **All coding agents**: Via system prompt context

See docs in main repository for full documentation.
