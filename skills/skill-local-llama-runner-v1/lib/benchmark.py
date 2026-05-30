#!/usr/bin/env python3
"""
Benchmark Runner - Performance testing for local models.

Compares local vs cloud for:
- Response time
- Token throughput
- Quality metrics
"""

import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    profile: str
    model: str
    prompts_tested: int
    avg_latency_ms: float
    tokens_per_sec: float
    total_tokens: int
    errors: int
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class BenchmarkRunner:
    """Benchmark local model performance."""
    
    TEST_PROMPTS = [
        "Summarize this: Local models are great for batch processing.",
        "Classify: "Hello world" as greeting or farewell",
        "Extract: Name John, Age 30 from 'John is 30 years old'",
        "List 3 colors that are not primary colors",
        "What is 2+2?", 
    ]
    
    def __init__(self, runner, save_dir: Optional[Path] = None):
        from .llama_runner import LocalLlamaRunner
        self.runner: LocalLlamaRunner = runner
        self.save_dir = save_dir or Path.home() / ".openclaw/logs/benchmarks"
        self.save_dir.mkdir(parents=True, exist_ok=True)
    
    def run_benchmark(self, max_tokens: int = 100) -> BenchmarkResult:
        """Run benchmark tests."""
        latencies = []
        total_tokens = 0
        errors = 0
        
        for prompt in self.TEST_PROMPTS:
            try:
                result = self.runner.complete(prompt, max_tokens=max_tokens)
                latencies.append(result.wall_time_ms)
                total_tokens += result.completion_tokens
            except Exception as e:
                errors += 1
                print(f"Benchmark error: {e}")
        
        # Calculate stats
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            total_time_sec = sum(latencies) / 1000
            tokens_per_sec = total_tokens / total_time_sec if total_time_sec > 0 else 0
        else:
            avg_latency = 0
            tokens_per_sec = 0
        
        result = BenchmarkResult(
            profile=self.runner.profile_name,
            model=self.runner.profile.get("model", "unknown"),
            prompts_tested=len(self.TEST_PROMPTS),
            avg_latency_ms=avg_latency,
            tokens_per_sec=tokens_per_sec,
            total_tokens=total_tokens,
            errors=errors,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%S")
        )
        
        self._save_result(result)
        return result
    
    def _save_result(self, result: BenchmarkResult):
        """Save benchmark result."""
        file = self.save_dir / f"benchmark_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"Benchmark saved to: {file}")


if __name__ == "__main__":
    print("Benchmark module - import and use with runner instance")
