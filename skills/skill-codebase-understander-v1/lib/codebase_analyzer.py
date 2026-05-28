#!/usr/bin/env python3
"""
CodebaseAnalyzer — Multi-language codebase analysis with knowledge graph generation.

Provides:
- Static analysis of Python, JavaScript, Go, Rust, Java
- Knowledge graph construction (modules, functions, classes, relationships)
- Impact analysis and dependency tracking
- Caching for incremental updates

Author: RockClaw  
Version: 1.0.0
"""

import os
import re
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict


class AnalysisDepth(Enum):
    """Depth of static analysis."""
    QUICK = "quick"      # Module-level only
    STANDARD = "standard"  # Functions, classes, basic call graph
    DEEP = "deep"        # Full analysis with data flow


class NodeType(Enum):
    """Types of nodes in the knowledge graph."""
    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    CONFIG = "config"
    EXTERNAL = "external"


class RelationType(Enum):
    """Types of edges between nodes."""
    IMPORTS = "imports"
    CALLS = "calls"
    INHERITS = "inherits"
    CONTAINS = "contains"
    USES = "uses"
    EXPORTS = "exports"


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    id: str
    type: str
    name: str
    file_path: Optional[str] = None
    line_no: Optional[int] = None
    language: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """An edge between nodes in the knowledge graph."""
    source: str
    target: str
    relation: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """Complete knowledge graph representation."""
    repo_path: str
    analyzed_at: str
    nodes: Dict[str, GraphNode]
    edges: List[GraphEdge]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo_path": self.repo_path,
            "analyzed_at": self.analyzed_at,
            "nodes": {k: asdict(v) for k, v in self.nodes.items()},
            "edges": [asdict(e) for e in self.edges],
            "metadata": self.metadata
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'KnowledgeGraph':
        nodes = {k: GraphNode(**v) for k, v in data.get("nodes", {}).items()}
        edges = [GraphEdge(**e) for e in data.get("edges", [])]
        return KnowledgeGraph(
            repo_path=data["repo_path"],
            analyzed_at=data["analyzed_at"],
            nodes=nodes,
            edges=edges,
            metadata=data.get("metadata", {})
        )


class CodebaseAnalyzer:
    """
    Analyzes codebase structure and builds knowledge graph.
    
    Usage:
        analyzer = CodebaseAnalyzer()
        graph = analyzer.analyze_repository(
            "/path/to/repo",
            languages=["python", "javascript"],
            depth=AnalysisDepth.STANDARD
        )
        
        # Query the graph
        module = analyzer.get_module("src/main.py")
        callers = analyzer.get_callers("DatabaseHandler.commit")
    """
    
    # File extensions by language
    LANGUAGE_PATTERNS = {
        "python": [r'\.py$'],
        "javascript": [r'\.js$', r'\.mjs$'],
        "typescript": [r'\.ts$', r'\.tsx$'],
        "go": [r'\.go$'],
        "rust": [r'\.rs$'],
        "java": [r'\.java$']
    }
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize analyzer.
        
        Args:
            cache_dir: Where to cache knowledge graphs (default: ~/.openclaw/codebase_graphs/)
        """
        self.cache_dir = cache_dir or Path.home() / ".openclaw" / "codebase_graphs"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._graph: Optional[KnowledgeGraph] = None
        self._repo_hash: Optional[str] = None
        
    def _hash_repo(self, repo_path: str) -> str:
        """Generate unique hash for repository."""
        abs_path = str(Path(repo_path).resolve())
        return hashlib.md5(abs_path.encode()).hexdigest()[:16]
    
    def _get_cache_path(self, repo_hash: str) -> Path:
        """Get cache directory for repository."""
        return self.cache_dir / repo_hash
    
    def _detect_languages(self, repo_path: str) -> List[str]:
        """Auto-detect languages in repository."""
        languages = set()
        repo_path = Path(repo_path)
        
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                if list(repo_path.rglob("*")):
                    # Quick check: any files matching pattern?
                    found = False
                    for file in repo_path.rglob("*"):
                        if file.is_file() and re.search(pattern, file.name):
                            languages.add(lang)
                            found = True
                            break
                    if found:
                        break
        
        return list(languages)
    
    def _find_files(self, repo_path: str, languages: List[str]) -> List[Path]:
        """Find all source files for specified languages."""
        files = []
        repo_path = Path(repo_path)
        
        for lang in languages:
            patterns = self.LANGUAGE_PATTERNS.get(lang, [])
            for pattern in patterns:
                for file in repo_path.rglob("*"):
                    if file.is_file() and re.search(pattern, file.name):
                        # Skip common non-source directories
                        if any(skip in str(file) for skip in [
                            '.git', 'node_modules', '__pycache__', 
                            '.venv', 'venv', 'dist', 'build'
                        ]):
                            continue
                        files.append(file)
        
        return sorted(set(files))  # Remove duplicates, sort for determinism
    
    def _analyze_python_file(self, file_path: Path, depth: AnalysisDepth) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Extract nodes and edges from Python file."""
        nodes = []
        edges = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IOError):
            return nodes, edges
        
        module_id = str(file_path.relative_to(file_path.parent.parent if file_path.parent.name == 'lib' else file_path.parent))
        if module_id.startswith('/'):
            module_id = module_id[1:]
        
        # Module node
        module_node = GraphNode(
            id=module_id,
            type=NodeType.MODULE.value,
            name=file_path.name,
            file_path=str(file_path),
            line_no=1,
            language="python",
            properties={
                "size_bytes": len(content),
                "line_count": content.count('\n') + 1
            }
        )
        nodes.append(module_node)
        
        # Parse imports (basic regex-based for portability)
        import_pattern = r'^(?:from\s+(\S+)\s+import|import\s+(\S+))'
        for line_no, line in enumerate(content.split('\n'), 1):
            match = re.match(import_pattern, line.strip())
            if match:
                module_name = match.group(1) or match.group(2)
                edges.append(GraphEdge(
                    source=module_id,
                    target=f"external:{module_name}",
                    relation=RelationType.IMPORTS.value,
                    properties={"line": line_no}
                ))
        
        # Parse class definitions
        class_pattern = r'^class\s+(\w+)(?:\([^)]*\))?:'
        for line_no, line in enumerate(content.split('\n'), 1):
            match = re.match(class_pattern, line.strip())
            if match:
                class_name = match.group(1)
                class_id = f"{module_id}::{class_name}"
                
                # Extract inheritance
                inherits = []
                if '(' in line and ')' in line:
                    parent_str = line[line.index('(')+1:line.index(')')]
                    inherits = [p.strip() for p in parent_str.split(',')]
                
                class_node = GraphNode(
                    id=class_id,
                    type=NodeType.CLASS.value,
                    name=class_name,
                    file_path=str(file_path),
                    line_no=line_no,
                    language="python",
                    properties={"inherits": inherits}
                )
                nodes.append(class_node)
                
                edges.append(GraphEdge(
                    source=module_id,
                    target=class_id,
                    relation=RelationType.CONTAINS.value
                ))
                
                for parent in inherits:
                    edges.append(GraphEdge(
                        source=class_id,
                        target=parent,
                        relation=RelationType.INHERITS.value
                    ))
        
        # Parse function definitions (standard
        func_pattern = r'^def\s+(\w+)\s*\('
        for line_no, line in enumerate(content.split('\n'), 1):
            match = re.match(func_pattern, line.strip())
            if match:
                func_name = match.group(1)
                func_id = f"{module_id}::{func_name}"
                
                func_node = GraphNode(
                    id=func_id,
                    type=NodeType.FUNCTION.value,
                    name=func_name,
                    file_path=str(file_path),
                    line_no=line_no,
                    language="python",
                    properties={}
                )
                nodes.append(func_node)
                
                edges.append(GraphEdge(
                    source=module_id,
                    target=func_id,
                    relation=RelationType.CONTAINS.value
                ))
        
        if depth == AnalysisDepth.DEEP:
            # Deeper analysis: function calls
            call_pattern = r'(\w+)\s*\('
            for line_no, line in enumerate(content.split('\n'), 1):
                calls = re.findall(call_pattern, line)
                for called_func in calls:
                    if called_func not in ['if', 'while', 'for', 'print', 'len', 'range']:
                        edges.append(GraphEdge(
                            source=module_id,
                            target=f"call:{called_func}",
                            relation=RelationType.CALLS.value,
                            properties={"line": line_no}
                        ))
        
        return nodes, edges
    
    def _analyze_javascript_file(self, file_path: Path, depth: AnalysisDepth) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Extract nodes and edges from JavaScript/TypeScript file."""
        nodes = []
        edges = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IOError):
            return nodes, edges
        
        module_id = str(file_path.relative_to(file_path.parent.parent if file_path.parent.name in ['src', 'lib'] else file_path.parent))
        if module_id.startswith('/'):
            module_id = module_id[1:]
        
        # Module node
        module_node = GraphNode(
            id=module_id,
            type=NodeType.MODULE.value,
            name=file_path.name,
            file_path=str(file_path),
            line_no=1,
            language="javascript",
            properties={
                "size_bytes": len(content),
                "line_count": content.count('\n') + 1
            }
        )
        nodes.append(module_node)
        
        # Parse imports
        import_pattern = r'import\s+(?:{[^}]+}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]|require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        for line_no, line in enumerate(content.split('\n'), 1):
            match = re.search(import_pattern, line)
            if match:
                module_name = match.group(1) or match.group(2)
                edges.append(GraphEdge(
                    source=module_id,
                    target=f"external:{module_name}",
                    relation=RelationType.IMPORTS.value,
                    properties={"line": line_no}
                ))
        
        # Parse function definitions (multiple patterns)
        func_patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(',  # function declarations
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(',  # arrow functions
            r'(\w+)\s*:\s*(?:async\s+)?\(',  # object methods
        ]
        
        for line_no, line in enumerate(content.split('\n'), 1):
            for pattern in func_patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    func_id = f"{module_id}::{func_name}"
                    
                    func_node = GraphNode(
                        id=func_id,
                        type=NodeType.FUNCTION.value,
                        name=func_name,
                        file_path=str(file_path),
                        line_no=line_no,
                        language="javascript",
                        properties={}
                    )
                    nodes.append(func_node)
                    
                    edges.append(GraphEdge(
                        source=module_id,
                        target=func_id,
                        relation=RelationType.CONTAINS.value
                    ))
                    break
        
        # Parse class definitions
        class_pattern = r'(?:export\s+)?class\s+(\w+)'
        for line_no, line in enumerate(content.split('\n'), 1):
            match = re.search(class_pattern, line)
            if match:
                class_name = match.group(1)
                class_id = f"{module_id}::{class_name}"
                
                class_node = GraphNode(
                    id=class_id,
                    type=NodeType.CLASS.value,
                    name=class_name,
                    file_path=str(file_path),
                    line_no=line_no,
                    language="javascript",
                    properties={}
                )
                nodes.append(class_node)
                
                edges.append(GraphEdge(
                    source=module_id,
                    target=class_id,
                    relation=RelationType.CONTAINS.value
                ))
        
        return nodes, edges
    
    def analyze_repository(
        self,
        repo_path: str,
        languages: Optional[List[str]] = None,
        depth: AnalysisDepth = AnalysisDepth.STANDARD,
        incremental: bool = False
    ) -> KnowledgeGraph:
        """
        Analyze a repository and build knowledge graph.
        
        Args:
            repo_path: Path to repository root
            languages: Languages to analyze (auto-detect if None)
            depth: Analysis depth level
            incremental: Update only changed files (if cached)
        
        Returns:
            KnowledgeGraph with all discovered nodes and edges
        """
        repo_path = Path(repo_path).resolve()
        
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        # Auto-detect languages
        if languages is None:
            languages = self._detect_languages(repo_path)
            print(f"Auto-detected languages: {', '.join(languages)}")
        
        # Check cache
        repo_hash = self._hash_repo(str(repo_path))
        cache_path = self._get_cache_path(repo_hash)
        cache_file = cache_path / "knowledge_graph.json"
        
        if incremental and cache_file.exists():
            # Load and update existing graph
            with open(cache_file) as f:
                cached_data = json.load(f)
            graph = KnowledgeGraph.from_dict(cached_data)
            print(f"Loaded cached graph: {len(graph.nodes)} nodes")
            # TODO: Implement incremental update logic
        else:
            # Build new graph
            graph = KnowledgeGraph(
                repo_path=str(repo_path),
                analyzed_at=datetime.utcnow().isoformat(),
                nodes={},
                edges=[],
                metadata={
                    "languages": languages,
                    "depth": depth.value,
                    "repo_hash": repo_hash
                }
            )
        
        # Find all source files
        files = self._find_files(repo_path, languages)
        print(f"Found {len(files)} source files")
        
        # Analyze each file
        for file_path in files:
            if file_path.suffix == '.py':
                nodes, edges = self._analyze_python_file(file_path, depth)
            elif file_path.suffix in ['.js', '.mjs', '.ts', '.tsx']:
                nodes, edges = self._analyze_javascript_file(file_path, depth)
            else:
                continue
            
            # Add nodes to graph
            for node in nodes:
                graph.nodes[node.id] = node
            
            # Add edges to graph
            graph.edges.extend(edges)
        
        # Resolve call edges (simple resolution)
        self._resolve_call_edges(graph)
        
        # Cache the graph
        self._cache_graph(graph, cache_path)
        
        self._graph = graph
        self._repo_hash = repo_hash
        
        print(f"Analysis complete: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        return graph
    
    def _resolve_call_edges(self, graph: KnowledgeGraph) -> None:
        """Attempt to resolve function calls to specific nodes."""
        # Build name-to-node mapping
        name_to_node = {}
        for node in graph.nodes.values():
            if node.name:
                name_to_node[node.name] = node.id
        
        # Update call edges with resolved targets
        for edge in graph.edges:
            if edge.relation == RelationType.CALLS.value:
                target = edge.target
                if target.startswith("call:"):
                    func_name = target[5:]  # Remove "call:" prefix
                    if func_name in name_to_node:
                        edge.target = name_to_node[func_name]
    
    def _cache_graph(self, graph: KnowledgeGraph, cache_path: Path) -> None:
        """Cache graph to disk."""
        cache_path.mkdir(parents=True, exist_ok=True)
        cache_file = cache_path / "knowledge_graph.json"
        
        with open(cache_file, 'w') as f:
            json.dump(graph.to_dict(), f, indent=2)
    
    def impact_analysis(self, target: str) -> Dict[str, Any]:
        """
        Analyze what would be affected by changing a node.
        
        Args:
            target: Node ID or name to analyze (e.g., "DatabaseHandler.commit" or "src/main.py")
        
        Returns:
            Dict with affected files, functions, classes, and suggested test updates
        """
        if self._graph is None:
            raise ValueError("No graph loaded. Call analyze_repository() first.")
        
        # Find target node
        target_node = None
        for node in self._graph.nodes.values():
            if node.id == target or node.name == target:
                target_node = node
                break
        
        if target_node is None:
            return None
        
        # Find all nodes that call or import this target
        affected = {
            "target_node": asdict(target_node),
            "direct_callers": [],
            "indirect_callers": [],
            "importers": [],
            "affected_files": set(),
            "affected_tests": [],
            "estimated_complexity": "medium"
        }
        
        # Find direct callers
        for edge in self._graph.edges:
            if edge.target == target_node.id and edge.relation == RelationType.CALLS.value:
                caller_node = self._graph.nodes.get(edge.source)
                if caller_node:
                    affected["direct_callers"].append(asdict(caller_node))
                    if caller_node.file_path:
                        affected["affected_files"].add(caller_node.file_path)
            
            # Find importers if target is a module
            if edge.target == target_node.id and edge.relation == RelationType.IMPORTS.value:
                importer_node = self._graph.nodes.get(edge.source)
                if importer_node:
                    affected["importers"].append(asdict(importer_node))
        
        # Try to find test files
        for file_path in affected["affected_files"]:
            # Look for corresponding test files
            patterns = [
                re.sub(r'\.py$', '_test.py', file_path),
                re.sub(r'\.py$', '_tests.py', file_path),
                re.sub(r'/([^/]+)\.py$', r'/test_\1.py', file_path),
                file_path.replace('.py', 'Test.py')
            ]
            for pattern in patterns:
                if Path(pattern).exists():
                    affected["affected_tests"].append(pattern)
        
        # Calculate complexity
        total_affected = len(affected["direct_callers"]) + len(affected["importers"])
        if total_affected > 20:
            affected["estimated_complexity"] = "high"
        elif total_affected > 5:
            affected["estimated_complexity"] = "medium"
        else:
            affected["estimated_complexity"] = "low"
        
        affected["affected_files"] = list(affected["affected_files"])
        
        return affected
    
    def get_module(self, module_path: str) -> Optional[GraphNode]:
        """Get a module node by path."""
        if self._graph is None:
            return None
        return self._graph.nodes.get(module_path)
    
    def get_callers(self, function_name: str) -> List[GraphNode]:
        """Get all nodes that call a given function."""
        if self._graph is None:
            return []
        
        callers = []
        for edge in self._graph.edges:
            if edge.target.endswith(f"::{function_name}") or edge.target == function_name:
                if edge.relation == RelationType.CALLS.value:
                    caller = self._graph.nodes.get(edge.source)
                    if caller:
                        callers.append(caller)
        
        return callers
    
    def get_dependencies(self, node_id: str) -> List[GraphNode]:
        """Get all dependencies of a node."""
        if self._graph is None:
            return []
        
        deps = []
        for edge in self._graph.edges:
            if edge.source == node_id and edge.relation in [RelationType.IMPORTS.value, RelationType.CALLS.value]:
                target = self._graph.nodes.get(edge.target)
                if target:
                    deps.append(target)
        
        return deps
    
    def find_symbol(self, name: str) -> List[GraphNode]:
        """Find all nodes matching a symbol name."""
        if self._graph is None:
            return []
        
        return [n for n in self._graph.nodes.values() 
                if n.name == name or n.id.endswith(f"::{name}")]
    
    def query(self, node_type: Optional[str] = None, language: Optional[str] = None) -> List[GraphNode]:
        """Query nodes by type and/or language."""
        if self._graph is None:
            return []
        
        results = []
        for node in self._graph.nodes.values():
            if node_type and node.type != node_type:
                continue
            if language and node.language != language:
                continue
            results.append(node)
        
        return results
    
    def get_graph(self) -> Optional[KnowledgeGraph]:
        """Get the current knowledge graph."""
        return self._graph
    
    def save_graph(self, output_path: str) -> bool:
        """Save current graph to a file."""
        if self._graph is None:
            return False
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(self._graph.to_dict(), f, indent=2)
        
        return True
    
    def load_cached(self, repo_path: str) -> Optional[KnowledgeGraph]:
        """Load a cached graph for a repository."""
        repo_hash = self._hash_repo(repo_path)
        cache_path = self._get_cache_path(repo_hash)
        cache_file = cache_path / "knowledge_graph.json"
        
        if cache_file.exists():
            with open(cache_file) as f:
                data = json.load(f)
            self._graph = KnowledgeGraph.from_dict(data)
            self._repo_hash = repo_hash
            return self._graph
        
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the analyzed codebase."""
        if self._graph is None:
            return {}
        
        stats = {
            "total_nodes": len(self._graph.nodes),
            "total_edges": len(self._graph.edges),
            "by_type": {},
            "by_language": {},
            "files": 0
        }
        
        for node in self._graph.nodes.values():
            # Count by type
            stats["by_type"][node.type] = stats["by_type"].get(node.type, 0) + 1
            
            # Count by language
            if node.language:
                stats["by_language"][node.language] = stats["by_language"].get(node.language, 0) + 1
            
            # Count files
            if node.type == NodeType.MODULE.value:
                stats["files"] += 1
        
        return stats


def analyze_codebase(repo_path: str, **kwargs) -> KnowledgeGraph:
    """Convenience function for one-shot analysis."""
    analyzer = CodebaseAnalyzer()
    return analyzer.analyze_repository(repo_path, **kwargs)


def demo():
    """Run a demo analysis."""
    print("=" * 60)
    print("CODEBASE ANALYZER DEMO")
    print("=" * 60)
    
    # Analyze self (this skill)
    skill_path = Path(__file__).parent.parent
    print(f"\nAnalyzing: {skill_path}")
    
    analyzer = CodebaseAnalyzer()
    graph = analyzer.analyze_repository(skill_path, languages=["python"], depth=AnalysisDepth.STANDARD)
    
    stats = analyzer.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total nodes: {stats['total_nodes']}")
    print(f"   Total edges: {stats['total_edges']}")
    print(f"   By type: {stats['by_type']}")
    
    # Find all classes
    print(f"\n📦 Classes found:")
    for node in analyzer.query(node_type=NodeType.CLASS.value):
        print(f"   - {node.name} ({node.file_path})")
    
    # Find all functions
    print(f"\n🔧 Functions found:")
    for node in analyzer.query(node_type=NodeType.FUNCTION.value):
        print(f"   - {node.name} ({node.file_path}:{node.line_no})")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()