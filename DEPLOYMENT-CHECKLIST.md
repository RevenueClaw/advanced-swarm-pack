# v1.4.0 Deployment Checklist

**Goal**: Deploy local llama.cpp models and activate v1.4.0 cost optimization

---

## Pre-Deployment Status

✅ All skills implemented and tested  
✅ Configuration files ready  
✅ Documentation complete  
⏳ Deployment to rock-5c pending

---

## Step 1: Deploy llama.cpp Servers on rock-5c

### 1.1 Install llama.cpp (if not already)
```bash
ssh rock-5c
# Clone and build
# Follow: https://github.com/ggerganov/llama.cpp#build
```

### 1.2 Download Models
```bash
# Fast model - qwen3-8b-q5
llama-cli --repo Revmorgan/qwen3-8b-q5 --model qwen3-8b-q5.gguf

# Balanced model - qwen3-14b-q4  
llama-cli --repo Revmorgan/qwen3-14b-q4 --model qwen3-14b-q4.gguf

# Overnight model - qwen3-30b-a3b-q4
llama-cli --repo Revmorgan/qwen3-30b-a3b-q4 --model qwen3-30b-a3b-q4.gguf
```

### 1.3 Start Servers (systemd services recommended)

**Fast (Port 8080)**
```bash
llama-server \
  --model qwen3-8b-q5.gguf \
  --port 8080 \
  --ctx-size 4096 \
  --threads 8 \
  --batch-size 512
```

**Balanced (Port 8081)**
```bash
llama-server \
  --model qwen3-14b-q4.gguf \
  --port 8081 \
  --ctx-size 4096 \
  --threads 8 \
  --batch-size 512
```

**Overnight (Port 8082)**
```bash
llama-server \
  --model qwen3-30b-a3b-q4.gguf \
  --port 8082 \
  --ctx-size 4096 \
  --threads 8 \
  --batch-size 512
```

**Create systemd services**:
```bash
sudo tee /etc/systemd/system/llama-fast.service << 'EOF'
[Unit]
Description=llama.cpp Fast Server (8B)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=/home/rock/models
ExecStart=/usr/local/bin/llama-server --model qwen3-8b-q5.gguf --port 8080 --ctx-size 4096
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable llama-fast
sudo systemctl start llama-fast
# Repeat for balanced and overnight
```

---

## Step 2: Configure OpenClaw

### 2.1 Copy Config
```bash
mkdir -p ~/.openclaw/config
cp /home/rock/.openclaw/workspace/advanced-swarm-pack/configs/local-llama-profiles.yaml ~/.openclaw/config/
```

### 2.2 Verify Config
```bash
cat ~/.openclaw/config/local-llama-profiles.yaml
# Ensure endpoints match your server IPs/ports
```

---

## Step 3: Test Local Runner

```bash
cd /home/rock/.openclaw/workspace/advanced-swarm-pack/skills/skill-local-llama-runner-v1

# Health check test
python3 -c "
from lib.llama_runner import LocalLlamaRunner
runner = LocalLlamaRunner(profile='fast')
health = runner.health_check()
print('Health:', health)
"

# Completion test (requires running server)
python3 -c "
from lib.llama_runner import LocalLlamaRunner
runner = LocalLlamaRunner(profile='fast')
if runner.is_healthy():
    result = runner.complete('Hello world', max_tokens=50)
    print('Response:', result.text[:100])
    print('Tokens:', result.completion_tokens)
else:
    print('Server not healthy - check llama.cpp')
"
```

---

## Step 4: Enable Overnight Batch

### 4.1 Add to HEARTBEAT.md
```markdown
## Overnight Batch Check (2 AM EDT)
If time is 02:00-02:30:
1. Run: python3 -c "from skill_overnight_batch_engine import BatchEngine; BatchEngine().run_batch()"
2. Update memory/overnight-state.json
```

### 4.2 Or Set Up Cron
```bash
# Add to crontab
crontab -e

# Add line:
0 2 * * * cd /home/rock/.openclaw/workspace/advanced-swarm-pack && python3 -c "from skills.skill_overnight_batch_engine.lib.batch_engine import BatchEngine; BatchEngine().run_batch()" >> /var/log/overnight-batch.log 2>&1
```

---

## Step 5: Migrate Existing Skills

### 5.1 Newsletter Processor
Edit `skills/skill-newsletter-processor/lib/newsletter_processor.py`:
```python
from skill_local_llama_runner import LocalLlamaRunner
from skill_structured_output_guardian import OutputGuardian

# Use overnight profile for digest generation
runner = LocalLlamaRunner(profile="overnight")
```

### 5.2 Idea Tracker
Edit `skills/skill-idea-tracker/lib/idea_tracker.py`:
```python
# Use balanced profile for deduplication and tagging
runner = LocalLlamaRunner(profile="balanced")
```

### 5.3 Price Tracker
Edit `skills/price_tracker_v1/price_tracker_v1.py`:
```python
# Use fast profile for deal explanations
runner = LocalLlamaRunner(profile="fast")
```

---

## Step 6: Monitor & Validate

### 6.1 Check Logs
```bash
tail -f ~/.openclaw/logs/local-llama/completions_$(date +%Y-%m-%d).jsonl
tail -f ~/.openclaw/logs/costs/usage_$(date +%Y-%m).jsonl
```

### 6.2 Morning Digest Location
```bash
cat ~/.local_swarm/morning_digests/digest_$(date +%Y-%m-%d).txt
```

### 6.3 Verify Cost Tracking
```python
from skill_resource_awareness import CostTracker
tracker = CostTracker()
print(tracker.get_local_savings_report())
```

---

## Troubleshooting

### Server Not Responding
```bash
# Check if servers are running
curl http://rock-5c:8080/health
curl http://rock-5c:8081/health
curl http://rock-5c:8082/health

# Restart services
sudo systemctl restart llama-fast
sudo systemctl restart llama-balanced
sudo systemctl restart llama-overnight
```

### Out of Memory
```bash
# Check memory
free -h

# If OOM, adjust model context sizes or run fewer servers
```

### Port Conflicts
```bash
# Check what's using ports
sudo lsof -i :8080
sudo lsof -i :8081
sudo lsof -i :8082
```

---

## Success Metrics

After 1 week of operation, verify:

| Metric | Target |
|--------|--------|
| Local model health checks | >95% pass |
| Batch jobs completed | >90% success |
| Cloud tokens avoided | >10,000/day |
| Estimated savings | >$20/week |
| Avg local confidence | >0.70 |
| Escalation rate | <15% |

---

## Rollback Plan

If issues occur:

1. Stop llama.cpp servers: `sudo systemctl stop llama-*`
2. Disable batch jobs: Comment out cron/heartbeat entries
3. Fallback to cloud: Skills auto-fallback if local fails
4. Review logs: Check `~/.openclaw/logs/local-llama/`

---

**Estimated Deployment Time**: 1-2 hours  
**Estimated Monthly Savings**: $60-100
