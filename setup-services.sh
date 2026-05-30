#!/bin/bash
# Setup systemd services for llama.cpp

set -e

LLAMA_BIN="/home/rock/llama.cpp/build/bin/llama-server"
MODEL_DIR="/home/rock/models"

echo "=== Setting up llama.cpp systemd services ==="
echo ""

# Verify binary exists
if [ ! -f "$LLAMA_BIN" ]; then
    echo "❌ llama-server not found at $LLAMA_BIN"
    echo "Run build first: cd /home/rock/llama.cpp && cmake -B build && cmake --build build"
    exit 1
fi

echo "✅ llama-server binary found"

# Check for models
echo ""
echo "Model directory: $MODEL_DIR"
ls -lh "$MODEL_DIR"/*.gguf 2>/dev/null | awk '{print "  " $9, "(" $5 ")"}' || echo "  (no models yet)"
echo ""

# Create services
echo "Creating systemd services..."

# Fast service (8080)
FAST_MODEL=$(ls $MODEL_DIR/*7*.{gguf,GGUF} 2>/dev/null | head -1 || echo "fast-model.gguf")
sudo tee /etc/systemd/system/llama-fast.service > /dev/null << EOF
[Unit]
Description=llama.cpp Fast Server (7B)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=$MODEL_DIR
Environment="PATH=/usr/bin:/bin"
ExecStart=$LLAMA_BIN \
    --model $FAST_MODEL \
    --port 8080 \
    --ctx-size 4096 \
    --threads 6 \
    --batch-size 512
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Balanced service (8081)
BAL_MODEL=$(ls $MODEL_DIR/*14*.{gguf,GGUF} 2>/dev/null | head -1 || echo "balanced-model.gguf")
sudo tee /etc/systemd/system/llama-balanced.service > /dev/null << EOF
[Unit]
Description=llama.cpp Balanced Server (14B)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=$MODEL_DIR
Environment="PATH=/usr/bin:/bin"
ExecStart=$LLAMA_BIN \
    --model $BAL_MODEL \
    --port 8081 \
    --ctx-size 4096 \
    --threads 6 \
    --batch-size 512
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Overnight service (8082)
OVER_MODEL=$(ls $MODEL_DIR/*30* $MODEL_DIR/*32*.{gguf,GGUF} 2>/dev/null | head -1 || echo "overnight-model.gguf")
sudo tee /etc/systemd/system/llama-overnight.service > /dev/null << EOF
[Unit]
Description=llama.cpp Overnight Server (30B+)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=$MODEL_DIR
Environment="PATH=/usr/bin:/bin"
ExecStart=$LLAMA_BIN \
    --model $OVER_MODEL \
    --port 8082 \
    --ctx-size 4096 \
    --threads 6 \
    --batch-size 512
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Services created"
echo ""

# Enable and reload
sudo systemctl daemon-reload
sudo systemctl enable llama-fast llama-balanced llama-overnight
echo "✅ Services enabled"

echo ""
echo "=== Next Steps ==="
echo ""
echo "1. Ensure models are downloaded:"
echo "   bash download-models-fixed.sh"
echo ""
echo "2. Start services:"
echo "   sudo systemctl start llama-fast"
echo "   sudo systemctl start llama-balanced"
echo "   sudo systemctl start llama-overnight"
echo ""
echo "3. Test:"
echo "   curl http://localhost:8080/health"
echo ""
echo "4. Install config:"
echo "   cp /home/rock/.openclaw/workspace/advanced-swarm-pack/configs/local-llama-profiles.yaml ~/.openclaw/config/"
