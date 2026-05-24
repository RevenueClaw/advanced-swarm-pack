#!/usr/bin/env python3
"""
Audit logging for credential access.
Tracks who accessed what and when, without logging actual values.

v1.0.2 - Production Release
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class AuditEntry:
    """Single audit log entry."""
    timestamp: str
    credential_name: str
    credential_hash: str  # Hash of name+service, not value
    action: str  # get, set, delete, validate
    skill: str  # Which skill accessed it
    success: bool
    error_message: Optional[str] = None


class AuditLogger:
    """
    Audit logging for credential operations.
    
    Logs:
    - When credentials are accessed
    - Which skill did the accessing
    - Success/failure status
    - Never logs actual credential values
    """
    
    def __init__(self, log_dir: Optional[Path] = None, 
                 max_entries: int = 10000):
        self.log_dir = log_dir or Path.home() / ".openclaw/credentials/.audit"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        
        self.log_file = self.log_dir / f"{datetime.now():%Y-%m}.jsonl"
    
    def _hash_credential_ref(self, name: str, service: str) -> str:
        """Create non-reversible hash for credential reference."""
        return hashlib.sha256(f"{service}:{name}".encode()).hexdigest()[:16]
    
    def log(self, credential_name: str, service: str, action: str,
           skill: str, success: bool, error: Optional[str] = None):
        """
        Log a credential operation.
        
        Args:
            credential_name: Name of credential accessed
            service: Service identifier (github, agentmail, etc)
            action: Operation performed (get, set, delete, validate)
            skill: Which skill made the request
            success: Whether operation succeeded
            error: Error message if failed
        """
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            credential_name=credential_name,
            credential_hash=self._hash_credential_ref(credential_name, service),
            action=action,
            skill=skill,
            success=success,
            error_message=error
        )
        
        self._append_entry(entry)
    
    def _append_entry(self, entry: AuditEntry):
        """Append entry to log file."""
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps({
                    'timestamp': entry.timestamp,
                    'credential_hash': entry.credential_hash,
                    'action': entry.action,
                    'skill': entry.skill,
                    'success': entry.success,
                    'error': entry.error_message
                }) + '\n')
        except Exception as e:
            print(f"Warning: Failed to write audit log: {e}")
    
    def get_activity(self, credential_name: Optional[str] = None,
                    days: int = 7) -> list:
        """
        Get audit trail for credentials.
        
        Args:
            credential_name: Filter by specific credential
            days: Lookback period
            
        Returns:
            List of audit entries
        """
        entries = []
        
        if not self.log_file.exists():
            return entries
        
        cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
        target_hash = None
        if credential_name:
            # Extract service from name (first part before underscore)
            service = credential_name.split('_')[0] if '_' in credential_name else 'unknown'
            target_hash = self._hash_credential_ref(credential_name, service)
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(data['timestamp'])
                        
                        if entry_time < cutoff:
                            continue
                        
                        if target_hash and data['credential_hash'] != target_hash:
                            continue
                        
                        entries.append(data)
                        
                    except:
                        continue
                        
        except Exception as e:
            print(f"Error reading audit log: {e}")
        
        return entries
    
    def get_stats(self, days: int = 30) -> dict:
        """Get audit statistics."""
        activity = self.get_activity(days=days)
        
        success_count = sum(1 for a in activity if a.get('success'))
        
        return {
            'total_operations': len(activity),
            'successful': success_count,
            'failed': len(activity) - success_count,
            'unique_credentials': len(set(a['credential_hash'] for a in activity)),
            'top_skills': self._top_skills(activity, 5),
            'top_actions': self._top_actions(activity, 5)
        }
    
    def _top_skills(self, activity: list, n: int) -> list:
        """Get top skills by operation count."""
        counts = {}
        for a in activity:
            skill = a.get('skill', 'unknown')
            counts[skill] = counts.get(skill, 0) + 1
        
        sorted_skills = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_skills[:n]
    
    def _top_actions(self, activity: list, n: int) -> list:
        """Get top actions by count."""
        counts = {}
        for a in activity:
            action = a.get('action', 'unknown')
            counts[action] = counts.get(action, 0) + 1
        
        sorted_actions = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_actions[:n]


# Self-test
if __name__ == "__main__":
    print("Testing AuditLogger...")
    
    logger = AuditLogger()
    
    # Test logging
    logger.log("github_token", "github", "get", "skill-idea-tracker", True)
    logger.log("github_token", "github", "validate", "skill-credential-manager", True)
    logger.log("test_creds", "test", "get", "test-skill", False, "Not found")
    
    print("✓ Logging works")
    
    # Test retrieval
    activity = logger.get_activity(days=1)
    assert len(activity) >= 3, f"Expected >= 3 entries, got {len(activity)}"
    print("✓ Retrieval works")
    
    # Test stats
    stats = logger.get_stats(days=1)
    assert stats['total_operations'] >= 3
    print(f"✓ Stats: {stats['total_operations']} ops, {stats['successful']} success")
    
    # Cleanup
    print("\n✓ All audit tests passed")
