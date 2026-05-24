# User Preference Learning

Learns and persists user preferences from interactions.

## Quick Start

```python
from lib.preference_engine import PreferenceEngine

pe = PreferenceEngine("shayne")
pe.learn_trait("communication.verbosity", "low", 0.8, "explicit_feedback")
style = pe.get_communication_style()
```

See docs in main repository for full documentation.
