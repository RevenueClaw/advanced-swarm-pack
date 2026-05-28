# Setting Up Understand-Anything Integration

## Overview

This skill includes a bridge to the [Understand-Anything](https://github.com/Lum1104/Understand-Anything) project for enhanced codebase analysis.

## Option 1: Standalone Mode (Default)

By default, skill-codebase-understander-v1 uses its own built-in analyzer:
- Regex-based parsing (no external dependencies)
- NetworkX for graph storage
- Local-first: No data leaves your machine

This works immediately with no setup.

## Option 2: Enhanced Mode with Understand-Anything

For more sophisticated analysis:

### Installation

```bash
# Clone Understand-Anything
git clone https://github.com/Lum1104/Understand-Anything.git ~/projects/understand-anything
cd ~/projects/understand-anything

# Install dependencies
pip install -r requirements.txt

# Build and run
cd backend && make run
```

### Configuration

Create `~/.openclaw/credentials/understand-anything.env`:

```
UNDERSTAND_ANYTHING_URL=http://localhost:9369
UNDERSTAND_ANYTHING_API_KEY=your-key-if-required
```

### Enable Enhanced Mode

```python
from skill_codebase_understander_v1.lib.enhanced import EnhancedAnalyzer

analyzer = EnhancedAnalyzer(use_understand_anything=True)
graph = analyzer.analyze_repository("/path/to/repo")
```

## Comparison

| Feature | Standalone | +Understand-Anything |
|---------|-----------|---------------------|
| Setup | None | Requires installation |
| Speed | Fast | Slower (deep analysis) |
| Accuracy | Good | Excellent |
| AST parsing | Regex-based | Full tree-sitter |
| Natural language | Limited | Full NL queries |
| Multi-agent | No | Yes |
| Local-only | Yes | Yes (self-hosted) |

## Recommendation

- **Quick tasks**: Use standalone mode
- **Complex refactoring**: Enable Understand-Anything
- **CI/CD pipelines**: Use standalone mode (faster)

## Troubleshooting

### "Connection refused" to Understand-Anything
- Check service is running: `curl http://localhost:9369/health`
- Verify port configuration in credentials file

### Parser errors
- Ensure tree-sitter grammars are installed
- Check language support in understand-anything
