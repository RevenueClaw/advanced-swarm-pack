#!/usr/bin/env python3
"""
Query patterns for codebase knowledge graphs.

Author: RockClaw
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional
from .codebase_analyzer import CodebaseAnalyzer, KnowledgeGraph


def impact_analysis(
    analyzer: CodebaseAnalyzer,
    target: str,
    change_type: str = "modify"
) -> Dict[str, Any]:
    """
    Analyze impact of changing a specific element.
    
    Args:
        analyzer: Initialized CodebaseAnalyzer
        target: Name or ID of element to change
        change_type: Type of change (modify, delete, signature_change)
    
    Returns:
        Impact analysis result
    """
    if not analyzer._graph:
        return {"error": "No graph loaded"}
    
    return analyzer.impact_analysis(target)


def find_feature(
    analyzer: CodebaseAnalyzer,
    description: str
) -> Dict[str, Any]:
    """
    Find code related to a feature description.
    
    This is a heuristic search - looks for keywords in docstrings,
    function names, and comments.
    
    Args:
        analyzer: Initialized CodebaseAnalyzer
        description: Natural language description of feature
    
    Returns:
        Feature location info
    """
    if not analyzer._graph:
        return {"error": "No graph loaded"}
    
    # Extract keywords
    keywords = [w.lower() for w in description.split() 
                if len(w) > 3 and w.lower() not in ['this', 'that', 'from', 'with']]
    
    results = {
        "query": description,
        "keywords": keywords,
        "entry_points": [],
        "modules": [],
        "functions": []
    }
    
    # Search for matches
    for node in analyzer._graph.nodes.values():
        if node.name:
            name_lower = node.name.lower()
            for kw in keywords:
                if kw in name_lower:
                    results["functions" if node.type == "function" else "modules"].append({
                        "name": node.name,
                        "file": node.file_path,
                        "line": node.line_no,
                        "match_score": len([k for k in keywords if k in name_lower])
                    })
    
    # Sort by match score
    results["functions"].sort(key=lambda x: x["match_score"], reverse=True)
    results["functions"] = results["functions"][:10]  # Cap results
    
    if results["functions"]:
        results["entry_points"] = [results["functions"][0]]
    
    return results


def dependency_chain(
    analyzer: CodebaseAnalyzer,
    start: str,
    direction: str = "downstream"
) -> Dict[str, Any]:
    """
    Find dependency chain starting from a node.
    
    Args:
        analyzer: Initialized CodebaseAnalyzer
        start: Starting node name/ID
        direction: 'downstream' (depends on) or 'upstream' (depended by)
    
    Returns:
        Chain of dependencies
    """
    if not analyzer._graph:
        return {"error": "No graph loaded"}
    
    # Find starting node
    start_node = None
    for node in analyzer._graph.nodes.values():
        if node.id == start or node.name == start:
            start_node = node
            break
    
    if not start_node:
        return {"error": f"Start node not found: {start}"}
    
    # Build dependency chain
    chain = []
    visited = set()
    queue = [start_node.id]
    
    while queue and len(chain) < 50:  # Limit chain length
        current_id = queue.pop(0)
        if current_id in visited:
            continue
        visited.add(current_id)
        
        current = analyzer._graph.nodes.get(current_id)
        if current:
            chain.append({
                "id": current.id,
                "name": current.name,
                "type": current.type,
                "file": current.file_path
            })
            
            # Find related nodes
            for edge in analyzer._graph.edges:
                if direction == "downstream" and edge.source == current_id:
                    if edge.target not in visited:
                        queue.append(edge.target)
                elif direction == "upstream" and edge.target == current_id:
                    if edge.source not in visited:
                        queue.append(edge.source)
    
    return {
        "start": start,
        "direction": direction,
        "chain_length": len(chain),
        "chain": chain
    }


def find_dead_code(
    analyzer: CodebaseAnalyzer
) -> List[Dict[str, Any]]:
    """
    Find potentially dead/unused code.
    
    Returns functions/classes with no incoming edges.
    """
    if not analyzer._graph:
        return []
    
    # Build incoming edge count
    incoming = {}
    for edge in analyzer._graph.edges:
        if edge.target not in incoming:
            incoming[edge.target] = 0
        incoming[edge.target] += 1
    
    dead = []
    for node in analyzer._graph.nodes.values():
        if node.type in ["function", "method"]:
            # Exclude main, __init__, and obvious entry points
            if node.name in ['main', '__init__', 'run', 'start']:
                continue
            
            # Check if called
            if node.id not in incoming and incoming.get(node.name, 0) == 0:
                dead.append({
                    "name": node.name,
                    "file": node.file_path,
                    "line": node.line_no,
                    "confidence": "medium"
                })
    
    return dead


def complexity_report(
    analyzer: CodebaseAnalyzer
) -> Dict[str, Any]:
    """
    Generate complexity report for codebase.
    """
    if not analyzer._graph:
        return {"error": "No graph loaded"}
    
    stats = analyzer.get_statistics()
    
    # Find most complex files (by edge count)
    file_complexity = {}
    for edge in analyzer._graph.edges:
        source_file = None
        if edge.source in analyzer._graph.nodes:
            source_file = analyzer._graph.nodes[edge.source].file_path
        
        if source_file:
            file_complexity[source_file] = file_complexity.get(source_file, 0) + 1
    
    top_complex = sorted(file_complexity.items(), key=lambda x: x[1], reverse=True)[:10]
    
    return {
        "total_nodes": stats.get("total_nodes", 0),
        "total_edges": stats.get("total_edges", 0),
        "by_type": stats.get("by_type", {}),
        "by_language": stats.get("by_language", {}),
        "most_complex_files": [
            {"file": f, "connections": c} for f, c in top_complex
        ],
        "recommendation": "Review top complexity files for refactoring opportunities"
    }


if __name__ == "__main__":
    print("Query module ready. Available queries:")
    print("  - impact_analysis(analyzer, target)")
    print("  - find_feature(analyzer, description)")
    print("  - dependency_chain(analyzer, start)")
    print("  - find_dead_code(analyzer)")
    print("  - complexity_report(analyzer)")
