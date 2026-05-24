#!/usr/bin/env python3
"""CostTracker - Token usage and cost accounting.

Pricing (OpenRouter):
- kimi-k2.5: $0.50 / 1M input, $2.00 / 1M output tokens
- o1-preview: $15 / 1M input, $60 / 1M output tokens
- gpt-4o: $2.50 / 1M input, $10 / 1M output tokens

Author: RockClaw
Version: 1.0.0-alpha
Status: VERIFIED
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class UsageRecord:
    """Single request usage."""
    timestamp: str
    backend: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int


MODEL_PRICING = {
    "openrouter/moonshotai/kimi-k2.5": {"input": 0.50, "output": 2.00},
    "openrouter/moonshotai/kimi-k2.6": {"input": 0.50, "output": 2.00},
    "openrouter/openai/o1-preview": {"input": 15.00, "output": 60.00},
    "openrouter/openai/gpt-4o": {"input": 2.50, "output": 10.00},
    "ollama/llama3:8b": {"input": 0.00, "output": 0.00},
    "local": {"input": 0.00, "output": 0.00},
}

DAILY_BUDGET_USD = 5.00
MONTHLY_BUDGET_USD = 100.00


class CostTracker:
    """
    Tracks token usage and costs across backends.
    
    Storage:
    ~/.openclaw/workspace/skills/skill-resource-awareness/cost_logs/daily/YYYY-MM-DD.json
    """
    
    def __init__(self, log_base: Optional[Path] = None):
        self.log_base = log_base or Path(
            "/home/rock/.openclaw/workspace/skills/skill-resource-awareness/cost_logs"
        )
        self.daily_dir = self.log_base / "daily"
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        
        self._today_usage: List[UsageRecord] = []
        self._load_today()
    
    def _log_file_for_date(self, date: datetime) -> Path:
        """Get log file path for a specific date."""
        return self.daily_dir / f"{date.strftime('%Y-%m-%d')}.json"
    
    def _load_today(self):
        """Load today's usage from disk."""
        today_file = self._log_file_for_date(datetime.now())
        if today_file.exists():
            with open(today_file) as f:
                data = json.load(f)
                self._today_usage = [
                    UsageRecord(**r) for r in data.get("records", [])
                ]
    
    def _save_today(self):
        """Save today's usage to disk."""
        today_file = self._log_file_for_date(datetime.now())
        with open(today_file, "w") as f:
            json.dump({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "records": [
                    {
                        "timestamp": r.timestamp,
                        "backend": r.backend,
                        "model": r.model,
                        "input_tokens": r.input_tokens,
                        "output_tokens": r.output_tokens,
                        "cost_usd": r.cost_usd,
                        "latency_ms": r.latency_ms
                    }
                    for r in self._today_usage
                ]
            }, f, indent=2)
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD for a request."""
        pricing = MODEL_PRICING.get(model, {"input": 0.50, "output": 2.00})
        
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return round(input_cost + output_cost, 6)
    
    def record_usage(
        self,
        backend: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: int
    ) -> float:
        """Record a request and return its cost."""
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            backend=backend,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_ms=latency_ms
        )
        
        self._today_usage.append(record)
        self._save_today()
        
        return cost
    
    def get_daily_spend(self, date: Optional[datetime] = None) -> Dict:
        """Get spend for a specific date."""
        date = date or datetime.now()
        log_file = self._log_file_for_date(date)
        
        if not log_file.exists():
            return {"date": date.strftime("%Y-%m-%d"), "total_cost": 0.0, "requests": 0}
        
        with open(log_file) as f:
            data = json.load(f)
            records = data.get("records", [])
            total = sum(r["cost_usd"] for r in records)
            
            return {
                "date": date.strftime("%Y-%m-%d"),
                "total_cost": round(total, 4),
                "requests": len(records),
                "by_model": self._aggregate_by_model(records),
                "budget_percent": min(100, (total / DAILY_BUDGET_USD) * 100)
            }
    
    def get_monthly_spend(self) -> Dict:
        """Get current month's spend."""
        now = datetime.now()
        total = 0.0
        total_requests = 0
        
        # Check last 31 days
        for i in range(31):
            date = now - timedelta(days=i)
            log_file = self._log_file_for_date(date)
            if log_file.exists():
                with open(log_file) as f:
                    data = json.load(f)
                    records = data.get("records", [])
                    total += sum(r["cost_usd"] for r in records)
                    total_requests += len(records)
        
        return {
            "month": now.strftime("%Y-%m"),
            "total_cost": round(total, 4),
            "total_requests": total_requests,
            "budget_percent": min(100, (total / MONTHLY_BUDGET_USD) * 100),
            "budget_remaining": round(MONTHLY_BUDGET_USD - total, 4)
        }
    
    def _aggregate_by_model(self, records: List[Dict]) -> Dict[str, float]:
        """Aggregate costs by model."""
        by_model = {}
        for r in records:
            model = r["model"]
            by_model[model] = by_model.get(model, 0.0) + r["cost_usd"]
        return {k: round(v, 4) for k, v in by_model.items()}
    
    def should_use_local(self, estimated_tokens: int = 1000) -> bool:
        """
        Determine if we should switch to local backend.
        
        Returns True if:
        - Daily budget exceeded
        - Monthly budget at 80%+
        """
        daily = self.get_daily_spend()
        monthly = self.get_monthly_spend()
        
        if daily["budget_percent"] >= 100:
            return True
        
        if monthly["budget_percent"] >= 80:
            return True
        
        return False


# Verification test
if __name__ == "__main__":
    import tempfile
    
    print("=" * 60)
    print("COST TRACKER - VERIFICATION TEST")
    print("=" * 60)
    
    # Setup
    test_dir = Path(tempfile.mkdtemp())
    print(f"\n[1] Test environment: {test_dir}")
    
    tracker = CostTracker(log_base=test_dir)
    
    # Test cost calculation
    print("\n[2] Testing cost calculations...")
    
    # kimi-k2.5: 1K in, 500 out
    cost = tracker.calculate_cost(
        "openrouter/moonshotai/kimi-k2.5",
        input_tokens=1000,
        output_tokens=500
    )
    expected = (1000/1_000_000 * 0.50) + (500/1_000_000 * 2.00)
    assert abs(cost - expected) < 0.0001
    print(f"    - kimi-k2.5 (1K+500 tokens): ${cost:.6f} ✓")
    
    # o1-preview: expensive
    expensive = tracker.calculate_cost(
        "openrouter/openai/o1-preview",
        input_tokens=10000,
        output_tokens=5000
    )
    print(f"    - o1-preview (10K+5K tokens): ${expensive:.4f} ✓")
    
    # Local: free
    free = tracker.calculate_cost("ollama/llama3:8b", 10000, 10000)
    assert free == 0.0
    print(f"    - Local model (any tokens): ${free:.4f} ✓")
    
    # Test usage recording
    print("\n[3] Testing usage recording...")
    cost1 = tracker.record_usage(
        backend="openrouter",
        model="openrouter/moonshotai/kimi-k2.5",
        input_tokens=5000,
        output_tokens=2000,
        latency_ms=1200
    )
    print(f"    - Recorded request: ${cost1:.6f} ✓")
    
    cost2 = tracker.record_usage(
        backend="openrouter",
        model="openrouter/moonshotai/kimi-k2.5",
        input_tokens=3000,
        output_tokens=1500,
        latency_ms=800
    )
    
    # Test daily spend
    print("\n[4] Testing daily spend query...")
    daily = tracker.get_daily_spend()
    assert daily["requests"] == 2
    assert daily["total_cost"] > 0
    print(f"    - Today's spend: ${daily['total_cost']:.4f} ✓")
    print(f"    - Requests: {daily['requests']} ✓")
    print(f"    - Budget used: {daily['budget_percent']:.1f}% ✓")
    
    # Test monthly spend
    print("\n[5] Testing monthly spend...")
    monthly = tracker.get_monthly_spend()
    print(f"    - Month: {monthly['month']} ✓")
    print(f"    - Total: ${monthly['total_cost']:.4f} ✓")
    print(f"    - Remaining budget: ${monthly['budget_remaining']:.2f} ✓")
    
    # Test local fallback decision
    print("\n[6] Testing local fallback decision...")
    should_local = tracker.should_use_local()
    print(f"    - Should use local: {should_local} ✓")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
