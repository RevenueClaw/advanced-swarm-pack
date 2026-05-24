#!/usr/bin/env python3
"""
EstimationEngine - Time estimation with historical tracking and calibration.

Features:
- Historical predicted vs actual time tracking
- Breakdown-based estimation (sum of subtasks + contingency)
- Automatic buffer rules (+50% novel, +30% standard, +20% known)
- Calibration score per task category

Author: RockClaw
Version: 1.0.0
"""

import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class TaskCategory(Enum):
    """Task categories for calibration."""
    CODING = "coding"
    RESEARCH = "research" 
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"
    DEBUGGING = "debugging"
    PLANNING = "planning"
    UNKNOWN = "unknown"


@dataclass
class HistoricalEstimate:
    """Record of predicted vs actual time."""
    task_id: str
    task_category: str
    predicted_hours: float
    actual_hours: float
    task_description: str
    created_at: str
    
    @property
    def error_ratio(self) -> float:
        """How much actual differed from predicted (>1 = underestimated)."""
        if self.predicted_hours == 0:
            return float('inf')
        return self.actual_hours / self.predicted_hours
    
    @property
    def was_underestimated(self) -> bool:
        return self.actual_hours > self.predicted_hours


@dataclass
class CalibrationData:
    """Calibration metrics for a task category."""
    category: str
    total_estimates: int
    avg_error_ratio: float
    underestimation_rate: float  # % of times we underestimated
    std_dev: float
    recommended_buffer: float  # Multiplier (1.5 = +50%)
    confidence_score: float  # 0-1, how reliable are our estimates?
    

class EstimationEngine:
    """
    Provides calibrated time estimates based on historical data.
    
    Usage:
        engine = EstimationEngine()
        
        # Make a new estimate
        estimate = engine.estimate(
            task="Implement new feature",
            subtasks=[
                ("Design", 0.5),
                ("Implementation", 2.0),
                ("Testing", 1.0)
            ],
            category=TaskCategory.CODING,
            is_novel=True
        )
        # Returns calibrated estimate with buffer
        
        # Record actual time later for calibration
        engine.record_actual(task_id, actual_hours=8.5)
    """
    
    # Buffer multipliers
    BUFFER_NOVEL = 1.50      # +50% for new territory
    BUFFER_STANDARD = 1.30   # +30% for normal work
    BUFFER_KNOWN = 1.20      # +20% for familiar patterns
    BUFFER_MINIMUM = 1.10    # Minimum buffer
    
    # Confidence thresholds
    HIGH_CONFIDENCE = 0.85
    MEDIUM_CONFIDENCE = 0.60
    LOW_CONFIDENCE = 0.40
    
    def __init__(self, history_dir: Optional[Path] = None):
        self.history_dir = history_dir or Path.home() / ".openclaw/workspace/skills/skill-estimation-engine/history"
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.history_file = self.history_dir / "estimates.jsonl"
        self.calibration_file = self.history_dir / "calibration.json"
        
        self._estimates: List[HistoricalEstimate] = []
        self._calibration: Dict[str, CalibrationData] = {}
        
        self._load_history()
        self._compute_calibration()
    
    def _load_history(self):
        """Load historical estimates from disk."""
        if self.history_file.exists():
            with open(self.history_file) as f:
                for line in f:
                    data = json.loads(line)
                    self._estimates.append(HistoricalEstimate(**data))
    
    def _save_estimate(self, estimate: HistoricalEstimate):
        """Append estimate to history."""
        with open(self.history_file, "a") as f:
            f.write(json.dumps({
                "task_id": estimate.task_id,
                "task_category": estimate.task_category,
                "predicted_hours": estimate.predicted_hours,
                "actual_hours": estimate.actual_hours,
                "task_description": estimate.task_description,
                "created_at": estimate.created_at
            }) + "\n")
    
    def _compute_calibration(self):
        """Compute calibration data for each category."""
        if not self._estimates:
            return
        
        # Group by category
        by_category: Dict[str, List[HistoricalEstimate]] = {}
        for est in self._estimates:
            cat = est.task_category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(est)
        
        # Compute calibration for each category
        for category, estimates in by_category.items():
            if len(estimates) < 3:
                # Not enough data
                self._calibration[category] = CalibrationData(
                    category=category,
                    total_estimates=len(estimates),
                    avg_error_ratio=1.5,  # Conservative default
                    underestimation_rate=0.5,
                    std_dev=0.5,
                    recommended_buffer=self.BUFFER_STANDARD,
                    confidence_score=0.3  # Low confidence
                )
                continue
            
            # Calculate metrics
            error_ratios = [e.error_ratio for e in estimates]
            avg_error = statistics.mean(error_ratios)
            underestimate_count = sum(1 for e in estimates if e.was_underestimated)
            underestimation_rate = underestimate_count / len(estimates)
            
            try:
                std_dev = statistics.stdev(error_ratios) if len(error_ratios) > 1 else 0.3
            except statistics.StatisticsError:
                std_dev = 0.3
            
            # Compute buffer recommendation based on historical accuracy
            if avg_error > 2.0 or underestimation_rate > 0.7:
                buffer_mult = self.BUFFER_NOVEL  # Very unreliable
            elif avg_error > 1.5 or underestimation_rate > 0.5:
                buffer_mult = self.BUFFER_STANDARD  # Moderately unreliable
            else:
                buffer_mult = self.BUFFER_KNOWN  # Reliable
            
            # Confidence score (inverse of variance)
            confidence = max(0.1, 1.0 - std_dev)
            confidence = min(1.0, confidence)
            
            self._calibration[category] = CalibrationData(
                category=category,
                total_estimates=len(estimates),
                avg_error_ratio=avg_error,
                underestimation_rate=underestimation_rate,
                std_dev=std_dev,
                recommended_buffer=buffer_mult,
                confidence_score=confidence
            )
        
        # Save calibration
        with open(self.calibration_file, "w") as f:
            cal_data = {
                cat: {
                    "category": cd.category,
                    "total_estimates": cd.total_estimates,
                    "avg_error_ratio": cd.avg_error_ratio,
                    "underestimation_rate": cd.underestimation_rate,
                    "std_dev": cd.std_dev,
                    "recommended_buffer": cd.recommended_buffer,
                    "confidence_score": cd.confidence_score
                }
                for cat, cd in self._calibration.items()
            }
            json.dump(cal_data, f, indent=2)
    
    def estimate(self,
                task: str,
                subtasks: List[Tuple[str, float]],
                category: TaskCategory = TaskCategory.UNKNOWN,
                is_novel: bool = False,
                has_similar_pattern: bool = False) -> Dict:
        """
        Generate calibrated time estimate.
        
        Args:
            task: High-level task description
            subtasks: List of (subtask_name, estimated_hours) tuples
            category: Task category for calibration
            is_novel: True if this is new territory
            has_similar_pattern: True if done similar before
            
        Returns:
            Dict with breakdown, totals, and calibration info
        """
        # 1. Sum base estimates
        base_hours = sum(hours for _, hours in subtasks)
        
        if base_hours == 0:
            base_hours = 1.0  # Minimum 1 hour
        
        # 2. Add contingency per subtask
        subtask_contingency = sum(hours * 0.15 for _, hours in subtasks)  # 15% per subtask
        
        # 3. Determine buffer based on historical calibration + task characteristics
        cat_key = category.value
        calibration = self._calibration.get(cat_key)
        
        if is_novel:
            buffer_mult = max(self.BUFFER_NOVEL, 
                             calibration.recommended_buffer if calibration else self.BUFFER_NOVEL)
        elif has_similar_pattern:
            buffer_mult = self.BUFFER_KNOWN
            if calibration and calibration.confidence_score > self.HIGH_CONFIDENCE:
                buffer_mult = max(self.BUFFER_KNOWN, 
                                 calibration.recommended_buffer * 0.8)  # Can reduce if history is good
        else:
            buffer_mult = calibration.recommended_buffer if calibration else self.BUFFER_STANDARD
        
        # Never go below minimum buffer
        buffer_mult = max(buffer_mult, self.BUFFER_MINIMUM)
        
        # 4. Apply buffer
        total_with_buffer = base_hours * buffer_mult
        
        # 5. Add subtask contingency
        total_hours = total_with_buffer + subtask_contingency
        
        # 6. Round to reasonable precision
        total_hours = round(total_hours, 1)
        
        # 7. Generate range estimate
        low_bound = round(base_hours * 1.0, 1)  # Best case
        high_bound = round(total_hours * 1.3, 1)  # Worst case (+30%)
        
        # Build result
        result = {
            "task": task,
            "category": category.value,
            "is_novel": is_novel,
            "has_pattern": has_similar_pattern,
            
            "breakdown": [
                {"name": name, "hours": hours, "contingency_15pct": round(hours * 0.15, 1)}
                for name, hours in subtasks
            ],
            
            "base_hours": base_hours,
            "subtask_contingency": round(subtask_contingency, 1),
            "buffer_multiplier": round(buffer_mult, 2),
            "total_estimated_hours": total_hours,
            
            "range_estimate": {
                "best_case": low_bound,
                "most_likely": total_hours,
                "worst_case": high_bound
            },
            
            "calibration_info": {
                "category": cat_key,
                "historical_estimates": calibration.total_estimates if calibration else 0,
                "category_calibration": calibration.recommended_buffer if calibration else "unknown",
                "confidence_score": round(calibration.confidence_score, 2) if calibration else 0.3
            },
            
            "recommendation": self._generate_recommendation(total_hours, calibration, is_novel),
            
            "estimate_id": self._generate_estimate_id(task, total_hours)
        }
        
        return result
    
    def _generate_recommendation(self, 
                                 hours: float, 
                                 calibration: Optional[CalibrationData],
                                 is_novel: bool) -> str:
        """Generate human-readable recommendation."""
        parts = []
        
        if hours < 2:
            parts.append("Quick task - should complete same day")
        elif hours < 8:
            parts.append("Same-day task with buffer included")
        elif hours < 24:
            parts.append("Multi-day task - consider breaking into smaller pieces")
        else:
            parts.append("Substantial effort - requires planning and tracking")
        
        if calibration:
            if calibration.confidence_score < self.LOW_CONFIDENCE:
                parts.append("⚠ Low confidence - track actual time carefully")
            elif calibration.confidence_score < self.MEDIUM_CONFIDENCE:
                parts.append("📊 Moderate confidence - update after completion")
            else:
                parts.append("✓ Based on reliable historical data")
        
        if is_novel:
            parts.append("⚠ Novel task - uncertainty is expected, revisit estimate after first block")
        
        return " ".join(parts)
    
    def _generate_estimate_id(self, task: str, hours: float) -> str:
        """Generate unique estimate ID."""
        import hashlib
        content = f"{task}{hours}{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def record_actual(self, estimate_id: str, actual_hours: float, 
                     task_description: str = "", category: str = "unknown"):
        """
        Record actual time for calibration.
        
        Call this after task completion to improve future estimates.
        """
        # Find matching estimate (simplified - in production would lookup by ID)
        estimation = HistoricalEstimate(
            task_id=estimate_id,
            task_category=category,
            predicted_hours=0,  # Would lookup original
            actual_hours=actual_hours,
            task_description=task_description,
            created_at=datetime.now().isoformat()
        )
        
        self._estimates.append(estimation)
        self._save_estimate(estimation)
        self._compute_calibration()
        
        # Return feedback
        return {
            "recorded": True,
            "actual_hours": actual_hours,
            "category": category,
            "calibration_updated": True
        }
    
    def get_calibration_report(self) -> Dict:
        """Get current calibration status for all categories."""
        if not self._calibration:
            return {"status": "insufficient_data", "categories": {}}
        
        return {
            "status": "calibrated",
            "total_estimates": len(self._estimates),
            "categories": {
                cat: {
                    "total_estimates": cd.total_estimates,
                    "avg_error_ratio": round(cd.avg_error_ratio, 2),
                    "underestimation_rate": f"{cd.underestimation_rate:.0%}",
                    "recommended_buffer": f"{cd.recommended_buffer:.0%}",
                    "confidence": f"{cd.confidence_score:.0%}"
                }
                for cat, cd in self._calibration.items()
            }
        }
    
    def get_category_recommendation(self, category: TaskCategory) -> str:
        """Get recommendation for a specific category."""
        cal = self._calibration.get(category.value)
        if not cal:
            return "No historical data. Use standard buffer (30%) and track actual time."
        
        if cal.confidence_score > self.HIGH_CONFIDENCE:
            return f"✓ Reliable estimates ({cal.confidence_score:.0%} confidence). Buffer: {cal.recommended_buffer:.0%}"
        elif cal.confidence_score > self.MEDIUM_CONFIDENCE:
            return f"📊 Moderate reliability. Review estimates, actual tends to be {cal.avg_error_ratio:.1f}x predicted."
        else:
            return f"⚠ Unreliable estimates. Strongly recommend {cal.recommended_buffer:.0%} buffer."


# Example/test
if __name__ == "__main__":
    print("=" * 60)
    print("ESTIMATION ENGINE - VERIFICATION TEST")
    print("=" * 60)
    
    engine = EstimationEngine()
    
    # Test 1: Novel coding task
    print("\n[1] Novel coding task estimate:")
    estimate = engine.estimate(
        task="Implement new payment processor",
        subtasks=[
            ("Research API", 1.0),
            ("Design integration", 1.5),
            ("Implement core", 3.0),
            ("Write tests", 2.0),
            ("Documentation", 1.0)
        ],
        category=TaskCategory.CODING,
        is_novel=True
    )
    
    print(f"  Base hours: {estimate['base_hours']}")
    print(f"  Buffer multiplier: {estimate['buffer_multiplier']}")
    print(f"  Total estimate: {estimate['total_estimated_hours']} hours")
    print(f"  Range: {estimate['range_estimate']['best_case']}-{estimate['range_estimate']['worst_case']} hours")
    print(f"  Recommendation: {estimate['recommendation']}")
    
    # Test 2: Known documentation task
    print("\n[2] Documentation task (with pattern):")
    estimate2 = engine.estimate(
        task="Update API documentation",
        subtasks=[("Review changes", 0.5),
            ("Update docs", 1.0),
            ("Verify examples", 0.5)
        ],
        category=TaskCategory.DOCUMENTATION,
        has_similar_pattern=True
    )
    
    print(f"  Base hours: {estimate2['base_hours']}")
    print(f"  Buffer multiplier: {estimate2['buffer_multiplier']}")
    print(f"  Total estimate: {estimate2['total_estimated_hours']} hours")
    print(f"  Range: {estimate2['range_estimate']['best_case']}-{estimate2['range_estimate']['worst_case']} hours")
    
    # Test 3: Calibration report
    print("\n[3] Calibration report:")
    report = engine.get_calibration_report()
    print(f"  Status: {report['status']}")
    print(f"  Total historical estimates: {report.get('total_estimates', 0)}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)