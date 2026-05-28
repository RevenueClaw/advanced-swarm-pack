#!/usr/bin/env python3
"""
skill-codebase-understander-v1: Deep codebase comprehension via knowledge graphs.

Main exports:
- CodebaseAnalyzer: Core analysis and query engine
- CodebaseContext: Integration helper for planning/estimation

Quick Start:
    from lib.codebase_analyzer import CodebaseAnalyzer
    
    analyzer = CodebaseAnalyzer()
    graph = analyzer.analyze_repository("/path/to/repo", languages=["python"])
    
    # Impact analysis
    impacts = analyzer.impact_analysis("db_handler.commit")
    print(f"{len(impacts['files'])} files affected")
"""

from .codebase_analyzer import CodebaseAnalyzer, AnalysisDepth, GraphNode
from .integration import CodebaseContext

try:
    from .queries import impact_analysis, find_feature, dependency_chain
except ImportError:
    # Queries module may need initialization
    pass

try:
    from .cache import CodebaseCache
except ImportError:
    pass

__all__ = [
    "CodebaseAnalyzer",
    "CodebaseContext",
    "AnalysisDepth",
    "GraphNode",
]

__version__ = "1.0.0"
__author__ = "RockClaw"
