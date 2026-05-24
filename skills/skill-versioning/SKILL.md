# Skill Versioning

Implements semantic versioning and shadow testing for safe skill deployment.

## Quick Start

```python
from lib.version_manager import SkillVersionManager, VersionStatus

vm = SkillVersionManager("my-skill")
vm.register_version("2.0.0", "/path/to/v2.0.0", VersionStatus.SHADOW)
vm.promote("2.0.0")
```

See docs in main repository for full documentation.
