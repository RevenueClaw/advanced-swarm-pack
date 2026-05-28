#!/usr/bin/env python3
"""
Cache management for codebase analysis graphs.

Author: RockClaw
Version: 1.0.0
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List


class CodebaseCache:
    """Manages caching of codebase knowledge graphs."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".openclaw" / "codebase_graphs"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def is_stale(self, repo_path: str, max_age_hours: int = 24) -> bool:
        """Check if cached graph is stale."""
        from .codebase_analyzer import CodebaseAnalyzer
        
        analyzer = CodebaseAnalyzer(cache_dir=self.cache_dir)
        repo_hash = analyzer._hash_repo(repo_path)
        cache_path = self.cache_dir / repo_hash
        cache_file = cache_path / "knowledge_graph.json"
        
        if not cache_file.exists():
            return True
        
        # Check age
        mtime = cache_file.stat().st_mtime
        age = datetime.now() - datetime.fromtimestamp(mtime)
        
        return age > timedelta(hours=max_age_hours)
    
    def get_last_analysis_time(self, repo_path: str) -> Optional[datetime]:
        """Get timestamp of last analysis."""
        from .codebase_analyzer import CodebaseAnalyzer
        
        analyzer = CodebaseAnalyzer(cache_dir=self.cache_dir)
        repo_hash = analyzer._hash_repo(repo_path)
        cache_path = self.cache_dir / repo_hash
        metadata_file = cache_path / "metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file) as f:
                data = json.load(f)
                ts = data.get("analyzed_at")
                if ts:
                    return datetime.fromisoformat(ts)
        
        return None
    
    def cleanup_older_than(self, days: int = 30) -> int:
        """Remove cached graphs older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        removed = 0
        
        for cache_path in self.cache_dir.iterdir():
            if cache_path.is_dir():
                graph_file = cache_path / "knowledge_graph.json"
                if graph_file.exists():
                    mtime = datetime.fromtimestamp(graph_file.stat().st_mtime)
                    if mtime < cutoff:
                        # Remove entire cache directory
                        import shutil
                        shutil.rmtree(cache_path)
                        removed += 1
        
        return removed
    
    def list_cached_repos(self) -> List[dict]:
        """List all cached repositories."""
        repos = []
        
        for cache_path in self.cache_dir.iterdir():
            if cache_path.is_dir():
                metadata_file = cache_path / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file) as f:
                        data = json.load(f)
                        repos.append({
                            "hash": cache_path.name,
                            "repo_path": data.get("repo_path", "unknown"),
                            "analyzed_at": data.get("analyzed_at"),
                            "languages": data.get("languages", [])
                        })
        
        return repos


def demo():
    """Demo cache management."""
    cache = CodebaseCache()
    
    print("Cached repositories:")
    for repo in cache.list_cached_repos():
        print(f"  - {repo['repo_path'][:50]}... ({repo['analyzed_at'][:10]})")
    
    print(f"\nCleanup candidates (older than 30 days): {cache.cleanup_older_than(days=30, dry_run=True)}")


if __name__ == "__main__":
    print("Codebase Cache module ready for import")
