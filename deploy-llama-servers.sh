#!/bin/bash
# Deploy llama.cpp servers for v1.4.0
# Run on Rock 5B

set -e

echo "=== v1.4.0 Llama.cpp Deployment ==="
echo "Started: $(date)"

# Configuration
MODEL_DIR="/home/rock/models"
LLAMA_CPP_DIR="/home/rock/llama.cpp"

mkdir -p "$MODEL_DIR"
cd /home/rock

# Step 1: Clone/Update llama.cpp
echo "[1/6] Setting up llama.cpp..."
if [ ! -d "$LLAMA_CPP_DIR" ]; then
    git clone https://github.com/ggerganov/llama.cpp.git
fi
cd "$LLAMA_CPP_DIR"
git pull

# Step 2: Build with ARM optimizations
echo "[2/6] Building llama.cpp for ARM64..."
if [ ! -f build/bin/llama-server ]; then
    cmake -B build -DCMAKE_BUILD_TYPE=Release \
        -DLLAMA_NATIVE=ON \
        -DLLAMA_OPENMP=ON
    cmake --build build --parallel $(nproc)
fi

echo "Build complete!"

# Step 3: Download models (using HuggingFace CLI if available, otherwise wget)
echo "[3/6] Checking models..."
cd "$MODEL_DIR"

# Model URLs from HuggingFace
FAST_MODEL="https://huggingface.co/Revmorgan/qwen3-8b-q5/resolve/main/qwen3-8b-q5.gguf"
BALANCED_MODEL="https://huggingface.co/Revmorgan/qwen3-14b-q4/resolve/main/qwen3-14b-q4.gguf"  
OVERNIGHT_MODEL="https://huggingface.co/Revmorgan/qwen3-30b-a3b-q4/resolve/main/qwen3-30b-a3b-q4.gguf"

download_model() {
    local url=$1
    local filename=$2
    if [ ! -f "$filename" ]; then
        echo "Downloading $filename..."
        wget --progress=bar:force "$url" -O "$filename" || \
        curl -L -o "$filename" "$url"
    else
        echo "$filename already exists"
    fi
}

# Note: These models are large (8B=~6GB, 14B=~8GB, 30B=~18GB)
# Download may take time

download_model "$FAST_MODEL" "qwen3-8b-q5.gguf"
download_model "$BALANCED_MODEL" "qwen3-14b-q4.gguf"
download_model "$OVERNIGHT_MODEL" "qwen3-30b-a3b-q4.gguf"

echo "Models ready!"

# Step 4: Create systemd services
echo "[4/6] Creating systemd services..."

sudo tee /etc/systemd/system/llama-fast.service > /dev/null << 'EOF'
[Unit]
Description=Llama.cpp Fast Server (8B)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=/home/rock/models
Environment="PATH=/usr/bin:/bin"
ExecStart=/home/rock/llama.cpp/build/bin/llama-server \
    --model qwen3-8b-q5.gguf \
    --port 8080 \
    --ctx-size 4096 \
    --threads 6 \
    --batch-size 512
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/llama-balanced.service > /dev/null << 'EOF'
[Unit]
Description=Llama.cpp Balanced Server (14B)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=/home/rock/models
Environment="PATH=/usr/bin:/bin"
ExecStart=/home/rock/llama.cpp/build/bin/llama-server \
    --model qwen3-14b-q4.gguf \
    --port 8081 \
    --ctx-size 4096 \
    --threads 6 \
    --batch-size 512
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/llama-overnight.service > /dev/null << 'EOF'
[Unit]
Description=Llama.cpp Overnight Server (30B)
After=network.target

[Service]
Type=simple
User=rock
WorkingDirectory=/home/rock/models
Environment="PATH=/usr/bin:/bin"
ExecStart=/home/rock/llama.cpp/build/bin/llama-server \
    --model qwen3-30b-a3b-q4.gguf \
    --port 8082 \
    --ctx-size 8192 \
    --threads 6 \
    --batch-size 512
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Step 5: Enable and start services
echo "[5/6] Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable llama-fast llama-balanced llama-overnight

echo "[6/6] Starting services..."
sudo systemctl start llama-fast || echo "Fast server failed to start"
sudo systemctl start llama-balanced || echo "Balanced server failed to start"
sudo systemctl start llama-overnight || echo "Overnight server failed to start"

# Wait for startup
sleep 5

# Check status
echo ""
echo "=== Deployment Status ==="
echo "Fast (8080): $(curl -s http://localhost:8080/health 2>/dev/null | grep -o 'status":"[^"]*' || echo 'NOT RUNNING')"
echo "Balanced (8081): $(curl -s http://localhost:8081/health 2>/dev/null | grep -o 'status":"[^"]*' || echo 'NOT RUNNING')"
echo "Overnight (8082): $(curl -s http://localhost:8082/health 2>/dev/null | grep -o 'status":"[^"]*' || echo 'NOT RUNNING')"

echo ""
echo "=== Service Status ==="
sudo systemctl status llama-fast --no-pager -l || true
echo "---"
sudo systemctl status llama-balanced --no-pager -l || true
echo "---"
sudo systemctl status llama-overnight --no-pager -l || true

echo ""
echo "=== Deployment Complete ==="
echo "Models location: $MODEL_DIR"
echo "Logs: journalctl -u llama-fast -f"
echo "Test: curl http://localhost:8080/health"
