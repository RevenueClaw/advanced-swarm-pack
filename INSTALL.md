# Installation Guide

## Prerequisites

- **OpenClaw** installed and configured ([docs.openclaw.ai](https://docs.openclaw.ai))
- **Git** for cloning
- **Python 3.10+** for skill modules

## Step 1: Clone the Repository

```bash
git clone https://github.com/RevenueClaw/advanced-swarm-pack.git
cd advanced-swarm-pack
```

## Step 2: Install Skills

```bash
# Install all skills
./scripts/install-skills.sh

# Or install individually
openclaw skill add skills/skill-versioning/
openclaw skill add skills/skill-preference-learning/
openclaw skill add skills/skill-consensus/
openclaw skill add skills/skill-resource-awareness/
```

## Step 3: Configure Your Swarm

Copy the example configuration:

```bash
cp configs/swarm-example.yaml ~/.openclaw/swarm-config.yaml
```

Edit `~/.openclaw/swarm-config.yaml`:

```yaml
swarm:
  name: "my-swarm"
  leader_node: "rock-5b"
  
nodes:
  - name: "rock-5b"
    ip: "192.168.1.100"
    role: "leader"
    specs:
      ram_gb: 32
      storage_gb: 500
    capabilities: ["orchestration", "heavy_context", "memory"]
    
  - name: "omen-gpu"
    ip: "192.168.1.101"
    role: "worker"
    specs:
      ram_gb: 16
      gpu: "RTX 3060"
    capabilities: ["cuda_inference", "embedding", "ollama"]
    
  - name: "pi-5"
    ip: "192.168.1.102"
    role: "worker"
    specs:
      ram_gb: 8
    capabilities: ["light_scripts", "monitoring"]

backends:
  openrouter:
    enabled: true
    model: "openrouter/moonshotai/kimi-k2.5"
    
  ollama:
    enabled: true
    endpoint: "http://192.168.1.101:11434"
    default_model: "llama3:8b"
    fallback_threshold: 0.8  # 80% of daily budget triggers fallback

versioning:
  registry_path: ~/.openclaw/versions/
  
preference_learning:
  user_id: "your-username"
  storage_path: ~/.openclaw/preferences/
```

## Step 4: Node Pairing

On the leader node, generate pairing codes for workers:

```bash
# Leader
openclaw nodes pair --generate

# On each worker node
openclaw nodes pair --code <generated-code>
```

## Step 5: Verify Installation

```bash
# Check node status
openclaw nodes status

# Expected output:
# rock-5b: connected, leader
# omen-gpu: connected, worker
# pi-5: connected, worker

# Test skill versioning
python -c "from skill_versioning import SkillVersionManager; print('✓ Versioning OK')"

# Test preference learning
python -c "from preference_engine import PreferenceEngine; print('✓ Preferences OK')"
```

## Troubleshooting

### Issue: Nodes won't pair
- Ensure all nodes are on the same network
- Check firewall rules (port 8080 default)
- Verify OpenClaw version match across nodes

### Issue: Skill import errors
- Install Python dependencies: `pip install -r requirements.txt`
- Ensure `~/.openclaw/workspace/skills/` is on PYTHONPATH

### Issue: Ollama not falling back
- Verify Ollama is running: `curl http://<gpu-node>:11434/api/tags`
- Check cost tracker logs: `tail ~/.openclaw/skills/skill-resource-awareness/cost_logs`

## Support

- [GitHub Issues](https://github.com/RevenueClaw/advanced-swarm-pack/issues)
- [Discussions](https://github.com/RevenueClaw/advanced-swarm-pack/discussions)
- Email: shayne@revenueclaw.com
