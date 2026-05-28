#!/usr/bin/env python3
"""
Guided tours through codebase knowledge graphs.

Author: RockClaw
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional
from .codebase_analyzer import CodebaseAnalyzer


def guided_tour(
    analyzer: CodebaseAnalyzer,
    topic: str,
    max_steps: int = 5
) -> List[Dict[str, Any]]:
    """
    Generate a guided tour explaining a codebase topic.
    
    Args:
        analyzer: Initialized CodebaseAnalyzer
        topic: Topic to explore (e.g., "How does authentication work?")
        max_steps: Maximum tour stops
    
    Returns:
        List of tour steps
    """
    if not analyzer._graph:
        return [{"error": "No graph loaded"}]
    
    # Extract relevant keywords
    keywords = [w.lower() for w in topic.split()
                if len(w) > 3 and w.lower() not in ['does', 'work', 'this', 'that', 'how']]
    
    # Find entry points
    entry_points = []
    for node in analyzer._graph.nodes.values():
        if node.name:
            for kw in keywords:
                if kw in node.name.lower():
                    entry_points.append(node)
                    break
    
    if not entry_points:
        return [{"error": f"No entry points found for topic: {topic}"}]
    
    # Build tour from entry points
    tour = []
    visited = set()
    
    for i, entry in enumerate(entry_points[:max_steps]):
        if entry.id in visited:
            continue
        visited.add(entry.id)
        
        # Build description based on node type
        if entry.type == "function":
            description = f"Function '{entry.name}' implements {topic.lower()} logic"
        elif entry.type == "class":
            description = f"Class '{entry.name}' defines the main data structure"
        elif entry.type == "module":
            description = f"Module '{entry.name}' contains the implementation"
        else:
            description = f"{entry.type.title()} '{entry.name}'"
        
        # Get code snippet if possible
        snippet = ""
        if entry.file_path and entry.line_no:
            try:
                with open(entry.file_path) as f:
                    lines = f.readlines()
                    start = max(0, entry.line_no - 2)
                    end = min(len(lines), entry.line_no + 3)
                    snippet = ''.join(lines[start:end])
            except:
                pass
        
        tour.append({
            "number": i + 1,
            "concept": description,
            "location": f"{entry.file_path}:{entry.line_no}" if entry.file_path else "unknown",
            "file": entry.file_path,
            "line": entry.line_no,
            "code_snippet": snippet.strip(),
            "node_type": entry.type
        })
    
    return tour


def explain_architecture(
    analyzer: CodebaseAnalyzer
) -> Dict[str, Any]:
    """
    Explain overall architecture of codebase.
    """
    if not analyzer._graph:
        return {"error": "No graph loaded"}]
    
    # Find entry points (nodes with no incoming edges but outgoing)
    incoming = set(edge.target for edge in analyzer._graph.edges)
    outgoing = set(edge.source for edge in analyzer._graph.edges)
    
    entry_points = list(outgoing - incoming)
    
    # Analyze module structure
    modules = [n for n in analyzer._graph.nodes.values() if n.type == "module"]
    
    # Find external dependencies
    externals = set()
    for edge in analyzer._graph.edges:
        if edge.target.startswith("external:"):
            externals.add(edge.target[9:])  # Remove 'external:' prefix
    
    return {
        "entry_points": [analyzer._graph.nodes.get(e, {}).get("name", e) for e in entry_points[:5]],
        "total_modules": len(modules),
        "external_dependencies": sorted(list(externals))[:20],
        "architecture_notes": ""
            f"The codebase has {len(modules)} modules with "
            f"{len(externals)} external dependencies. "
            f"Entry points are located in: {', '.join([analyzer._graph.nodes.get(e, {}).get('name', e) for e in entry_points[:3]])}"
    }


def onboarding_guide(
    analyzer: CodebaseAnalyzer,
    role: str = "developer"
) -> List[Dict[str, Any]]:
    """
    Generate onboarding guide for new team members.
    """
    if not analyzer._graph:
        return [{"error": "No graph loaded"}]
    
    guide = []
    
    # Start with architecture overview
    arch = explain_architecture(analyzer)
    guide.append({
        "section": "Architecture Overview",
        "content": arch["architecture_notes"],
        "priority": "must_read"
    })
    
    # Find main configuration files
    config_files = [n for n in analyzer._graph.nodes.values()
                    if n.type == "module" and "config" in n.name.lower()]
    
    if config_files:
        guide.append({
            "section": "Configuration",
            "content": f"Configuration defined in: {', '.join([c.name for c in config_files[:3]])}",
            "priority": "should_read"
        })
    
    # Find test files
    test_files = [n for n in analyzer._graph.nodes.values()
                  if n.type == "module" and any(x in n.name.lower() for x in ["test_", "_test", "spec"])]
    
    guide.append({
        "section": "Testing",
        "content": f"Tests located in: {len(test_files)} test files",
        "priority": "should_read"
    })
    
    return guide


if __name__ == "__main__":
    print("Tours module ready. Available tours:")
    print("  - guided_tour(analyzer, topic)")
    print("  - explain_architecture(analyzer)")
    print("  - onboarding_guide(analyzer, role)")
