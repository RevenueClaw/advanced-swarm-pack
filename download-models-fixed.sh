#!/bin/bash
# Download models from PUBLIC HuggingFace repos (no auth required)

set -e

MODEL_DIR="/home/rock/models"
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

echo "=== Downloading Qwen2.5 Models (Public) ==="
echo "Using huggingface-cli or wget fallback..."
echo ""

# Try huggingface-cli first, fallback to wget
get_model() {
    local repo=$1
    local file=$2
    local target=$3
    
    echo "Downloading: $file -> $target"
    
    # Try huggingface-cli if available
    if command -v huggingface-cli &> /dev/null; then
        huggingface-cli download "$repo" "$file" --local-dir . --local-dir-use-symlinks False 2>/dev/null || true
        if [ -f "$file" ]; then
            mv "$file" "$target"
            echo "✅ Downloaded via huggingface-cli"
            return 0
        fi
    fi
    
    # Fallback to direct HF URL
    local url="https://huggingface.co/$repo/resolve/main/$file"
    wget --progress=bar:force -O "$target" "$url" 2>&1 | tail -5
    
    if [ -s "$target" ] && [ $(stat -c%s "$target") -gt 1000000 ]; then
        echo "✅ Downloaded: $(du -h "$target" | cut -f1)"
        return 0
    else
        echo "❌ Download failed or file too small"
        rm -f "$target"
        return 1
    fi
}

# Qwen2.5 models (Apache 2.0, public)
get_model "Qwen/Qwen2.5-7B-Instruct-GGUF" "qwen2.5-7b-instruct-q5_k_m.gguf" "fast-model.gguf" &
PID1=$!

try_model1() {
    get_model "Qwen/Qwen2.5-7B-Instruct-GGUF" "qwen2.5-7b-instruct-q5_k_m.gguf" "fast-model.gguf"
}

wait $PID1 2>/dev/null

get_model "Qwen/Qwen2.5-14B-Instruct-GGUF" "qwen2.5-14b-instruct-q4_k_m.gguf" "balanced-model.gguf" &
PID2=$!
wait $PID2 2>/dev/null

get_model "Qwen/Qwen2.5-32B-Instruct-GGUF" "qwen2.5-32b-instruct-q4_k_m.gguf" "overnight-model.gguf" &
PID3=$!
wait $PID3 2>/dev/null

echo ""
echo "=== Download Summary ==="
ls -lh *.gguf 2>/dev/null | awk '{print $9, $5}' || echo "No models found"
echo ""
echo "Next: Create systemd services to run these models"
