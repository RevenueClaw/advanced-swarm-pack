# Configuration Files

## local-llama-profiles.yaml

Defines local llama.cpp model endpoints and routing policies for v1.4.0.

**Copy to your home directory:**
```bash
cp configs/local-llama-profiles.yaml ~/.openclaw/config/
```

**Edit with your endpoints**, then restart any skills.

## Integration

This config is read by:
- `skill-local-llama-runner-v1`
- `skill-backend-interface` (updated for v1.4.0)
- `skill-resource-awareness` (for cost tracking)
