#!/bin/bash
# Complete v1.4.0 deployment - Manual steps

echo "=== v1.4.0 Deployment - Manual Completion Steps ==="
echo ""

# Check if llama.cpp built
if [ -f "/home/rock/llama.cpp/build/bin/llama-server" ]; then
    echo "✅ llama.cpp built successfully"
else
    echo "❌ llama-server not found. Build may have failed."
    exit 1
fi

# Check for models
MODEL_DIR="/home/rock/models"
mkdir -p "$MODEL_DIR"

echo ""
echo "=== Model Download ==="
echo "Models need to be downloaded manually (public sources):"
echo ""
echo "Run this command to download models:"
echo "  bash /home/rock/.openclaw/workspace/advanced-swarm-pack/download-models.sh"
echo ""
echo "Or manually download from HuggingFace:"
echo "  Qwen2.5-7B-Instruct (Q5_K_M)  -> $MODEL_DIR/fast-model.gguf"
echo "  Qwen2.5-14B-Instruct (Q4_K_M) -> $MODEL_DIR/balanced-model.gguf"  
echo "  Qwen2.5-32B-Instruct (Q4_K_M) -> $MODEL_DIR/overnight-model.gguf"
echo ""

# Check current models
echo "Current models in $MODEL_DIR:"
ls -lh "$MODEL_DIR"/*.gguf 2>/dev/null || echo "  (none found)"
echo ""

echo "=== Systemd Services ==="
echo "To create systemd services, run these commands:"
echo ""

cat << 'SYSTEMD'
# Fast server (8080)
sudo tee /etc/systemd/system/llama-fast.service << 'EOF'
[Unit]
Description=llama.cpp Fast Server (7B)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=/home/rock/models
ExecStart=/home/rock/llama.cpp/build/bin/llama-server \
    --model fast-model.gguf \
    --port 8080 \
    --ctx-size 4096 \
    --threads 6 \
    --batch-size 512
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Balanced server (8081)
sudo tee /etc/systemd/system/llama-balanced.service << 'EOF'
[Unit]
Description=llama.cpp Balanced Server (14B)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=/home/rock/models
ExecStart=/home/rock/llama.cpp/build/bin/llama-server \
    --model balanced-model.gguf \
    --port 8081 \
    --ctx-size 4096 \
    --threads 6 \
    --batch-size 512
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Overnight server (8082)
sudo tee /etc/systemd/system/llama-overnight.service << 'EOF'
[Unit]
Description=llama.cpp Overnight Server (32B)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=/home/rock/models
ExecStart=/home/rock/llama.cpp/build/bin/llama-server \
    --model overnight-model.gguf \
    --port 8082 \
    --ctx-size 4096 \
    --threads 6 \
    --batch-size 512
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable llama-fast llama-balanced llama-overnight
sudo systemctl start llama-fast llama-balanced llama-overnight
SYSTEMD

echo ""
echo "=== Testing ==="
echo "After starting services, test with:"
echo "  curl http://localhost:8080/health"
echo "  curl http://localhost:8081/health"
echo "  curl http://localhost:8082/health"
echo ""

echo "=== Config Install ==="
echo "Install the config file:"
echo "  mkdir -p ~/.openclaw/config"
echo "  cp /home/rock/.openclaw/workspace/advanced-swarm-pack/configs/local-llama-profiles.yaml ~/.openclaw/config/"
echo ""

echo "=== Test Skill ==="
echo "Test the runner:"
echo "  cd /home/rock/.openclaw/workspace/advanced-swarm-pack/skills/skill-local-llama-runner-v1"
echo "  python3 lib/llama_runner.py"
