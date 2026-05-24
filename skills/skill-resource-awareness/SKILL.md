# Resource & Cost Awareness

Tracks costs and routes between OpenRouter and local Ollama.

## Quick Start

```python
from lib.cost_tracker import CostTracker

tracker = CostTracker()
cost = tracker.record_usage("openrouter", "kimi-k2.5", 5000, 2000, 1200)
should_local = tracker.should_use_local()
```

See docs in main repository for full documentation.
