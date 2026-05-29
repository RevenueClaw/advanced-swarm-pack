#!/bin/bash
# Install all Advanced Swarm Pack skills
# Version: 1.3.1 (Fixed to include v1 skills)

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$(dirname "$SCRIPT_DIR")/skills"
OPENCLAW_SKILLS_DIR="${HOME}/.openclaw/workspace/skills"

echo "=========================================="
echo "RevenueClaw Advanced Swarm Pack v1.3.1"
echo "Installing skills..."
echo "=========================================="
echo ""
echo "Source: $SKILLS_DIR"
echo "Target: $OPENCLAW_SKILLS_DIR"
echo ""

# Create target directory if needed
mkdir -p "$OPENCLAW_SKILLS_DIR"

# Check if OpenClaw workspace exists
if [ ! -d "$OPENCLAW_SKILLS_DIR" ]; then
    echo "Error: OpenClaw workspace not found at $OPENCLAW_SKILLS_DIR"
    echo "Please ensure OpenClaw is installed and initialized."
    exit 1
fi

# Add to PYTHONPATH
PROFILE_FILE=""
if [[ "$SHELL" == *"bash"* ]]; then
    PROFILE_FILE="$HOME/.bashrc"
elif [[ "$SHELL" == *"zsh"* ]]; then
    PROFILE_FILE="$HOME/.zshrc"
fi

if [[ -n "$PROFILE_FILE" && ! -f "$PROFILE_FILE" ]] || ! grep -q "OPENCLAW_SKILLS_PATH" "$PROFILE_FILE" 2>/dev/null; then
    echo "Adding SKILL_PATH to $PROFILE_FILE..."
    echo "export PYTHONPATH=\"\${PYTHONPATH}:$SKILLS_DIR\"" >> "$PROFILE_FILE"
    echo "Please run: source $PROFILE_FILE"
fi

echo "Installing skills..."
echo ""

# Track counts
INSTALLED=0
SKIPPED=0

# Install skill-* prefixed skills
for skill_dir in "$SKILLS_DIR"/skill-*; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        target_link="$OPENCLAW_SKILLS_DIR/$skill_name"
        
        if [ -L "$target_link" ]; then
            echo "  - $skill_name (already linked)"
            SKIPPED=$((SKIPPED + 1))
        else
            echo "  - $skill_name"
            ln -sf "$skill_dir" "$target_link"
            INSTALLED=$((INSTALLED + 1))
        fi
        
        # Create necessary directories
        mkdir -p "$skill_dir/registry" 2>/dev/null || true
        mkdir -p "$skill_dir/preferences" 2>/dev/null || true
        mkdir -p "$skill_dir/shadow_results" 2>/dev/null || true
        mkdir -p "$skill_dir/cost_logs/daily" 2>/dev/null || true
        mkdir -p "$skill_dir/debate_logs" 2>/dev/null || true
        
        # Make CLI scripts executable
        if [ -f "$skill_dir/cli.py" ]; then
            chmod +x "$skill_dir/cli.py"
        fi
    fi
done

# Install v1 suffixed skills (amazon_creators_api_v1, etc.)
echo ""
echo "Installing e-commerce skills..."
for skill_dir in "$SKILLS_DIR"/*_v1; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        target_link="$OPENCLAW_SKILLS_DIR/$skill_name"
        
        if [ -L "$target_link" ]; then
            echo "  - $skill_name (already linked)"
            SKIPPED=$((SKIPPED + 1))
        else
            echo "  - $skill_name"
            ln -sf "$skill_dir" "$target_link"
            INSTALLED=$((INSTALLED + 1))
        fi
        
        # Create subdirectories
        mkdir -p "$skill_dir/backups" 2>/dev/null || true
        mkdir -p "$skill_dir/.backups" 2>/dev/null || true
    fi
done

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo "  New: $INSTALLED"
echo "  Skipped: $SKIPPED"
echo "  Total: $((INSTALLED + SKIPPED))"
echo ""
echo "Next steps:"
if [[ -n "$PROFILE_FILE" ]]; then
    echo "  1. Source your shell profile: source $PROFILE_FILE"
fi
echo "  2. Verify: ls ~/.openclaw/workspace/skills/ | wc -l"
echo "  3. Test: python3 -c 'from price_tracker_v1 import PriceTracker; print(\"OK\")'"
echo ""
