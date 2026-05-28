# Codebase Understanding (v1)

Deep codebase comprehension using local-first knowledge graphs and multi-agent analysis.

## Philosophy

**Understand, Don't Guess:** Before modifying any code, understand its structure, dependencies, and impact.

This skill provides:
- **Knowledge Graph Generation**: Maps code relationships (imports, calls, inheritance)
- **Impact Analysis**: "What breaks if I change X?"
- **Guided Exploration**: Navigate from high-level concepts to implementation details
- **Context for Planning**: Feed structured code insights into Architect-First plans

## Core Components

### CodebaseAnalyzer

```python
from lib.codebase_analyzer import CodebaseAnalyzer

analyzer = CodebaseAnalyzer()

# Analyze a repository
graph = analyzer.analyze_repository(
    repo_path="/path/to/project",
    languages=["python", "javascript"],  # Auto-detects if omitted
    depth="deep"  # quick, standard, deep
)

# Query the knowledge graph
impacts = analyzer.impact_analysis("class PlanReviewer")
upstreams = analyzer.upstream_dependencies("price_tracker_v1/main.py")
```

### Supported Languages

- **Fully Supported**: Python, JavaScript/TypeScript
- **Partially Supported**: Go, Rust, Java
- **Extensible**: Parser plugins for additional languages

### Knowledge Graph Nodes

| Type | Properties | Relations |
|------|-----------|-----------|
| **Module** | Path, size, language | imports, exports_to |
| **Function** | Name, signature, complexity | calls, called_by, in_module |
| **Class** | Name, inheritance, docstring | inherits_from, methods, uses |
| **Variable** | Name, type (inferred), mutable | reads, writes |
| **Configuration** | Key, type, default | defined_in, referenced_by |
| **External** | Package, version, usage_count | imported_by |

### Analysis Depth Levels

| Level | Time | Output |
|-------|------|--------|
| **quick** | 30s-2m | Module-level relationships only |
| **standard** | 2-5m | Functions, classes, basic call graph |
| **deep** | 5-15m | Full static analysis, complexity metrics, data flow |

For ongoing projects, use `incremental=True` to update only changed files.

## Query Interface

### Impact Analysis

```python
# "What breaks if I change this?"
from lib.queries import impact_analysis

result = impact_analysis(
    analyzer,
    target="DatabaseHandler.commit()",
    change_type="signature_add_required_param"
)

print(f"Files to modify: {len(result['affected_files'])}")
print(f"Tests to update: {len(result['affected_tests'])}")
```

### Feature Mapping

```python
# "Where is feature X implemented?"
from lib.queries import find_feature

result = find_feature(
    analyzer,
    description="price alert notification system"
)

print(f"Entry point: {result['entry_point']}")
print(f"Key modules: {result['modules']}")
print(f"Configuration: {result['config_keys']}")
```

### Guided Tour

```python
# Interactive guided exploration
from lib.tours import guided_tour

tour = guided_tour(
    analyzer,
    topic="How does the premortem integration work?"
)

for step in tour:
    print(f"{step['number']}. {step['concept']}")
    print(f"   Location: {step['file']}:{step['line']}")
    print(f"   Read this: {step['code_snippet']}")
    print()
```

## Integration with Other Skills

### Architect-First Planning

When creating plans for code changes:

```python
# In skill-architect-first/lib/plan_reviewer.py:
from skill_codebase_understander_v1.lib.integration import CodebaseContext

def review_code_plan(self, plan):
    # Get codebase context
    context = CodebaseContext.from_plan(plan)
    
    # Enhance plan with:
    plan['affected_files'] = context.get_affected_files()
    plan['dependency_depth'] = context.calculate_dependency_depth()
    plan['test_coverage_gaps'] = context.find_untested_dependencies()
    
    # Add to 5D scoring:
    if plan['dependency_depth'] > 3:
        completeness_score -= 10  # Knock for complexity
```

### Estimation Engine

More accurate time estimates based on actual code complexity:

```python
from lib.integration import EstimationHelper

helper = EstimationHelper(analyzer)
estimate = helper.estimate_change(
    change="Refactor PlanReviewer scoring",
    impact_files=["plan_reviewer.py", "scoring_utils.py"]
)

# Returns: {
#   "estimated_hours": 8.5,
#   "complexity_factors": ["circular_dependency", "test_coverage_gap"],
#   "recommended_approach": "extract_interface_first"
# }
```

### Consensus/Debate

Include codebase complexity in decision:

```python
# Adds to debate context:
"Codebase analysis shows:
- This change affects 12 files across 4 modules
- 2 untested dependencies identified
- Recommended prerequisite: add tests for Foo.bar()"
```

## Local-First Architecture

**No code leaves your machine.** All analysis happens:
1. Using local AST parsers (tree-sitter, jedi, ts-parser)
2. With local graph database (NetworkX or optional Neo4j)
3. Cached locally in `~/.openclaw/codebase_graphs/`

### Optional External Dependencies

- **Neo4j**: For very large repos (>100k files), local Neo4j Community Edition
- **tree-sitter grammars**: Auto-downloaded on first use per language

## Storage

**Location**: `~/.openclaw/workspace/skills/skill-codebase-understander-v1/graphs/`

**Structure**:
```
graphs/
  {repo_hash}/
    knowledge_graph.json       # Full graph export
    metadata.json              # Analysis timestamp, versions
    incremental_cache/         # Changed file tracking
```

**Format**: NetworkX JSON + custom annotations (GEXF compatible)

## Refresh & Cache Management

```python
from lib.cache import CodebaseCache

cache = CodebaseCache()

# Check staleness
if cache.is_stale(repo_path, max_age_hours=24):
    analyzer.analyze_repository(repo_path, incremental=True)

# Force full re-analysis
analyzer.analyze_repository(repo_path, incremental=False, depth="deep")

# Cleanup old graphs
cache.cleanup_older_than(days=30)
```

## Files

- `lib/codebase_analyzer.py` (~800 lines) - Core analysis engine
- `lib/parsers/` - Language-specific AST parsers
- `lib/queries.py` - Query patterns and implementations
- `lib/tours.py` - Guided exploration generation
- `lib/integration.py` - Connectors for Architect-First, Estimation Engine
- `lib/cache.py` - Graph persistence and incremental updates
- `lib/docker_analyzer.py` - Docker/infrastructure analysis & Safe Edit Protocol

## Docker & Infrastructure Analysis

For complex multi-container projects (like ChipRadar):

```python
from lib.docker_analyzer import DockerAnalyzer, SafeEditProtocol

# Analyze Docker setup
docker = DockerAnalyzer("/path/to/chipradar")
summary = docker.get_infrastructure_summary()
volume_risks = docker.get_volume_risks()
startup_order = docker.get_container_startup_order()

# Find risky import-time code
python_files = list(Path("/path/to/chipradar").rglob("*.py"))
import_risks = docker.find_import_time_risks(python_files)

# Safe editing with automatic backup
editor = SafeEditProtocol("/path/to/chipradar", "/path/to/backups")
result = editor.safe_edit(
    file_path="docker-compose.yml",
    content=new_compose_content,
    verify_syntax=lambda c: yaml.safe_load(c)  # Validate YAML
)

if result['success']:
    print(f"✅ Safe edit complete. Backup: {result['backup_id']}")
else:
    print(f"❌ Edit failed: {result['error']}")
    # Rollback if needed
    editor.rollback("docker-compose.yml", result['backup_id'])
```

### Safe Editing Protocol (CRITICAL)

**Never lose data. Never leave containers broken.**

The SafeEditProtocol guarantees:

1. **Atomic Writes**: `temp.write() → verify → rename(temp, target)`
2. **Timestamped Backups**: Every edit backed up with MD5 hash
3. **Syntax Verification**: Validate before writing
4. **Integrity Check**: Compare written content with intended
5. **Rollback Plan**: One-call restore to previous state

**Docker-Specific Safeguards:**
- Never append via SCP (use atomic rsync or cat > file)
- Check container health before and after
- Verify volume mounts post-edit
- Test docker-compose syntax before applying

### Infrastructure Risks Detected

| Risk Type | Detection | Example |
|-----------|-----------|---------|
| **Volume Mount** | Database in bind mount | `volumes: ['./data:/var/lib/postgres']` |
| **Import Side Effect** | Connection on import | `db_client = MongoClient()` at module level |
| **Startup Order** | Circular dependency | Service A depends on B, B depends on A |
| **Secret Exposure** | Hardcoded credentials | `ENV API_KEY=secret123` in Dockerfile |
| **Resource Leak** | Unbounded logs | Log volume without rotation config |

## Quick Reference

```python
# One-shot analysis
from lib.codebase_analyzer import CodebaseAnalyzer

analyzer = CodebaseAnalyzer()
graph = analyzer.analyze_repository("/path/to/repo")

# Query impact
impacts = analyzer.impact_analysis("PlanReviewer.review")

# Get for planning
from lib.integration import CodebaseContext
context = CodebaseContext.from_files(["file1.py", "file2.py"])
complexity = context.get_overall_complexity()
```

## Installation Notes

### Dependencies

```bash
# Auto-installed on first use
pip install tree-sitter tree-sitter-python tree-sitter-javascript
pip install networkx jedi

# Optional for large repos
pip install neo4j
```

### First Run Setup

```python
from lib.codebase_analyzer import setup
setup.initialize_parser_library()  # Downloads tree-sitter grammars
```
