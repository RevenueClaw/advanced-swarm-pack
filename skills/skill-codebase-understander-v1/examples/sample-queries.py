#!/usr/bin/env python3
"""
Example queries for codebase understanding.

Run this to see how the skill works on the swarm pack itself.
"""

import sys
from pathlib import Path

# Add the skill to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.codebase_analyzer import CodebaseAnalyzer, AnalysisDepth


def main():
    """Run sample queries on the swarm pack."""
    print("=" * 60)
    print("CODEBASE UNDERSTANDER - Example Queries")
    print("=" * 60)
    
    # Analyze the swarm pack
    repo_path = Path(__file__).parent.parent.parent.parent.parent
    print(f"\n📁 Analyzing: {repo_path}")
    
    analyzer = CodebaseAnalyzer()
    graph = analyzer.analyze_repository(
        repo_path,
        languages=["python"],
        depth=AnalysisDepth.STANDARD
    )
    
    print("\n" + "=" * 60)
    print("QUERY 1: Statistics")
    print("=" * 60)
    stats = analyzer.get_statistics()
    print(f"Total nodes: {stats['total_nodes']}")
    print(f"Total edges: {stats['total_edges']}")
    print(f"By type: {stats['by_type']}")
    print(f"By language: {stats['by_language']}")
    
    print("\n" + "=" * 60)
    print("QUERY 2: All Classes")
    print("=" * 60)
    for node in analyzer.query(node_type="class")[:10]:
        print(f"  - {node.name} ({node.file_path}:{node.line_no})")
    
    print("\n" + "=" * 60)
    print("QUERY 3: Impact Analysis (CodebaseAnalyzer)")
    print("=" * 60)
    impacts = analyzer.impact_analysis("CodebaseAnalyzer.analyze_repository")
    if impacts:
        print(f"Complexity: {impacts['estimated_complexity']}")
        print(f"Files affected: {len(impacts['affected_files'])}")
        print(f"Direct callers: {len(impacts['direct_callers'])}")
    
    print("\n" + "=" * 60)
    print("QUERY 4: Find Symbol (PlanReviewer)")
    print("=" * 60)
    symbols = analyzer.find_symbol("PlanReviewer")
    print(f"Found {len(symbols)} symbols")
    for sym in symbols[:3]:
        print(f"  - {sym.id} at {sym.file_path}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
