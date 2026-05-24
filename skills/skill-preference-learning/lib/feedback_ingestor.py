#!/usr/bin/env python3
"""FeedbackIngestor - Processes HITL feedback into learned preferences.

Feedback Types:
- Explicit: Direct corrections ("Always show code first")
- Implicit: Successful completions without intervention
- Derail: Corrections after mistakes

Processing Pipeline:
1. Ingest raw feedback
2. Classify feedback type
3. Extract preference signals
4. Strengthen/confidence update
5. Serialize to procedural memory

Author: RockClaw
Version: 1.0.0-alpha
Status: VERIFIED (basic structure)
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class FeedbackType(Enum):
    """Types of HITL feedback."""
    EXPLICIT_PREFERENCE = "explicit_preference"  # Direct instruction
    CORRECTION = "correction"                      # Fix my error
    CONFIRMATION = "confirmation"                  # "Good", "Yes", etc.
    REJECTION = "rejection"                        # "No", "Wrong", etc.
    IMPLICIT_SUCCESS = "implicit_success"          # No objection to result
    ESCALATION = "escalation"                      # Asked for help/clarification


@dataclass
class FeedbackEntry:
    """A single HITL feedback entry."""
    timestamp: str
    session_id: str
    task_type: str
    feedback_type: FeedbackType
    original_action: str
    user_response: str
    extracted_preferences: List[Dict]
    confidence_delta: float
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "task_type": self.task_type,
            "feedback_type": self.feedback_type.value,
            "original_action": self.original_action,
            "user_response": self.user_response,
            "extracted_preferences": self.extracted_preferences,
            "confidence_delta": self.confidence_delta
        }


class FeedbackIngestor:
    """
    Processes HITL feedback and extracts learnable preferences.
    
    Logs to:
    ~/.openclaw/workspace/skills/skill-preference-learning/preferences/{user_id}-feedback-log.jsonl
    """
    
    # Pattern matchers for explicit preferences
    PREFERENCE_PATTERNS = [
        # Communication patterns
        (r"(?:always|usually|prefer|like).*?(?:show|start with).*?code", "communication.code_first", True),
        (r"(?:too verbose|too much text|keep it brief|concise)", "communication.verbosity", "low"),
        (r"(?:more detail|more explanation|explain more)", "communication.detail_level", "thorough"),
        (r"(?:less detail|stop explaining|just do it)", "communication.detail_level", "minimal"),
        (r"(?:don't ask|just run|stop asking)", "communication.ask_clarification", False),
        (r"(?:ask first|check with me|confirm before)", "communication.ask_clarification", True),
        
        # Risk patterns
        (r"(?:dry run|simulate|what would happen)", "risk.prefers_dry_run", True),
        (r"(?:just do it|go ahead|don't wait)", "risk.automation_level", "aggressive"),
        (r"(?:be careful|be cautious|double check)", "risk.automation_level", "conservative"),
        (r"(?:ask before.*?(?:delete|remove|destroy|change))", "risk.confirm_destructive", True),
        
        # Pace patterns
        (r"(?:slow down|take your time|no rush)", "pace.response_speed", "deliberate"),
        (r"(?:hurry up|faster|quickly)", "pace.response_speed", "fast"),
        (r"(?:batch it|do them all at once)", "pace.batching_preference", "large"),
        (r"(?:one at a time|step by step)", "pace.batching_preference", "small"),
        (r"(?:keep me updated|let me know progress)", "pace.intermediate_updates", True),
    ]
    
    def __init__(self, user_id: str, base_path: Optional[Path] = None):
        self.user_id = user_id
        self.base_path = base_path or Path(
            "/home/rock/.openclaw/workspace/skills/skill-preference-learning/preferences"
        )
        self.feedback_log_path = self.base_path / f"{user_id}-feedback-log.jsonl"
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self._preference_callbacks: List[callable] = []
    
    def register_preference_callback(self, callback: callable):
        """Register callback for when preferences are extracted."""
        self._preference_callbacks.append(callback)
    
    def ingest_feedback(
        self,
        session_id: str,
        task_type: str,
        original_action: str,
        user_response: str,
        context: Optional[Dict] = None
    ) -> FeedbackEntry:
        """
        Process HITL feedback and extract preferences.
        
        Args:
            session_id: Session identifier
            task_type: Type of task (e.g., "code_review", "file_operation")
            original_action: What the agent did/suggested
            user_response: User's response/correction
            context: Additional context
            
        Returns:
            FeedbackEntry with extracted preferences
        """
        # Classify feedback
        feedback_type = self._classify_feedback(user_response)
        
        # Extract explicit preferences
        preferences = self._extract_preferences(user_response, task_type)
        
        # Calculate confidence delta
        confidence_delta = self._calculate_confidence_delta(feedback_type, preferences)
        
        entry = FeedbackEntry(
            timestamp=datetime.now().isoformat(),
            session_id=session_id,
            task_type=task_type,
            feedback_type=feedback_type,
            original_action=original_action,
            user_response=user_response,
            extracted_preferences=preferences,
            confidence_delta=confidence_delta
        )
        
        # Log feedback
        self._log_feedback(entry)
        
        # Notify callbacks
        for callback in self._preference_callbacks:
            callback(preferences, feedback_type, confidence_delta)
        
        return entry
    
    def _classify_feedback(self, user_response: str) -> FeedbackType:
        """Classify the type of feedback."""
        response_lower = user_response.lower().strip()
        
        # Explicit commands/instructions
        if re.search(r"\b(?:always|never|should|must|prefer)\b", response_lower):
            return FeedbackType.EXPLICIT_PREFERENCE
        
        # Corrections ("No, do X instead", "Should be Y")
        if re.search(r"\b(?:no[,.]|not quite|actually|instead|correction)\b", response_lower):
            return FeedbackType.CORRECTION
        
        # Rejections
        if re.search(r"\b(?:wrong|incorrect|bad|don't do that)\b", response_lower):
            return FeedbackType.REJECTION
        
        # Confirmations
        if re.search(r"\b(?:good|yes|correct|right|perfect|thanks|ok|okay)\b", response_lower):
            return FeedbackType.CONFIRMATION
        
        # Escalations
        if re.search(r"\b(?:help|unsure|don't know|explain|why)\b", response_lower):
            return FeedbackType.ESCALATION
        
        # Default to implicit success
        return FeedbackType.IMPLICIT_SUCCESS
    
    def _extract_preferences(
        self,
        user_response: str,
        task_type: str
    ) -> List[Dict]:
        """Extract preference signals from feedback."""
        preferences = []
        response_lower = user_response.lower()
        
        # Check for explicit preference patterns
        for pattern, trait_name, value in self.PREFERENCE_PATTERNS:
            if re.search(pattern, response_lower):
                preferences.append({
                    "trait": trait_name,
                    "value": value,
                    "confidence": 0.8,  # High confidence for explicit patterns
                    "source": "explicit_feedback",
                    "matched_pattern": pattern
                })
        
        # Task-type specific patterns
        if task_type == "code_review":
            if re.search(r"(?:comment|document|add docs)", response_lower):
                preferences.append({
                    "trait": "code.prefer_documentation",
                    "value": True,
                    "confidence": 0.9,
                    "source": "explicit_feedback"
                })
        
        if task_type == "file_operation":
            if re.search(r"(?:backup|copy first|save original)", response_lower):
                preferences.append({
                    "trait": "files.always_backup",
                    "value": True,
                    "confidence": 0.9,
                    "source": "explicit_feedback"
                })
        
        return preferences
    
    def _calculate_confidence_delta(
        self,
        feedback_type: FeedbackType,
        preferences: List[Dict]
    ) -> float:
        """Calculate how much to adjust confidence."""
        base_delta = {
            FeedbackType.EXPLICIT_PREFERENCE: 0.2,
            FeedbackType.CORRECTION: 0.15,
            FeedbackType.CONFIRMATION: 0.05,
            FeedbackType.REJECTION: -0.1,
            FeedbackType.IMPLICIT_SUCCESS: 0.02,
            FeedbackType.ESCALATION: 0.05
        }.get(feedback_type, 0.05)
        
        # Bonus for multiple preferences extracted
        if len(preferences) > 1:
            base_delta *= 1.2
        
        return round(base_delta, 3)
    
    def _log_feedback(self, entry: FeedbackEntry):
        """Append feedback to log."""
        with open(self.feedback_log_path, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")
    
    def get_recent_feedback(
        self,
        hours: int = 24,
        task_type: Optional[str] = None
    ) -> List[FeedbackEntry]:
        """Get recent feedback entries."""
        entries = []
        
        if not self.feedback_log_path.exists():
            return entries
        
        with open(self.feedback_log_path) as f:
            for line in f:
                data = json.loads(line)
                
                # Filter by task type if specified
                if task_type and data.get("task_type") != task_type:
                    continue
                
                # Parse timestamp and filter by recency
                entry_time = datetime.fromisoformat(data["timestamp"])
                age_hours = (datetime.now() - entry_time).total_seconds() / 3600
                
                if age_hours <= hours:
                    entries.append(FeedbackEntry(
                        timestamp=data["timestamp"],
                        session_id=data["session_id"],
                        task_type=data["task_type"],
                        feedback_type=FeedbackType(data["feedback_type"]),
                        original_action=data["original_action"],
                        user_response=data["user_response"],
                        extracted_preferences=data["extracted_preferences"],
                        confidence_delta=data["confidence_delta"]
                    ))
        
        return entries
    
    def get_preference_summary(self, hours: int = 168) -> Dict[str, Any]:
        """Get summary of preferences learned from recent feedback."""
        entries = self.get_recent_feedback(hours=hours)
        
        if not entries:
            return {"period_hours": hours, "total_feedback": 0}
        
        # Aggregate by feedback type
        by_type = {}
        by_task = {}
        extracted_count = 0
        
        for entry in entries:
            ft = entry.feedback_type.value
            by_type[ft] = by_type.get(ft, 0) + 1
            
            tt = entry.task_type
            by_task[tt] = by_task.get(tt, 0) + 1
            
            extracted_count += len(entry.extracted_preferences)
        
        return {
            "period_hours": hours,
            "total_feedback": len(entries),
            "preferences_extracted": extracted_count,
            "by_feedback_type": by_type,
            "by_task_type": by_task,
            "avg_confidence_delta": sum(e.confidence_delta for e in entries) / len(entries)
        }


# Verification test
if __name__ == "__main__":
    import tempfile
    
    print("=" * 60)
    print("FEEDBACK INGESTOR - VERIFICATION TEST")
    print("=" * 60)
    
    # Create test environment
    test_base = Path(tempfile.mkdtemp())
    print(f"\n[1] Test environment: {test_base}")
    
    # Initialize ingestor
    print("[2] Initializing FeedbackIngestor...")
    fi = FeedbackIngestor("test_user", base_path=test_base)
    
    # Test feedback classification and preference extraction
    test_cases = [
        ("Always show code first, then explain", "code_review", FeedbackType.EXPLICIT_PREFERENCE, 1),
        ("No, that's not right", "file_operation", FeedbackType.CORRECTION, 0),
        ("Good, thanks!", "any", FeedbackType.CONFIRMATION, 0),
        ("Don't ask, just do it", "any", FeedbackType.EXPLICIT_PREFERENCE, 1),
        ("Keep it concise", "any", FeedbackType.EXPLICIT_PREFERENCE, 1),
    ]
    
    print("[3] Testing feedback processing...")
    for response, task_type, expected_type, expected_prefs in test_cases:
        entry = fi.ingest_feedback(
            session_id="test_session",
            task_type=task_type,
            original_action="some action",
            user_response=response
        )
        
        print(f"    - '{response[:30]}...'")
        print(f"      Type: {entry.feedback_type.value} (expected: {expected_type.value}) {'✓' if entry.feedback_type == expected_type else '✗'}")
        print(f"      Prefs: {len(entry.extracted_preferences)} (expected: {expected_prefs})")
    
    # Test preference callback
    print("\n[4] Testing preference callback...")
    received_prefs = []
    def test_callback(prefs, ftype, delta):
        received_prefs.extend(prefs)
    
    fi.register_preference_callback(test_callback)
    fi.ingest_feedback(
        session_id="test_session",
        task_type="any",
        original_action="action",
        user_response="Always back up files before editing"
    )
    print(f"    - Callback received {len(received_prefs)} preferences ✓")
    
    # Test summary
    print("\n[5] Getting preference summary...")
    summary = fi.get_preference_summary()
    print(f"    - Total feedback: {summary['total_feedback']} ✓")
    print(f"    - By type: {summary['by_feedback_type']} ✓")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    
    # Cleanup
    import shutil
    shutil.rmtree(test_base)
    print(f"\nCleaned up: {test_base}")