#!/usr/bin/env python3
"""PreferenceEngine - Main entry point for user preference learning.

Integrates:
- ProfileManager (learned traits)
- FeedbackIngestor (HITL feedback processing)

Provides:
- unified learning interface
- preference queries for agent behavior
- procedural memory compilation

Author: RockClaw
Version: 1.0.0-alpha
Status: VERIFIED (basic structure)
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from profile_manager import ProfileManager
from feedback_ingestor import FeedbackIngestor
from typing import Dict, List, Optional, Any


class PreferenceEngine:
    """
    Unified interface for user preference learning.
    
    Usage:
        pe = PreferenceEngine("shayne")
        
        # Learn from HITL feedback
        pe.ingest_feedback(
            session_id="abc123",
            task_type="code_review",
            original_action="suggested edit",
            user_response="Always show the diff first"
        )
        
        # Learn from successful workflow
        pe.learn_workflow(
            pattern_name="config_change",
            steps=["backup", "modify", "verify"],
            success=True
        )
        
        # Query preferences
        style = pe.get_communication_style()
    """
    
    def __init__(self, user_id: str, base_path: Optional[Path] = None):
        self.user_id = user_id
        
        # Initialize sub-components
        self.profile = ProfileManager(user_id, base_path)
        self.feedback = FeedbackIngestor(user_id, base_path)
        
        # Initialize default complex coding preferences (v1.3.0)
        self._init_complex_coding_defaults()
        
        # Wire feedback -> profile
        self.feedback.register_preference_callback(
            self._on_preference_extracted
        )
    
    def _init_complex_coding_defaults(self):
        """Initialize default preferences for complex coding (v1.3.0)."""
        defaults = {
            # Path resolution
            "coding.path_resolution": ("runtime", 0.95, "system_default"),
            
            # File operations
            "coding.file_operations": ("atomic", 0.95, "system_default"),
            "coding.backup_required": (True, 0.95, "system_default"),
            
            # Logging patterns
            "coding.logging_pattern": ("runtime_paths", 0.95, "system_default"),
            
            # Docker/infrastructure awareness
            "coding.docker_aware": (True, 0.95, "system_default"),
            "coding.import_time_safe": (True, 0.95, "system_default"),
            
            # Safety practices
            "coding.scp_append_avoid": (True, 0.95, "system_default"),
            "coding.verify_before_cascade": (True, 0.95, "system_default"),
            
            # Build/cache awareness
            "coding.docker_build_no_cache_on_dependency_change": (True, 0.9, "system_default")
        }
        
        for trait, (value, confidence, source) in defaults.items():
            # Only set if not already learned
            if self.profile.get_trait(trait) is None:
                self.profile.learn_trait(trait, value, confidence, source)
    
    def _on_preference_extracted(self, preferences: List[Dict], ftype: Any, delta: float):
        """Callback when new preferences are extracted from feedback."""
        for pref in preferences:
            self.profile.learn_trait(
                name=pref["trait"],
                value=pref["value"],
                confidence=pref.get("confidence", 0.6),
                source="explicit_feedback"
            )
    
    def ingest_feedback(
        self,
        session_id: str,
        task_type: str,
        original_action: str,
        user_response: str,
        context: Optional[Dict] = None
    ):
        """Ingest HITL feedback and learn preferences."""
        return self.feedback.ingest_feedback(
            session_id, task_type, original_action, user_response, context
        )
    
    def learn_workflow(
        self,
        pattern_name: str,
        steps: List[str],
        success: bool = True,
        duration_seconds: Optional[int] = None,
        tools_used: Optional[List[str]] = None
    ):
        """Learn from a completed workflow pattern."""
        return self.profile.learn_workflow_pattern(
            pattern_name, steps, success, duration_seconds, tools_used
        )
    
    def get_communication_style(self) -> Dict[str, Any]:
        """Get learned communication preferences."""
        return self.profile.get_communication_profile()
    
    def get_risk_tolerance(self) -> Dict[str, Any]:
        """Get learned risk tolerance."""
        return self.profile.get_risk_profile()
    
    def get_pace_preferences(self) -> Dict[str, Any]:
        """Get learned pace preferences."""
        return self.profile.get_pace_profile()
    
    def get_workflow_preference(self, pattern_name: str) -> Optional[Dict]:
        """Get learned workflow pattern."""
        return self.profile.get_workflow_profile(pattern_name)
    
    def get_full_context(self) -> Dict[str, Any]:
        """Get complete preference context for system prompt."""
        return {
            "user_id": self.user_id,
            **self.profile.get_full_profile(),
            "recent_feedback": self.feedback.get_preference_summary(hours=24)
        }
    
    def should_ask_clarification(self, action_type: str, risk_level: str) -> bool:
        """Decision helper: should agent ask for clarification?"""
        # Check learned preference
        ask_trait = self.profile.get_trait("communication.ask_clarification")
        if ask_trait is not None:
            return ask_trait
        
        # Risk-based default
        if risk_level == "high":
            return True
        if risk_level == "destructive":
            return True
        
        return True  # Conservative default
    
    def should_use_dry_run(self, action_type: str, destructive: bool) -> bool:
        """Decision helper: should agent use dry-run first?"""
        dry_run_pref = self.profile.get_trait("risk.prefers_dry_run")
        if dry_run_pref is not None:
            return dry_run_pref
        
        # Default based on action
        if destructive:
            return True
        return False
    
    def get_coding_preferences(self) -> Dict[str, Any]:
        """Get complex coding and infrastructure preferences."""
        # Check for learned preferences, fallback to safe defaults
        prefs = {
            "path_resolution": self.profile.get_trait("coding.path_resolution") or "runtime",
            "file_operations": self.profile.get_trait("coding.file_operations") or "atomic",
            "backup_required": self.profile.get_trait("coding.backup_required") or True,
            "logging_pattern": self.profile.get_trait("coding.logging_pattern") or "runtime_paths",
            "docker_aware": self.profile.get_trait("coding.docker_aware") or True,
            "import_time_safe": self.profile.get_trait("coding.import_time_safe") or True
        }
        return prefs
    
    def get_safe_edit_checklist(self) -> Dict[str, List[str]]:
        """Get safe edit checklist for complex coding/infrastructure tasks."""
        return {
            "mandatory": [
                "Create timestamped backup before any edit",
                "Use atomic writes (temp file + rename)",
                "Verify file integrity after write (content matches intent)"
            ],
            "for_docker": [
                "Validate docker-compose syntax before applying",
                "Check container health before and after edits",
                "Verify volume mounts in 'docker inspect'",
                "Never use SCP in append mode"
            ],
            "for_python": [
                "Avoid import-time DB connections (move to init functions)",
                "Avoid import-time network calls",
                "Resolve paths at runtime, not import",
                "Log actual paths at runtime, not assumed"
            ],
            "verification_steps": [
                "Syntax check before write",
                "Test dry-run if available",
                "Verify rollback works before proceeding with cascade edits"
            ]
        }


# Verification test
if __name__ == "__main__":
    import tempfile
    import shutil
    
    print("=" * 60)
    print("PREFERENCE ENGINE - VERIFICATION TEST")
    print("=" * 60)
    
    # Setup
    test_base = Path(tempfile.mkdtemp())
    print(f"\n[1] Test environment: {test_base}")
    
    # Initialize
    print("[2] Initializing PreferenceEngine...")
    pe = PreferenceEngine("test_user", base_path=test_base)
    
    # Test feedback -> preference flow
    print("[3] Testing feedback -> preference learning...")
    pe.ingest_feedback(
        session_id="sess-001",
        task_type="code_review",
        original_action="suggested changes",
        user_response="Always show code first, then explain"
    )
    
    # Verify preference was learned
    code_first = pe.profile.get_trait("communication.code_first")
    assert code_first == True, f"Expected True, got {code_first}"
    print(f"    - Learned: code_first = {code_first} ✓")
    
    # Test workflow learning
    print("[4] Testing workflow pattern learning...")
    pe.learn_workflow(
        pattern_name="config_backup",
        steps=["backup", "edit", "verify"],
        success=True,
        duration_seconds=45,
        tools_used=["file_write", "read"]
    )
    
    workflow = pe.get_workflow_preference("config_backup")
    assert workflow is not None
    print(f"    - Learned workflow: {workflow['name']} ✓")
    print(f"    - Steps: {workflow['common_steps']} ✓")
    
    # Test decision helpers
    print("[5] Testing decision helpers...")
    
    # Explicit preference exists
    should_ask = pe.should_ask_clarification("any", "medium")
    print(f"    - Should ask clarification: {should_ask} ✓")
    
    # No pref set, high risk
    should_ask = pe.should_ask_clarification("file_delete", "destructive")
    assert should_ask == True
    print(f"    - Should ask on destructive: {should_ask} ✓")
    
    # Get full context
    print("[6] Getting full context...")
    context = pe.get_full_context()
    print(f"    - User ID: {context['user_id']} ✓")
    print(f"    - Communication: {len(context['communication'])} traits ✓")
    print(f"    - Risk profile: {len(context['risk_tolerance'])} traits ✓")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    
    # Cleanup
    shutil.rmtree(test_base)
    print(f"\nCleaned up: {test_base}")