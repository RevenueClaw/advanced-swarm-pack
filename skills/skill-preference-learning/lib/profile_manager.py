#!/usr/bin/env python3
"""ProfileManager - Personalizes agent behavior based on user habits.

Learned Attributes:
- Communication: verbosity, detail level, code-first vs explain-first
- Risk Tolerance: automation level, confirmation requirements, rollback comfort
- Pace: response speed, async preferences, batching preferences
- Workflows: preferred patterns, tool combinations, success rates

Confidence Scoring:
- Observations increase confidence gradually
- Explicit feedback provides high confidence
- Contradictions reduce confidence with decay

Author: RockClaw
Version: 1.0.0-alpha
Status: VERIFIED (basic structure)
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class LearnedTrait:
    """A learned user preference with confidence tracking."""
    name: str
    value: Any
    confidence: float  # 0.0 to 1.0
    source: str        # "observation", "explicit_feedback", "inferred"
    first_seen: str    # ISO timestamp
    last_updated: str  # ISO timestamp
    observation_count: int = 0
    contradictions: int = 0
    
    def strengthen(self, amount: float = 0.05):
        """Increase confidence from positive observation."""
        self.confidence = min(1.0, self.confidence + amount)
        self.observation_count += 1
        self.last_updated = datetime.now().isoformat()
    
    def contradict(self, new_value: Any, amount: float = 0.1):
        """Reduce confidence when preference changes."""
        self.contradictions += 1
        self.confidence = max(0.1, self.confidence - amount)
        self.value = new_value
        self.last_updated = datetime.now().isoformat()


class ProfileManager:
    """
    Manages user profile with learned preferences.
    
    Stored in:
    ~/.openclaw/workspace/skills/skill-preference-learning/preferences/{user_id}-profile.json
    """
    
    CONFIDENCE_DECAY_DAYS = 30  # Confidence decays after inactivity
    MIN_CONFIDENCE_FOR_APPLICATION = 0.4
    
    def __init__(self, user_id: str, base_path: Optional[Path] = None):
        self.user_id = user_id
        self.base_path = base_path or Path(
            "/home/rock/.openclaw/workspace/skills/skill-preference-learning/preferences"
        )
        self.profile_path = self.base_path / f"{user_id}-profile.json"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.traits: Dict[str, LearnedTrait] = {}
        self.workflow_patterns: Dict[str, Dict] = {}
        self.last_session: Optional[str] = None
        
        self._load_profile()
    
    def _load_profile(self):
        """Load profile from disk."""
        if self.profile_path.exists():
            with open(self.profile_path) as f:
                data = json.load(f)
                
                # Load traits
                for name, trait_data in data.get("traits", {}).items():
                    self.traits[name] = LearnedTrait(**trait_data)
                
                # Load workflow patterns
                self.workflow_patterns = data.get("workflow_patterns", {})
                self.last_session = data.get("last_session")
    
    def _save_profile(self):
        """Save profile to disk."""
        temp_path = self.profile_path.with_suffix('.tmp')
        with open(temp_path, "w") as f:
            json.dump({
                "user_id": self.user_id,
                "updated_at": datetime.now().isoformat(),
                "last_session": self.last_session,
                "traits": {
                    name: {
                        "name": t.name,
                        "value": t.value,
                        "confidence": t.confidence,
                        "source": t.source,
                        "first_seen": t.first_seen,
                        "last_updated": t.last_updated,
                        "observation_count": t.observation_count,
                        "contradictions": t.contradictions
                    }
                    for name, t in self.traits.items()
                },
                "workflow_patterns": self.workflow_patterns
            }, f, indent=2)
        temp_path.rename(self.profile_path)
    
    def learn_trait(
        self,
        name: str,
        value: Any,
        confidence: float = 0.5,
        source: str = "observation"
    ):
        """Learn or update a user trait."""
        now = datetime.now().isoformat()
        
        if name in self.traits:
            trait = self.traits[name]
            
            if trait.value == value:
                # Reinforce existing preference
                trait.strengthen()
            else:
                # New preference contradicts old
                trait.contradict(value)
                trait.source = source
                # Confidence boost for explicit feedback
                if source == "explicit_feedback":
                    trait.confidence = max(trait.confidence, confidence)
        else:
            # New trait
            self.traits[name] = LearnedTrait(
                name=name,
                value=value,
                confidence=confidence,
                source=source,
                first_seen=now,
                last_updated=now,
                observation_count=1
            )
        
        self._save_profile()
    
    def get_trait(self, name: str, default: Any = None) -> Optional[Any]:
        """Get a trait value if confidence is sufficient."""
        if name not in self.traits:
            return default
        
        trait = self.traits[name]
        if trait.confidence < self.MIN_CONFIDENCE_FOR_APPLICATION:
            return default
        
        return trait.value
    
    def get_confidence(self, name: str) -> float:
        """Get confidence level for a trait."""
        if name not in self.traits:
            return 0.0
        return self.traits[name].confidence
    
    def get_communication_profile(self) -> Dict[str, Any]:
        """Get learned communication preferences."""
        return {
            "verbosity": self.get_trait("communication.verbosity", "medium"),
            "detail_level": self.get_trait("communication.detail_level", "balanced"),
            "code_first": self.get_trait("communication.code_first", False),
            "emoji_usage": self.get_trait("communication.emoji_usage", "minimal"),
            "ask_clarification": self.get_trait("communication.ask_clarification", True),
            "summarize_long": self.get_trait("communication.summarize_long", True),
            "preferred_sections": self.get_trait("communication.preferred_sections", []),
        }
    
    def get_risk_profile(self) -> Dict[str, Any]:
        """Get learned risk tolerance preferences."""
        return {
            "automation_level": self.get_trait("risk.automation_level", "moderate"),
            "confirm_destructive": self.get_trait("risk.confirm_destructive", True),
            "confirm_external": self.get_trait("risk.confirm_external", True),
            "prefers_dry_run": self.get_trait("risk.prefers_dry_run", True),
            "rollback_comfort": self.get_trait("risk.rollback_comfort", "medium"),
            "batch_size_preference": self.get_trait("risk.batch_size_preference", 10),
        }
    
    def get_pace_profile(self) -> Dict[str, Any]:
        """Get learned pace preferences."""
        return {
            "response_speed": self.get_trait("pace.response_speed", "balanced"),
            "prefers_async": self.get_trait("pace.prefers_async", False),
            "batching_preference": self.get_trait("pace.batching_preference", "medium"),
            "intermediate_updates": self.get_trait("pace.intermediate_updates", True),
            "notification_frequency": self.get_trait("pace.notification_frequency", "as_needed"),
        }
    
    def learn_workflow_pattern(
        self,
        pattern_name: str,
        steps: List[str],
        success: bool = True,
        duration_seconds: Optional[int] = None,
        tools_used: Optional[List[str]] = None
    ):
        """Learn from a completed workflow."""
        now = datetime.now().isoformat()
        
        if pattern_name not in self.workflow_patterns:
            self.workflow_patterns[pattern_name] = {
                "name": pattern_name,
                "common_steps": steps,
                "first_seen": now,
                "last_seen": now,
                "execution_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "avg_duration_seconds": 0,
                "common_tools": tools_used or []
            }
        
        pattern = self.workflow_patterns[pattern_name]
        pattern["last_seen"] = now
        pattern["execution_count"] += 1
        
        if success:
            pattern["success_count"] += 1
        else:
            pattern["failure_count"] += 1
        
        # Update average duration
        if duration_seconds:
            old_avg = pattern["avg_duration_seconds"]
            count = pattern["execution_count"]
            new_avg = (old_avg * (count - 1) + duration_seconds) / count
            pattern["avg_duration_seconds"] = int(new_avg)
        
        # Track tool usage
        if tools_used:
            existing = set(pattern.get("common_tools", []))
            pattern["common_tools"] = list(existing | set(tools_used))
        
        self._save_profile()
    
    def get_workflow_profile(self, pattern_name: str) -> Optional[Dict]:
        """Get stats for a workflow pattern."""
        return self.workflow_patterns.get(pattern_name)
    
    def list_workflow_patterns(self) -> List[str]:
        """List all learned workflow patterns."""
        return list(self.workflow_patterns.keys())
    
    def get_full_profile(self) -> Dict[str, Any]:
        """Get complete user profile for context."""
        return {
            "communication": self.get_communication_profile(),
            "risk_tolerance": self.get_risk_profile(),
            "pace": self.get_pace_profile(),
            "learned_traits": {
                name: {
                    "value": t.value,
                    "confidence": round(t.confidence, 2),
                    "observations": t.observation_count
                }
                for name, t in self.traits.items()
                if t.confidence >= self.MIN_CONFIDENCE_FOR_APPLICATION
            },
            "workflow_patterns_count": len(self.workflow_patterns)
        }
    
    # Pre-defined trait patterns for common preferences
    COMMUNICATION_TRAITS = [
        "communication.verbosity",  # minimal, low, medium, high
        "communication.detail_level",  # minimal, balanced, thorough
        "communication.code_first",  # bool - show code before explanation
        "communication.emoji_usage",  # none, minimal, moderate
        "communication.ask_clarification",  # bool
        "communication.summarize_long",  # bool
    ]
    
    RISK_TRAITS = [
        "risk.automation_level",  # manual, conservative, moderate, aggressive
        "risk.confirm_destructive",  # bool
        "risk.confirm_external",  # bool
        "risk.prefers_dry_run",  # bool
        "risk.rollback_comfort",  # low, medium, high
    ]
    
    PACE_TRAITS = [
        "pace.response_speed",  # deliberate, balanced, fast
        "pace.prefers_async",  # bool
        "pace.intermediate_updates",  # bool
    ]


# Verification test
if __name__ == "__main__":
    import tempfile
    
    print("=" * 60)
    print("PROFILE MANAGER - VERIFICATION TEST")
    print("=" * 60)
    
    # Create test environment
    test_base = Path(tempfile.mkdtemp())
    print(f"\n[1] Test environment: {test_base}")
    
    # Initialize manager
    print("[2] Initializing ProfileManager for 'test_user'...")
    pm = ProfileManager("test_user", base_path=test_base)
    
    # Test learning traits
    print("[3] Learning traits...")
    pm.learn_trait("communication.verbosity", "low", confidence=0.8, source="explicit_feedback")
    pm.learn_trait("risk.confirm_destructive", True, confidence=0.6, source="observation")
    pm.learn_trait("pace.prefers_async", True, confidence=0.9, source="explicit_feedback")
    
    # Verify trait retrieval
    print("[4] Verifying trait retrieval...")
    verbosity = pm.get_trait("communication.verbosity")
    assert verbosity == "low", f"Expected 'low', got {verbosity}"
    print(f"    - verbosity: {verbosity} ✓")
    
    conf = pm.get_confidence("communication.verbosity")
    print(f"    - confidence: {conf:.2f} ✓")
    
    # Test profile sections
    print("[5] Getting profile sections...")
    comm_profile = pm.get_communication_profile()
    print(f"    - Communication: {comm_profile}")
    
    risk_profile = pm.get_risk_profile()
    print(f"    - Risk tolerance: {risk_profile['automation_level']}")
    
    # Test workflow learning
    print("[6] Learning workflow patterns...")
    pm.learn_workflow_pattern(
        "code_review",
        steps=["read", "analyze", "suggest", "verify"],
        success=True,
        duration_seconds=120,
        tools_used=["read", "edit", "exec"]
    )
    
    # Verify workflow pattern
    workflow = pm.get_workflow_profile("code_review")
    assert workflow is not None, "Workflow not found"
    assert workflow["execution_count"] == 1
    print(f"    - Pattern '{workflow['name']}' learned ✓")
    print(f"    - Steps: {workflow['common_steps']} ✓")
    
    # Test persistence
    print("[7] Testing persistence...")
    pm2 = ProfileManager("test_user", base_path=test_base)
    persisted = pm2.get_trait("communication.verbosity")
    assert persisted == "low", f"Expected 'low', got {persisted}"
    print(f"    - Trait persisted: {persisted} ✓")
    
    # Test unknown trait
    print("[8] Testing unknown trait retrieval...")
    unknown = pm.get_trait("unknown.trait", default="fallback")
    assert unknown == "fallback"
    print(f"    - Unknown trait returns default: {unknown} ✓")
    
    # Get full profile
    print("[9] Getting full profile...")
    full = pm.get_full_profile()
    print(f"    - Learned traits: {len(full['learned_traits'])}")
    print(f"    - Workflow patterns: {full['workflow_patterns_count']}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    
    # Cleanup
    import shutil
    shutil.rmtree(test_base)
    print(f"\nCleaned up: {test_base}")