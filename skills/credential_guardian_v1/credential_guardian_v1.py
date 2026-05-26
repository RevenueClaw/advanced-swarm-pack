#!/usr/bin/env python3
"""
Credential Guardian v1 - Advanced Swarm Pack
Prevents credential loss/corruption through validation, backup, and auto-restore.
"""

import os
import json
import hashlib
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import time

# Configuration
CREDENTIALS_DIR = Path.home() / ".openclaw" / "credentials"
BACKUP_DIR = CREDENTIALS_DIR / ".backups"
MASTER_STORE = CREDENTIALS_DIR / ".master_store.json"

# Critical credentials to monitor
CRITICAL_CREDENTIALS = {
    "amazon_creators": {
        "files": ["amazon_creators.env"],
        "required_vars": ["AMAZON_CREATOR_CLIENT_ID", "AMAZON_CREATOR_CLIENT_SECRET", "AMAZON_PARTNER_TAG"],
        "backup_interval_minutes": 30,
    },
    "github": {
        "files": ["github.env", ".github_token"],
        "required_vars": ["GITHUB_PERSONAL_ACCESS_TOKEN", "GITHUB_TOKEN"],
        "backup_interval_minutes": 30,
    },
}


class CredentialGuardian:
    """
    Protects critical credentials from loss/corruption.
    
    Features:
    - Auto-validation on startup
    - Automatic restoration from master backup
    - Timestamped backups before edits
    - Periodic health checks
    """
    
    def __init__(self, auto_validate: bool = True):
        self.credentials_dir = CREDENTIALS_DIR
        self.backup_dir = BACKUP_DIR
        self.master_store = MASTER_STORE
        
        # Ensure directories exist
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize master store if not exists
        if not self.master_store.exists():
            self._init_master_store()
        
        # Load master store
        self._load_master_store()
        
        # Auto-validate on init
        if auto_validate:
            self.validate_all_credentials()
        
        # Start periodic health check
        self._start_health_check_thread()
    
    def _init_master_store(self):
        """Initialize empty master store with metadata."""
        master_data = {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "credentials": {},
            "last_backup": None,
        }
        
        with open(self.master_store, 'w') as f:
            json.dump(master_data, f, indent=2)
        
        # Set secure permissions
        os.chmod(self.master_store, 0o600)
    
    def _load_master_store(self) -> Dict:
        """Load master store data."""
        try:
            with open(self.master_store, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # Corrupted master store - reinitialize
            self._init_master_store()
            return self._load_master_store()
    
    def _save_master_store(self, data: Dict):
        """Save to master store."""
        with open(self.master_store, 'w') as f:
            json.dump(data, f, indent=2)
        os.chmod(self.master_store, 0o600)
    
    def _hash_file(self, filepath: Path) -> str:
        """Generate MD5 hash of file contents."""
        if not filepath.exists():
            return ""
        
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def create_timed_backup(self, filepath: Path, reason: str = "manual") -> Path:
        """
        Create timestamped backup before editing credential file.
        
        Args:
            filepath: Path to credential file
            reason: Why backup was created (e.g., "pre_edit", "scheduled")
        
        Returns:
            Path to backup file
        """
        if not filepath.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filepath.stem}_{timestamp}_{reason}{filepath.suffix}"
        backup_path = self.backup_dir / filename
        
        shutil.copy2(filepath, backup_path)
        os.chmod(backup_path, 0o600)
        
        # Update master store
        master_data = self._load_master_store()
        master_data["last_backup"] = {
            "timestamp": timestamp,
            "file": str(filepath),
            "backup_path": str(backup_path),
            "reason": reason,
        }
        self._save_master_store(master_data)
        
        return backup_path
    
    def validate_credential(self, cred_name: str, auto_restore: bool = True) -> Tuple[bool, str]:
        """
        Validate a critical credential set.
        
        Args:
            cred_name: Name of credential set (e.g., "amazon_creators")
            auto_restore: If True, attempt restoration from master
        
        Returns:
            (is_valid, message)
        """
        if cred_name not in CRITICAL_CREDENTIALS:
            return False, f"Unknown credential: {cred_name}"
        
        config = CRITICAL_CREDENTIALS[cred_name]
        
        # Check if credential files exist and are valid
        for filename in config["files"]:
            filepath = self.credentials_dir / filename
            
            if not filepath.exists():
                if auto_restore:
                    restored = self._restore_from_master(cred_name, filename)
                    if restored:
                        return True, f"Restored {filename} from master"
                    else:
                        return False, f"Missing {filename} - no backup available"
                else:
                    return False, f"Missing {filename}"
            
            # Check if file is corrupted (empty or unreadable)
            try:
                stat = filepath.stat()
                if stat.st_size == 0:
                    if auto_restore:
                        restored = self._restore_from_master(cred_name, filename)
                        if restored:
                            return True, f"Restored empty {filename} from master"
                    return False, f"Corrupted (empty): {filename}"
                
                # Try to read
                with open(filepath, 'r') as f:
                    content = f.read()
                    if not content.strip():
                        if auto_restore:
                            restored = self._restore_from_master(cred_name, filename)
                            if restored:
                                return True, f"Restored {filename} from master"
                        return False, f"Corrupted (blank): {filename}"
                    
                    # Validate required vars are present
                    for var in config.get("required_vars", []):
                        if var not in content or "=" not in content:
                            continue  # Skip if not present
                        value = content.split(f"{var}=")[1].split("\n")[0].strip() if f"{var}=" in content else ""
                        if not value or value.startswith("{{"):
                            if auto_restore:
                                restored = self._restore_from_master(cred_name, filename)
                                if restored:
                                    return True, f"Restored {filename} from master (missing values)"
                            return False, f"Corrupted (placeholder values): {filename}"
            
            except Exception as e:
                if auto_restore:
                    restored = self._restore_from_master(cred_name, filename)
                    if restored:
                        return True, f"Restored {filename} from master (error: {e})"
                return False, f"Error reading {filename}: {e}"
        
        return True, f"{cred_name} validated OK"
    
    def _restore_from_master(self, cred_name: str, filename: str) -> bool:
        """Restore credential from master store."""
        master_data = self._load_master_store()
        
        if cred_name not in master_data.get("credentials", {}):
            return False
        
        cred_data = master_data["credentials"][cred_name]
        filepath = self.credentials_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                f.write(cred_data.get("content", ""))
            os.chmod(filepath, 0o600)
            
            print(f"[CredentialGuardian] Restored {filename} from master store")
            return True
        except Exception as e:
            print(f"[CredentialGuardian] Failed to restore {filename}: {e}")
            return False
    
    def validate_all_credentials(self) -> Dict[str, Tuple[bool, str]]:
        """Validate all critical credentials."""
        results = {}
        print("[CredentialGuardian] Validating all credentials...")
        
        for cred_name in CRITICAL_CREDENTIALS:
            is_valid, message = self.validate_credential(cred_name, auto_restore=True)
            results[cred_name] = (is_valid, message)
            status = "✓" if is_valid else "✗"
            print(f"  {status} {cred_name}: {message}")
        
        return results
    
    def backup_to_master(self, cred_name: str, filename: str, content: str):
        """
        Store credential content in master backup.
        Call this after successful credential updates.
        """
        master_data = self._load_master_store()
        
        if "credentials" not in master_data:
            master_data["credentials"] = {}
        
        master_data["credentials"][cred_name] = {
            "filename": filename,
            "content": content,
            "backed_up_at": datetime.now().isoformat(),
            "hash": hashlib.sha256(content.encode()).hexdigest()[:16],
        }
        
        self._save_master_store(master_data)
        print(f"[CredentialGuardian] Backed up {filename} to master store")
    
    def _start_health_check_thread(self):
        """Start periodic health check in background thread."""
        def health_check_loop():
            while True:
                time.sleep(1800)  # 30 minutes
                try:
                    self.validate_all_credentials()
                except Exception as e:
                    print(f"[CredentialGuardian] Health check error: {e}")
        
        thread = threading.Thread(target=health_check_loop, daemon=True)
        thread.start()
    
    def get_status(self) -> Dict:
        """Get current guardian status."""
        master_data = self._load_master_store()
        
        # Count backups
        backup_count = len(list(self.backup_dir.glob("*")))
        
        return {
            "version": master_data.get("version", "unknown"),
            "credentials_backed_up": len(master_data.get("credentials", {})),
            "total_backups": backup_count,
            "last_backup": master_data.get("last_backup"),
            "master_store": str(self.master_store),
            "credentials_dir": str(self.credentials_dir),
        }


def credential_guardian_cli():
    """CLI interface for credential guardian."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Credential Guardian")
    parser.add_argument("--validate", action="store_true", help="Validate all credentials")
    parser.add_argument("--status", action="store_true", help="Show guardian status")
    parser.add_argument("--backup", metavar="FILE", help="Create backup of file")
    parser.add_argument("--restore", metavar="NAME", help="Restore credential by name")
    
    args = parser.parse_args()
    
    guardian = CredentialGuardian(auto_validate=False)
    
    if args.validate:
        results = guardian.validate_all_credentials()
        print("\nValidation Results:")
        for name, (is_valid, message) in results.items():
            status = "✓" if is_valid else "✗"
            print(f"  {status} {name}: {message}")
    
    elif args.status:
        status = guardian.get_status()
        print("\nCredential Guardian Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    elif args.backup:
        filepath = Path(args.backup)
        backup_path = guardian.create_timed_backup(filepath, "cli_manual")
        print(f"Created backup: {backup_path}")
    
    elif args.restore:
        restored = guardian._restore_from_master(args.restore, f"{args.restore}.env")
        print(f"Restored: {restored}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    credential_guardian_cli()
