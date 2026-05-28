#!/usr/bin/env python3
"""
Codebase Understanding Integration Hooks

Connects CodebaseAnalyzer to:
- skill-architect-first (PlanReviewer context injection)
- skill-estimation-engine (complexity-based time estimation)
- skill-consensus (code complexity context)

Author: RockClaw
Version: 1.0.0
"""

from typing import Dict, Any, Optional, List
from pathlib import Path


class CodebaseContext:
    """
    Context provider for planning and estimation based on codebase analysis.
    
    Usage:
        context = CodebaseContext.from_plan(plan)
        complexity = context.get_overall_complexity()
        affected = context.get_affected_files()
    """
    
    def __init__(self, analyzer=None, repo_path: Optional[str] = None):
        self.analyzer = analyzer
        self.repo_path = repo_path
        self._cached_graph = None
    
    @classmethod
    def from_plan(cls, plan: Dict[str, Any]) -> 'CodebaseContext':
        """Create context from a plan dict."""
        repo_path = plan.get("repo_path", ".")
        
        from .codebase_analyzer import CodebaseAnalyzer
        analyzer = CodebaseAnalyzer()
        
        # Try to load cached graph first
        graph = analyzer.load_cached(repo_path)
        if graph is None:
            # Analyze if needed
            print(f"No cached graph found for {repo_path}, analyzing...")
            graph = analyzer.analyze_repository(repo_path)
        
        return cls(analyzer=analyzer, repo_path=repo_path)
    
    @classmethod
    def from_files(cls, file_paths: List[str], repo_path: str = ".") -> 'CodebaseContext':
        """Create context from specific files."""
        ctx = cls.from_plan({"repo_path": repo_path})
        ctx._target_files = file_paths
        return ctx
    
    def get_affected_files(self) -> List[str]:
        """Get list of files affected by a change."""
        if not self.analyzer:
            return []
        
        files = set()
        
        # Get modules from graph
        for node in self.analyzer.query(node_type="module"):
            if node.file_path:
                files.add(node.file_path)
        
        return sorted(files)
    
    def calculate_dependency_depth(self, node_id: Optional[str] = None) -> int:
        """
        Calculate max dependency depth from a starting point.
        
        Returns:
            Integer depth (0 = isolated, 1-2 = simple, 3+ = complex, 5+ = very complex)
        """
        if not self.analyzer or not self.analyzer._graph:
            return 0
        
        graph = self.analyzer._graph
        edges_by_source = {}
        
        for edge in graph.edges:
            if edge.source not in edges_by_source:
                edges_by_source[edge.source] = []
            edges_by_source[edge.source].append(edge.target)
        
        # BFS to find max depth
        if node_id:
            start_nodes = [node_id]
        else:
            start_nodes = [n.id for n in graph.nodes.values() if n.type == "module"]
        
        max_depth = 0
        for start in start_nodes:
            visited = set()
            depth = {start: 0}
            queue = [start]
            
            while queue:
                current = queue.pop(0)
                visited.add(current)
                max_depth = max(max_depth, depth[current])
                
                for neighbor in edges_by_source.get(current, []):
                    if neighbor not in visited:
                        depth[neighbor] = depth[current] + 1
                        queue.append(neighbor)
        
        return max_depth
    
    def find_untested_dependencies(self) -> List[str]:
        """Find modules that lack test coverage."""
        all_files = self.get_affected_files()
        test_files = set()
        files_needing_tests = []
        
        for f in all_files:
            # Identify test files
            if any(x in f.lower() for x in ['test_', '_test', '_spec', 'Spec', 'Test']):
                test_files.add(f)
        
        # Check which non-test files have corresponding test files
        for f in all_files:
            if f in test_files:
                continue
            
            # Possible test file patterns
            base = f.replace('.py', '').replace('.js', '')
            test_patterns = [
                f"test_{base}.py",
                f"{base}_test.py",
                f"{base}.test.js",
                f"{base}.spec.js"
            ]
            
            has_test = any(any(tp in tf for tf in test_files) for tp in test_patterns)
            if not has_test:
                files_needing_tests.append(f)
        
        return files_needing_tests
    
    def get_overall_complexity(self) -> str:
        """
        Summarize overall codebase complexity.
        
        Returns:
            String: "low", "medium", "high", "very_high"
        """
        if not self.analyzer:
            return "unknown"
        
        stats = self.analyzer.get_statistics()
        
        metrics = {
            "total_nodes": stats.get("total_nodes", 0),
            "files": stats.get("files", 0),
            "dependency_depth": self.calculate_dependency_depth()
        }
        
        # Complexity scoring
        score = 0
        
        if metrics["files"] > 100:
            score += 2
        elif metrics["files"] > 20:
            score += 1
        
        if metrics["dependency_depth"] > 4:
            score += 2
        elif metrics["dependency_depth"] > 2:
            score += 1
        
        if metrics["total_nodes"] > 500:
            score += 2
        elif metrics["total_nodes"] > 100:
            score += 1
        
        complexity_map = {
            0: "low",
            1: "medium",
            2: "medium",
            3: "high",
            4: "high",
            5: "very_high",
            6: "very_high"
        }
        
        return complexity_map.get(min(score, 6), "medium")
    
    def get_impact_summary(self, target: str) -> Dict[str, Any]:
        """Get human-readable impact summary for a target."""
        if not self.analyzer:
            return {"error": "No analyzer loaded"}
        
        impact = self.analyzer.impact_analysis(target)
        
        if impact is None:
            return {"error": f"Target not found: {target}"}
        
        return {
            "target": target,
            "complexity": impact.get("estimated_complexity"),
            "files_affected": len(impact.get("affected_files", [])),
            "direct_callers": len(impact.get("direct_callers", [])),
            "test_files_to_update": impact.get("affected_tests", []),
            "recommendation": self._recommendation_from_impact(impact)
        }
    
    def _recommendation_from_impact(self, impact: Dict[str, Any]) -> str:
        """Generate recommendation text from impact analysis."""
        complexity = impact.get("estimated_complexity", "medium")
        files = len(impact.get("affected_files", []))
        callers = len(impact.get("direct_callers", []))
        
        if complexity == "high":
            return f"High-impact change affecting {files} files and {callers} callers. Recommend phased rollout with feature flags."
        elif complexity == "medium":
            return f"Medium-impact change affecting {files} files. Ensure tests pass before merging."
        else:
            return f"Low-impact change affecting {files} files. Standard review process sufficient."
    
    def to_plan_context(self) -> Dict[str, Any]:
        """Convert to context dict for Architect-First PlanReviewer."""
        return {
            "complexity": self.get_overall_complexity(),
            "dependency_depth": self.calculate_dependency_depth(),
            "untested_files": self.find_untested_dependencies()[:5],  # Cap at 5
            "total_modules": len(self.analyzer.query(node_type="module")) if self.analyzer else 0,
            "total_functions": len(self.analyzer.query(node_type="function")) if self.analyzer else 0,
            "total_classes": len(self.analyzer.query(node_type="class")) if self.analyzer else 0
        }


class EstimationHelper:
    """
    Helper for time estimation based on codebase complexity.
    
    Integrates with skill-estimation-engine to provide complexity-based
    calibration factors.
    """
    
    def __init__(self, analyzer=None):
        self.analyzer = analyzer
    
    def estimate_change(self, change: str, impact_files: List[str]) -> Dict[str, Any]:
        """
        Estimate effort for a code change.
        
        Args:
            change: Description of the change
            impact_files: Files expected to be modified
        
        Returns:
            Estimate dict with hours, factors, and approach
        """
        if not self.analyzer:
            return {"error": "No analyzer available"}
        
        # Base hours by task type
        base_hours = 4.0
        
        if "refactor" in change.lower():
            base_hours = 8.0
        elif "add" in change.lower() or "implement" in change.lower():
            base_hours = 6.0
        elif "fix" in change.lower():
            base_hours = 3.0
        
        # Complexity factors
        factors = []
        
        # File count factor
        if len(impact_files) > 10:
            factors.append("affects_many_files")
            base_hours *= 1.5
        elif len(impact_files) > 5:
            factors.append("affects_multiple_files")
            base_hours *= 1.3
        
        # Dependency analysis
        total_deps = 0
        for file in impact_files:
            imp = self.analyzer.impact_analysis(file)
            if imp:
                total_deps += len(imp.get("direct_callers", []))
        
        if total_deps > 20:
            factors.append("high_fan_out")
            base_hours *= 1.4
        elif total_deps > 10:
            factors.append("medium_fan_out")
            base_hours *= 1.2
        
        # Test coverage factor
        ctx = CodebaseContext(self.analyzer)
        untested = ctx.find_untested_dependencies()
        if len(untested) > len(impact_files) * 0.5:
            factors.append("test_coverage_gap")
            base_hours *= 1.3
        
        # Depth factor
        depth = ctx.calculate_dependency_depth()
        if depth > 4:
            factors.append("tight_coupling")
            base_hours *= 1.25
        
        # Determine recommended approach
        approach = "standard"
        if "high_fan_out" in factors or "tight_coupling" in factors:
            approach = "extract_interface_first"
        elif "test_coverage_gap" in factors:
            approach = "add_tests_first"
        
        return {
            "estimated_hours": round(base_hours, 1),
            "base_hours": base_hours,
            "complexity_factors": factors,
            "files_analyzed": len(impact_files),
            "total_affected_dependencies": total_deps,
            "recommended_approach": approach,
            "risk_level": "high" if len(factors) > 2 else ("medium" if factors else "low")
        }
    
    def estimate_refactor(self, target_module: str) -> Dict[str, Any]:
        """
        Special estimation for refactoring tasks.
        
        Refactoring is inherently riskier because you're changing working code.
        """
        if not self.analyzer:
            return {"error": "No analyzer available"}
        
        impact = self.analyzer.impact_analysis(target_module)
        
        if impact is None:
            return {"error": f"Target not found: {target_module}"}
        
        base_hours = 8.0  # Refactoring baseline
        
        # Risk multipliers
        if impact["estimated_complexity"] == "high":
            base_hours *= 2.0
        elif impact["estimated_complexity"] == "medium":
            base_hours *= 1.5
        
        # Coverage penalty
        if len(impact.get("affected_tests", [])) == 0:
            base_hours *= 1.5  # Extra time to add tests
        
        return {
            "estimated_hours": round(base_hours, 1),
            "complexity": impact["estimated_complexity"],
            "files_affected": len(impact["affected_files"]),
            "test_files_to_update": impact["affected_tests"],
            "recommendation": "High-risk refactor - consider interface extraction first",
            "required_before_merge": [
                "All affected tests pass",
                "Manual smoke testing",
                "Code review by domain expert"
            ]
        }


def integrate_with_plan_reviewer(plan_reviewer, plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance a plan with codebase context.
    
    Called from skill-architect-first when plan involves code changes.
    
    Args:
        plan_reviewer: PlanReviewer instance
        plan: Plan dict
    
    Returns:
        Enhanced plan with codebase insights
    """
    # Check if this is a code change plan
    goal = plan.get("goal", "").lower()
    is_code_plan = any(kw in goal for kw in [
        "implement", "refactor", "add", "change", "modify",
        "code", "feature", "function", "class", "module"
    ])
    
    if not is_code_plan:
        return plan
    
    # Get codebase context
    ctx = CodebaseContext.from_plan(plan)
    
    # Add to plan
    enhanced = dict(plan)
    enhanced["codebase_context"] = ctx.to_plan_context()
    
    # Add complexity warning if high
    if ctx.get_overall_complexity() == "very_high":
        enhanced["complexity_warning"] = (
            "Very high complexity codebase detected. "
            "Recommend incremental changes with thorough testing."
        )
    
    return enhanced


if __name__ == "__main__":
    print("Codebase Understanding integrations ready.")
    print("Import with: from skill_codebase_understander_v1.lib.integration import CodebaseContext")
