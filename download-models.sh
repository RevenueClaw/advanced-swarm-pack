#!/bin/bash
# Download models from public sources

set -e

MODEL_DIR="/home/rock/models"
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

echo "=== Downloading Models for v1.4.0 ==="
echo "Target directory: $MODEL_DIR"
echo ""

# Use HuggingFace CLI with default models
# These are public models that should work

# Option 1: Qwen2.5 models (public, Apache 2.0)
FAST_MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf"
BALANCED_MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q4_k_m.gguf"
OVERNIGHT_MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF/resolve/main/qwen2.5-32b-instruct-q4_k_m.gguf"

echo "[1/3] Downloading fast model (Qwen2.5-7B Q5)..."
if [ ! -f "fast-model.gguf" ]; then
    wget --progress=bar:force "$FAST_MODEL_URL" -O fast-model.gguf 2>/dev/null || \
    curl -L -o fast-model.gguf "$FAST_MODEL_URL"
    echo "Downloaded: fast-model.gguf ($(du -h fast-model.gguf | cut -f1))"
else
    echo "Already exists: fast-model.gguf"
fi

echo ""
echo "[2/3] Downloading balanced model (Qwen2.5-14B Q4)..."
if [ ! -f "balanced-model.gguf" ]; then
    wget --progress=bar:force "$BALANCED_MODEL_URL" -O balanced-model.gguf 2>/dev/null || \
    curl -L -o balanced-model.gguf "$BALANCED_MODEL_URL"
    echo "Downloaded: balanced-model.gguf ($(du -h balanced-model.gguf | cut -f1))"
else
    echo "Already exists: balanced-model.gguf"
fi

echo ""
echo "[3/3] Downloading overnight model (Qwen2.5-32B Q4)..."
if [ ! -f "overnight-model.gguf" ]; then
    wget --progress=bar:force "$OVERNIGHT_MODEL_URL" -O overnight-model.gguf 2>/dev/null || \
    curl -L -o overnight-model.gguf "$OVERNIGHT_MODEL_URL"
    echo "Downloaded: overnight-model.gguf ($(du -h overnight-model.gguf | cut -f1))"
else
    echo "Already exists: overnight-model.gguf"
fi

echo ""
echo "=== Model Download Complete ==="
ls -lh *.gguf 2>/dev/null || echo "Some models may have failed to download"
echo ""
echo "Total disk usage: $(du -sh . | cut -f1)"
