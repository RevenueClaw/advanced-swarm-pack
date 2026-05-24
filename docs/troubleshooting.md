# Troubleshooting Guide

## Quick Diagnostics

Before diving deep, run:

```bash
# Full health check
openclaw doctor

# Node connectivity
openclaw nodes status

# Skill tests
python -m pytest ~/.openclaw/workspace/skills/ -v

# Disk space
df -h ~/.openclaw/

# Memory usage
free -h
```

---

## Common Issues

### "Node disconnected"

**Symptoms**: `openclaw nodes status` shows disconnected worker

**Diagnosis**:
```bash
# From leader, ping worker
ping <worker-ip>

# Check OpenClaw service on worker
ssh <worker> "systemctl status openclaw"

# Check logs
ssh <worker> "journalctl -u openclaw -n 50"
```

**Solutions**:
1. **Network issue**: Check firewall, ensure port 8080 open
2. **Service down**: `systemctl restart openclaw`
3. **Out of memory**: Check `free -h`, restart if near limit
4. **Corrupted state**: Re-pair node

---

### "Skill import error"

**Symptoms**: `ModuleNotFoundError: skill_versioning`

**Solution**:
```bash
# Install skills properly
cd ~/.openclaw/workspace/skills
chmod +x install-skills.sh
./install-skills.sh

# Or manually
export PYTHONPATH="${PYTHONPATH}:$(realpath ~/.openclaw/workspace/skills/skill-versioning/lib)"
```

---

### "Cost tracking not recording"

**Symptoms**: Daily spend shows $0 despite usage

**Check**:
```bash
ls -la ~/.openclaw/workspace/skills/skill-resource-awareness/cost_logs/daily/
# Should show today's file

# Check if writable
touch ~/.openclaw/workspace/skills/skill-resource-awareness/cost_logs/daily/test
rm ~/.openclaw/workspace/skills/skill-resource-awareness/cost_logs/daily/test
```

**Fix**:
```bash
mkdir -p ~/.openclaw/workspace/skills/skill-resource-awareness/cost_logs/daily
chmod 755 ~/.openclaw/workspace/skills/skill-resource-awareness/cost_logs/daily
```

---

### "Shadow mode not running"

**Symptoms**: Version always shows `production`, no shadow comparison

**Check**:
```python
from skill_versioning import SkillVersionManager

vm = SkillVersionManager("my-skill")
shadows = vm.get_shadow_versions()
print(shadows)  # Should list shadow versions
```

**Fix**: Ensure shadow version registered:
```python
vm.register_version(
    "2.0.0",
    Path("/path/to/v2.0.0"),
    status=VersionStatus.SHADOW
)
```

---

### "Preference not persisting"

**Symptoms**: Learned preference forgotten after restart

**Check**:
```bash
# Check file exists
ls -la ~/.openclaw/workspace/skills/skill-preference-learning/preferences/shayne-profile.json

# Check content
cat ~/.openclaw/workspace/skills/skill-preference-learning/preferences/shayne-profile.json | head -20
```

**Fix**:
Make sure preference engine initialized with correct user_id:
```python
from preference_engine import PreferenceEngine
pe = PreferenceEngine("shayne")  # Must match filename
```

---

### "Debate not triggering"

**Symptoms**: High-uncertainty decisions skip debate

**Check trigger conditions**:
```python
from debate_orchestrator import DebateOrchestrator

orch = DebateOrchestrator()
should_debate = orch.should_debate(
    risk_score=0.7,
    confidence=0.5,
    has_rejection_history=False,
    is_novel=True
)
print(should_debate)  # Should be True
```

**Solution**: Ensure conditions met:
- Risk > 0.6 OR
- Confidence < 0.7 OR
- Novel situation OR
- User rejected similar before

---

### "Session corruption after crash"

**Symptoms**: Gateway won't start, orphaned session errors

**Fix**:
```bash
# Run safe cleanup
~/scripts/orphaned-session-cleanup.sh

# If still failing
cp ~/.openclaw/config.json ~/.openclaw/config.json.backup
rm ~/.openclaw/agents/main/sessions/*.deleted.*
openclaw doctor -fix
openclaw restart
```

---

### "Ollama not falling back"

**Symptoms**: Continuing to use OpenRouter after budget exceeded

**Check**:
```bash
# Verify Ollama running
curl http://<gpu-node>:11434/api/tags

# Check budget tracking
python -c "
from cost_tracker import CostTracker
t = CostTracker()
print(t.get_daily_spend())
print(t.get_monthly_spend())
print(t.should_use_local())
"
```

**Fix**:
1. Start Ollama: `