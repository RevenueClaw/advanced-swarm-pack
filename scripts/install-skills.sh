#!/bin/bash
# Install all Advanced Swarm Pack skills

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SKILLS_DIR="$(dirname "$SCRIPT_DIR")/skills"

echo "Installing RevenueClaw Advanced Swarm Pack skills..."
echo "Skills directory: $SKILLS_DIR"
echo ""

# Check if OpenClaw is installed
if ! command -v openclaw &> /dev/null; then
    echo "Error: OpenClaw not found. Please install OpenClaw first."
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
    echo "export PYTHONPATH=\"\${PYTHONPATH}:$SKILLS_DIR/skill-versioning/lib:$SKILLS_DIR/skill-preference-learning/lib:$SKILLS_DIR/skill-consensus/lib:$SKILLS_DIR/skill-resource-awareness/lib\"" >> "$PROFILE_FILE"
    echo "Please run: source $PROFILE_FILE"
fi

echo "Installing skills..."

for skill_dir in "$SKILLS_DIR"/skill-*; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        echo "  - Installing $skill_name..."
        
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
        
        echo "    ✓ $skill_name installed"
    fi
done

echo ""
echo "All skills installed!"
echo ""
echo "Next steps:"
echo "  1. Source your shell profile: source $PROFILE_FILE"
echo "  2. Test: python -c 'from version_manager import SkillVersionManager; print(\"OK\")'"
echo "  3. Copy config: cp configs/swarm-example.yaml ~/.openclaw/swarm-config.yaml"
