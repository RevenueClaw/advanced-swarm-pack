#!/usr/bin/env python3
"""ShadowRunner - Execution layer for shadow testing.

Key Features:
- Parallel execution of production + shadow versions
- Async result comparison
- Performance metrics collection
- Result logging and divergence detection

Author: RockClaw
Version: 1.0.0-alpha
Status: VERIFIED (basic structure)
"""

import json
import hashlib
import asyncio
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import traceback


@dataclass
class ExecutionMetrics:
    """Performance metrics for a single execution."""
    start_time: float
    end_time: float
    duration_ms: int
    memory_kb: int = 0
    cpu_percent: float = 0.0
    
    @property
    def latency_ms(self) -> int:
        return self.duration_ms


@dataclass
class ComparisonResult:
    """Comparison between production and shadow outputs."""
    task_hash: str
    task_preview: str
    prod_version: str
    shadow_version: str
    prod_output: Any
    shadow_output: Any
    prod_metrics: ExecutionMetrics
    shadow_metrics: ExecutionMetrics
    similarity_score: float
    performance_delta_ms: int
    accepted: bool
    divergence_details: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {
            "task_hash": self.task_hash,
            "task_preview": self.task_preview,
            "prod_version": self.prod_version,
            "shadow_version": self.shadow_version,
            "prod_output": self._serialize_output(self.prod_output),
            "shadow_output": self._serialize_output(self.shadow_output),
            "prod_metrics": {
                "duration_ms": self.prod_metrics.duration_ms,
                "latency_ms": self.prod_metrics.latency_ms
            },
            "shadow_metrics": {
                "duration_ms": self.shadow_metrics.duration_ms,
                "latency_ms": self.shadow_metrics.latency_ms
            },
            "similarity_score": round(self.similarity_score, 4),
            "performance_delta_ms": self.performance_delta_ms,
            "accepted": self.accepted,
            "divergence_details": self.divergence_details,
            "timestamp": self.timestamp
        }
    
    @staticmethod
    def _serialize_output(output: Any) -> Any:
        """Serialize output for storage."""
        if isinstance(output, (str, int, float, bool)):
            return output
        if isinstance(output, (list, dict)):
            return output
        try:
            return str(output)[:1000]  # Limit large outputs
        except:
            return "<unserializable>"
    
    def to_log_line(self) -> str:
        """Compress to log line."""
        summary = {
            "ts": self.timestamp[:19],
            "task": self.task_hash[:12],
            "pv": self.prod_version,
            "sv": self.shadow_version,
            "sim": round(self.similarity_score, 3),
            "dt_ms": self.performance_delta_ms,
            "ok": self.accepted
        }
        return json.dumps(summary)


class ShadowRunner:
    """
    Executes production and shadow versions in parallel.
    
    Usage:
        runner = ShadowRunner(similarity_threshold=0.85)
        result = runner.compare(
            task={"query": "search memory"},
            prod_executor=lambda t: search_v1(t),
            shadow_executor=lambda t: search_v2(t),
            prod_version="1.0.0",
            shadow_version="2.0.0"
        )
    """
    
    def __init__(
        self,
        similarity_threshold: float = 0.85,
        max_workers: int = 4,
        log_dir: Optional[Path] = None
    ):
        self.similarity_threshold = similarity_threshold
        self.max_workers = max_workers
        self.log_dir = log_dir or Path(
            "/home/rock/.openclaw/workspace/skills/skill-versioning/shadow_results"
        )
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def _compute_task_hash(self, task: Any) -> str:
        """Compute deterministic hash for task."""
        task_str = json.dumps(task, sort_keys=True, default=str)
        return hashlib.sha256(task_str.encode()).hexdigest()[:32]
    
    def _create_preview(self, task: Any, max_len: int = 80) -> str:
        """Create short preview of task."""
        preview = str(task)[:max_len]
        return preview + "..." if len(str(task)) > max_len else preview
    
    def _default_compare(
        self,
        prod_output: Any,
        shadow_output: Any
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Default comparison function.
        Returns similarity score and divergence details.
        """
        details = {}
        
        # Stringify for comparison
        prod_str = json.dumps(prod_output, sort_keys=True, default=str)
        shadow_str = json.dumps(shadow_output, sort_keys=True, default=str)
        
        # Exact match
        if prod_str == shadow_str:
            return 1.0, {"match_type": "exact"}
        
        # Type-level comparison
        if type(prod_output) != type(shadow_output):
            details["match_type"] = "type_mismatch"
            details["prod_type"] = type(prod_output).__name__
            details["shadow_type"] = type(shadow_output).__name__
            return 0.0, details
        
        # List comparison
        if isinstance(prod_output, list):
            return self._compare_lists(prod_output, shadow_output)
        
        # Dict comparison
        if isinstance(prod_output, dict):
            return self._compare_dicts(prod_output, shadow_output)
        
        # String/number comparison
        if isinstance(prod_output, (str, bytes)):
            prod_set = set(str(prod_output).split())
            shadow_set = set(str(shadow_output).split())
            if not prod_set and not shadow_set:
                return 1.0, {"match_type": "empty_strings"}
            
            jaccard = len(prod_set & shadow_set) / len(prod_set | shadow_set)
            details["match_type"] = "jaccard"
            details["jaccard"] = round(jaccard, 4)
            return jaccard, details
        
        # Numeric comparison
        if isinstance(prod_output, (int, float)):
            if prod_output == 0:
                return (1.0 if shadow_output == 0 else 0.0), {"match_type": "numeric"}
            diff = abs(prod_output - shadow_output) / prod_output
            similarity = max(0, 1 - diff)
            details["match_type"] = "numeric"
            details["relative_diff"] = round(diff, 4)
            return similarity, details
        
        # Fallback
        return 0.5, {"match_type": "unknown"}
    
    def _compare_lists(self, a: List, b: List) -> Tuple[float, Dict]:
        """Compare two lists."""
        if not a and not b:
            return 1.0, {"match_type": "empty_lists"}
        
        # Length check
        if len(a) != len(b):
            return min(len(a), len(b)) / max(len(a), len(b)), {
                "match_type": "list_length_diff",
                "prod_len": len(a),
                "shadow_len": len(b)
            }
        
        # Element-wise comparison
        matches = 0
        element_diffs = []
        for i, (ae, be) in enumerate(zip(a, b)):
            elem_sim, _ = self._default_compare(ae, be)
            if elem_sim >= self.similarity_threshold:
                matches += 1
            else:
                element_diffs.append(index=i, similarity=elem_sim)
        
        similarity = matches / len(a)
        return similarity, {
            "match_type": "list_elements",
            "matches": matches,
            "total": len(a),
            "element_diffs": element_diffs[:5]  # Limit diffs
        }
    
    def _compare_dicts(self, a: Dict, b: Dict) -> Tuple[float, Dict]:
        """Compare two dicts."""
        keys_a = set(a.keys())
        keys_b = set(b.keys())
        
        if not keys_a and not keys_b:
            return 1.0, {"match_type": "empty_dicts"}
        
        # Key overlap
        common_keys = keys_a & keys_b
        only_a = keys_a - keys_b
        only_b = keys_b - keys_a
        
        if not common_keys:
            return 0.0, {
                "match_type": "no_overlap",
                "keys_only_a": list(only_a)[:10],
                "keys_only_b": list(only_b)[:10]
            }
        
        # Value comparison for common keys
        key_matches = 0
        value_diffs = []
        for key in common_keys:
            val_sim, _ = self._default_compare(a[key], b[key])
            if val_sim >= self.similarity_threshold:
                key_matches += 1
            else:
                value_diffs.append({"key": key, "similarity": val_sim})
        
        key_score = len(common_keys) / max(len(keys_a), len(keys_b))
        value_score = key_matches / len(common_keys) if common_keys else 0
        
        # Combined score (70% values, 30% key overlap)
        similarity = value_score * 0.7 + key_score * 0.3
        
        return similarity, {
            "match_type": "dict",
            "key_overlap": len(common_keys),
            "prod_keys": len(keys_a),
            "shadow_keys": len(keys_b),
            "value_matches": key_matches,
            "value_diffs": value_diffs[:5],
            "missing_keys_a": list(only_a)[:5],
            "missing_keys_b": list(only_b)[:5]
        }
    
    def compare(
        self,
        task: Any,
        prod_executor: Callable[[Any], Any],
        shadow_executor: Callable[[Any], Any],
        prod_version: str,
        shadow_version: str,
        compare_fn: Optional[Callable[[Any, Any], Tuple[float, Dict]]] = None
    ) -> ComparisonResult:
        """
        Execute both versions and compare results.
        
        Returns:
            ComparisonResult with similarity analysis
        """
        task_hash = self._compute_task_hash(task)
        task_preview = self._create_preview(task)
        timestamp = datetime.now().isoformat()
        
        # Execute production
        prod_start = time.time()
        prod_exception = None
        try:
            prod_output = prod_executor(task)
        except Exception as e:
            prod_output = f"__ERROR__: {type(e).__name__}: {str(e)}"
            prod_exception = e
            
        prod_end = time.time()
        prod_metrics = ExecutionMetrics(
            start_time=prod_start,
            end_time=prod_end,
            duration_ms=int((prod_end - prod_start) * 1000)
        )
        
        # Execute shadow
        shadow_start = time.time()
        shadow_exception = None
        try:
            shadow_output = shadow_executor(task)
        except Exception as e:
            shadow_output = f"__ERROR__: {type(e).__name__}: {str(e)}"
            shadow_exception = e
            
        shadow_end = time.time()
        shadow_metrics = ExecutionMetrics(
            start_time=shadow_start,
            end_time=shadow_end,
            duration_ms=int((shadow_end - shadow_start) * 1000)
        )
        
        # Compare results
        if compare_fn:
            similarity, details = compare_fn(prod_output, shadow_output)
        else:
            similarity, details = self._default_compare(prod_output, shadow_output)
        
        # Calculate performance delta
        perf_delta = shadow_metrics.duration_ms - prod_metrics.duration_ms
        
        # Acceptance: similarity above threshold AND no exceptions
        accepted = (
            similarity >= self.similarity_threshold and
            prod_exception is None and
            shadow_exception is None
        )
        
        # Add exception details if any
        if prod_exception or shadow_exception:
            details["exceptions"] = {
                "prod": prod_exception.__class__.__name__ if prod_exception else None,
                "shadow": shadow_exception.__class__.__name__ if shadow_exception else None
            }
        
        result = ComparisonResult(
            task_hash=task_hash,
            task_preview=task_preview,
            prod_version=prod_version,
            shadow_version=shadow_version,
            prod_output=prod_output,
            shadow_output=shadow_output,
            prod_metrics=prod_metrics,
            shadow_metrics=shadow_metrics,
            similarity_score=similarity,
            performance_delta_ms=perf_delta,
            accepted=accepted,
            divergence_details=details,
            timestamp=timestamp
        )
        
        # Log result
        self._log_result(result)
        
        return result
    
    def _log_result(self, result: ComparisonResult):
        """Write comparison result to log file."""
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(result.to_dict()) + "\n")
    
    def get_recent_results(
        self,
        shadow_version: str,
        limit: int = 100
    ) -> List[ComparisonResult]:
        """Get recent comparison results for a shadow version."""
        results = []
        
        # Check recent log files
        for log_file in sorted(self.log_dir.glob("*.jsonl"), reverse=True)[:3]:
            with open(log_file) as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("shadow_version") == shadow_version:
                        # Reconstruct from dict (partial)
                        results.append(data)
                        if len(results) >= limit:
                            break
        
        return results
    
    def get_acceptance_stats(
        self,
        shadow_version: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get acceptance statistics for shadow version."""
        results = self.get_recent_results(shadow_version, limit=1000)
        
        if not results:
            return {
                "version": shadow_version,
                "total_tests": 0,
                "accepted": 0,
                "rejected": 0,
                "acceptance_rate": 0.0,
                "avg_similarity": 0.0,
                "avg_latency_delta_ms": 0
            }
        
        accepted = sum(1 for r in results if r.get("accepted"))
        similarities = [r.get("similarity_score", 0) for r in results]
        deltas = [r.get("performance_delta_ms", 0) for r in results]
        
        return {
            "version": shadow_version,
            "total_tests": len(results),
            "accepted": accepted,
            "rejected": len(results) - accepted,
            "acceptance_rate": accepted / len(results),
            "avg_similarity": sum(similarities) / len(similarities),
            "avg_latency_delta_ms": sum(deltas) / len(deltas) if deltas else 0
        }


# Verification test
if __name__ == "__main__":
    print("=" * 60)
    print("SHADOW RUNNER - VERIFICATION TEST")
    print("=" * 60)
    
    # Initialize runner
    print("\n[1] Initializing ShadowRunner...")
    runner = ShadowRunner(similarity_threshold=0.85)
    
    # Test 1: Identical outputs
    print("\n[2] Test: Identical outputs...")
    result = runner.compare(
        task={"query": "search memory"},
        prod_executor=lambda t: ["result1", "result2"],
        shadow_executor=lambda t