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

## Step 3: Configure Your Swarm (IMPORTANT)

**This is the most critical step.** The Swarm Pack needs to know about your specific nodes.

### 3.1 Copy Example Configuration

```bash
cp configs/swarm-example.yaml ~/.openclaw/swarm-config.yaml
```

### 3.2 Edit with YOUR Values

Open `~/.openclaw/swarm-config.yaml` in your editor and **replace ALL placeholder values (YOUR_*)** with your actual configuration:

**Required Changes:**
- `YOUR_USERNAME` → your actual username
- `YOUR_LEADER_IP` → IP of your leader node (or `127.0.0.1` if single machine)
- `YOUR_GPU_IP` → IP of your GPU node (if you have one)
- `${OPENROUTER_API_KEY}` → your actual OpenRouter API key

**Example for single-machine setup:**
```yaml
nodes:
  - name: "my-desktop"
    ip: "127.0.0.1"  # Single machine = localhost
    role: "leader"
    # ... rest of config
```

**Example for multi-node setup:**
```yaml
nodes:
  - name: "rock-5b"
    ip: "192.168.1.10"  # Your leader node IP
    role: "leader"
    # ...
  - name: "workstation"
    ip: "192.168.1.20"  # Your GPU node IP
    role: "worker"
    # ...
```

### 3.3 Configure Ollama (Optional but Recommended)

If you have a GPU for local inference:

```yaml
backends:
  ollama:
    enabled: true
    endpoint: "http://YOUR_GPU_IP:11434"  # e.g., "http://192.168.1.20:11434"
    default_model: "mistral:7b"
```

If you don't have a GPU, set `enabled: false` and rely on OpenRouter.

**Full template:** See `configs/swarm-example.yaml` for all configuration options with detailed comments.

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

# Expected output (example - your node names will differ):
# my-leader: connected, leader
# my-worker: connected, worker
# my-gpu: connected, worker (if configured)

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
- Email: See README.md for contact options
