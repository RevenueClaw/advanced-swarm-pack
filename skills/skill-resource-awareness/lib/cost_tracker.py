#!/usr/bin/env python3
"""
Cost Tracker - v1.4.0 Enhanced with local/cloud cost optimization.

Tracks costs and routes between OpenRouter and local models.

Author: RockClaw
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class UsageRecord:
    """Single usage record."""
    timestamp: str
    provider: str  # openrouter, local_llama, ollama
    model: str
    prompt_tokens: int
    completion_tokens: int
    wall_time_ms: int
    task_type: str
    estimated_cost: float
    

class CostTracker:
    """
    Cost tracking with v1.4.0 enhancements:
    - Local vs cloud cost comparison
    - Estimated savings tracking
    - Routing decision metrics
    """
    
    # Estimated costs per 1K tokens (USD)
    CLOUD_COSTS = {
        "kimi-k2.5": 0.00125,
        "gpt-4o": 0.00375,
        "claude-sonnet": 0.00300,
        "llama3-70b": 0.00064,
    }
    
    LOCAL_COST = 0.0  # Assumed negligible
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path.home() / ".openclaw/logs/costs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.daily_usage: Dict[str, List[UsageRecord]] = {}
        self.local_tokens_saved = 0
        self.cloud_tokens_used = 0
        self.estimated_savings = 0.0
        
        # New v1.4.0 metrics
        self.routing_stats = {
            "local_routed": 0,
            "cloud_routed": 0,
            "escalations": 0,
            "local_failures": 0,
        }
    
    def record_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        wall_time_ms: int,
        task_type: str = "unknown"
    ) -> Dict:
        """
        Record usage and return metrics.
        """
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            wall_time_ms=wall_time_ms,
            task_type=task_type,
            estimated_cost=self._estimate_cost(model, completion_tokens)
        )
        
        # Track stats
        day = datetime.now().strftime("%Y-%m-%d")
        if day not in self.daily_usage:
            self.daily_usage[day] = []
        self.daily_usage[day].append(record)
        
        if provider.startswith("local"):
            self.local_tokens_saved += completion_tokens
        else:
            self.cloud_tokens_used += completion_tokens
        
        # Calculate savings
        cloud_cost = self._estimate_cost("kimi-k2.5", completion_tokens)
        local_cost = 0.0
        self.estimated_savings += (cloud_cost - local_cost)
        
        self._log_record(record)
        
        return {
            "tokens": completion_tokens,
            "estimated_cost": record.estimated_cost,
            "provider": provider,
        }
    
    def _estimate_cost(self, model: str, tokens: int) -> float:
        """Estimate cost for given model and tokens."""
        cost_per_1k = self.CLOUD_COSTS.get(model, 0.001)  # Default safe estimate
        return (tokens / 1000) * cost_per_1k
    
    def _log_record(self, record: UsageRecord):
        """Log record to file."""
        log_file = self.log_dir / f"usage_{datetime.now().strftime('%Y-%m')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(asdict(record)) + '\n')
    
    def should_use_local(self) -> Tuple[bool, str]:
        """
        v1.4.0: Decide whether to use local model.
        
        Returns (should_use_local, reason)
        """
        # Simple heuristic: always prefer local for eligible tasks
        # More sophisticated logic would check:
        # - Current usage vs budget
        # - Time of day (local preferred overnight)
        # - Task type
        
        return True, "local_first_policy"
    
    def get_local_savings_report(self) -> Dict:
        """
        v1.4.0: Get estimated savings from local model usage.
        """
        return {
            "local_tokens_processed": self.local_tokens_saved,
            "cloud_tokens_processed": self.cloud_tokens_used,
            "estimated_cloud_cost_avoided": self.estimated_savings,
            "routing_decisions": self.routing_stats,
            "local_percentage": self.local_tokens_saved / (self.local_tokens_saved + self.cloud_tokens_used) * 100
            if (self.local_tokens_saved + self.cloud_tokens_used) > 0 else 0
        }
    
    def get_daily_summary(self, days: int = 7) -> List[Dict]:
        """Get daily summaries for last N days."""
        summaries = []
        date = datetime.now()
        
        for _ in range(days):
            day_str = date.strftime("%Y-%m-%d")
            records = self.daily_usage.get(day_str, [])
            
            total_tokens = sum(r.completion_tokens for r in records)
            total_cost = sum(r.estimated_cost for r in records)
            local_count = sum(1 for r in records if r.provider.startswith("local"))
            cloud_count = len(records) - local_count
            
            summaries.append({
                "date": day_str,
                "total_requests": len(records),
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 4),
                "local_requests": local_count,
                "cloud_requests": cloud_count,
            })
            
            date -= timedelta(days=1)
        
        return summaries


# Test
if __name__ == "__main__":
    tracker = CostTracker()
    
    # Simulate usage
    tracker.record_usage("openrouter", "kimi-k2.5", 1000, 500, 1000, "summarization")
    tracker.record_usage("local_llama", "qwen3-8b", 500, 300, 2000, "classification")
    
    print("Cost tracking test:")
    print(json.dumps(tracker.get_local_savings_report(), indent=2))
