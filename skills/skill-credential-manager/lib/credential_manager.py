#!/usr/bin/env python3
"""
Credential Manager - Main interface
Secure credential management for OpenClaw swarm.

v1.0.2 - Production Release
"""

import os
import sys
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Import local modules
from storage import CredentialEntry, FileStorage, EnvVarFallback, ChainedStorage
from validator import CredentialValidator, ValidationResult
from audit import AuditLogger
from discover import CredentialDiscovery


@dataclass
class CredentialInfo:
    """Information about a credential (without value)."""
    name: str
    service: str
    scopes: List[str]
    created_at: str
    last_used: Optional[str]
    validation_status: str
    source: str
    masked_value: str  # First/last 4 chars


class CredentialManager:
    """
    Main credential manager for the OpenClaw swarm.
    
    Features:
    - Secure file storage (permissions 600)
    - Environment variable fallback
    - Live validation against APIs
    - Audit logging (no values logged)
    - Automatic redaction
    
    Usage:
        mgr = CredentialManager()
        
        # Simple get
        token = mgr.get("github_token")
        
        # With validation
        token = mgr.require("github_token", ["repo"])
        
        # Store new credential
        mgr.add("my_api_key", "secret_value", "custom_service")
        
        # Check status
        status = mgr.status()
    """
    
    # Known service configurations
    SERVICES = {
        "github": {
            "required_scopes": ["repo"],
            "validate_endpoint": "https://api.github.com/user",
            "env_vars": ["GITHUB_TOKEN", "GITHUB_PAT"]
        },
        "agentmail": {
            "env_vars": ["AGENTMAIL_API_KEY"]
        },
        "abund": {
            "env_vars": ["ABUND_API_KEY"]
        },
        "openrouter": {
            "env_vars": ["OPENROUTER_API_KEY"]
        }
    }
    
    def __init__(self):
        # Initialize storage backends
        self.file_storage = FileStorage()
        self.env_storage = EnvVarFallback()
        self.storage = ChainedStorage([self.env_storage, self.file_storage])
        
        # Initialize validator and audit logger
        self.validator = CredentialValidator()
        self.audit = AuditLogger()
        
        # Track which skill is requesting
        self._current_skill = self._detect_calling_skill()
    
    def _detect_calling_skill(self) -> str:
        """Detect which skill is making the call."""
        try:
            # Walk up call stack looking for skill pattern
            import inspect
            for frame in inspect.stack():
                filename = frame.filename
                if "skills/skill-" in filename:
                    # Extract skill name from path
                    match = re.search(r'skills/skill-([^/]+)', filename)
                    if match:
                        return f"skill-{match.group(1)}"
                elif "/home/rock/.openclaw/workspace/skills/" in filename:
                    match = re.search(r'skills/([^/]+)', filename)
                    if match:
                        return match.group(1)
        except:
            pass
        
        return "unknown"
    
    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get credential value.
        
        Args:
            name: Credential name
            default: Default if not found
            
        Returns:
            Credential value or default
        """
        entry = self.storage.get(name)
        
        if entry:
            # Mark as used
            entry.mark_used()
            self.file_storage.set(entry)  # Update last_used
            
            # Audit log
            self.audit.log(name, entry.service, "get", 
                          self._current_skill, True)
            
            return entry.value
        
        return default
    
    def require(self, name: str, required_scopes: Optional[List[str]] = None) -> str:
        """
        Get credential, raise if not found or invalid scopes.
        
        Args:
            name: Credential name
            required_scopes: Required scopes for validation
            
        Returns:
            Credential value
            
        Raises:
            CredentialNotFoundError: If credential not available
            InsufficientScopesError: If scopes don't match
        """
        entry = self.storage.get(name)
        
        if not entry:
            self.audit.log(name, "unknown", "get", 
                          self._current_skill, False, "Not found")
            raise CredentialNotFoundError(f"Credential '{name}' not found")
        
        # Validate if we have a validator for the service
        if entry.service in self.SERVICES:
            service_config = self.SERVICES[entry.service]
            
            # Check required scopes
            required = required_scopes or service_config.get("required_scopes", [])
            if required:
                has_all, missing = self.validator.check_required_scopes(
                    entry.scopes, required
                )
                
                if not has_all:
                    error = f"Missing scopes: {', '.join(missing)}"
                    self.audit.log(name, entry.service, "get",
                                  self._current_skill, False, error)
                    raise InsufficientScopesError(error)
        
        # Mark as used
        entry.mark_used()
        self.file_storage.set(entry)
        
        # Audit log
        self.audit.log(name, entry.service, "get",
                      self._current_skill, True)
        
        return entry.value
    
    def add(self, name: str, value: str, service: str,
           scopes: Optional[List[str]] = None,
           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a new credential.
        
        Args:
            name: Credential name (e.g., 'github_token')
            value: The actual credential value
            service: Service identifier (e.g., 'github', 'agentmail')
            scopes: List of permissions/scopes
            metadata: Additional metadata dict
            
        Returns:
            True if stored successfully
        """
        # Validate name
        if not re.match(r'^[a-zA-Z0-9_]+$', name):
            raise ValueError(f"Invalid credential name: {name}. Use alphanumeric + underscore only.")
        
        entry = CredentialEntry(
            name=name,
            value=value,
            service=service,
            scopes=scopes or [],
            metadata=metadata or {}
        )
        
        success = self.file_storage.set(entry)
        
        # Audit log
        self.audit.log(name, service, "set",
                      self._current_skill, success)
        
        return success
    
    def delete(self, name: str) -> bool:
        """Delete a credential."""
        success = self.storage.delete(name)
        
        self.audit.log(name, "unknown", "delete",
                      self._current_skill, success)
        
        return success
    
    def validate(self, name: str) -> ValidationResult:
        """
        Validate credential against live API.
        
        Args:
            name: Credential name to validate
            
        Returns:
            ValidationResult status
        """
        entry = self.storage.get(name)
        
        if not entry:
            return ValidationResult.UNKNOWN
        
        # Use appropriate validator
        if entry.service == "github":
            result, scopes, error = self.validator.validate_github(entry.value)
            
            # Update entry with scopes and status
            entry.scopes = scopes or []
            entry.validation_status = result.value
            self.file_storage.set(entry)
            
            # Audit log
            self.audit.log(name, entry.service, "validate",
                          self._current_skill, result == ValidationResult.VALID,
                          error if result != ValidationResult.VALID else None)
            
            return result
        
        elif entry.service == "agentmail":
            result, scopes, error = self.validator.validate_agentmail(entry.value)
            entry.validation_status = result.value
            self.file_storage.set(entry)
            return result
        
        return ValidationResult.UNKNOWN
    
    def status(self) -> Dict[str, CredentialInfo]:
        """
        Get status of all credentials (without values).
        
        Returns:
            Dict of credential name -> CredentialInfo
        """
        result = {}
        
        # Check both file and env storage
        all_names = set()
        all_names.update(self.file_storage.list_credentials())
        all_names.update(self.env_storage.list_credentials())
        
        for name in all_names:
            entry = self.file_storage.get(name) or self.env_storage.get(name)
            
            if entry:
                source = "env" if self.env_storage.exists(name) else "file"
                
                result[name] = CredentialInfo(
                    name=entry.name,
                    service=entry.service,
                    scopes=entry.scopes,
                    created_at=entry.created_at,
                    last_used=entry.last_used,
                    validation_status=entry.validation_status,
                    source=source,
                    masked_value=self._mask(entry.value) if entry.value else ""
                )
        
        return result
    
    def get_audit_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get audit statistics."""
        return self.audit.get_stats(days)
    
    def exists(self, name: str) -> bool:
        """Check if credential exists in any backend."""
        return self.storage.exists(name)
    
    def _mask(self, value: str) -> str:
        """Mask credential value for display."""
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"


# Exception classes
class CredentialNotFoundError(Exception):
    """Raised when required credential not found."""
    pass


class InsufficientScopesError(Exception):
    """Raised when credential lacks required scopes."""
    pass


# -- Discovery & Import --

def check_first_run_status(filepath: Path) -> bool:
    """Check if this is the first time status has been run."""
    marker = filepath.parent / ".discovery_completed"
    return not marker.exists()

def mark_discovery_completed(filepath: Path):
    """Mark that discovery has been completed."""
    marker = filepath.parent / ".discovery_completed"
    marker.touch()
    os.chmod(marker, 0o600)

# Convenience function for backward compatibility
def get_credential(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Quick access function for other skills.
    
    Usage:
        from credential_manager import get_credential
        token = get_credential("github_token")
    """
    mgr = CredentialManager()
    return mgr.get(name, default)


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Credential Manager CLI")
    parser.add_argument("command", 
                     choices=["status", "add", "get", "delete", "validate", "discover"],
                     help="Command to run")
    parser.add_argument("--name", help="Credential name")
    parser.add_argument("--value", help="Credential value (for add)")
    parser.add_argument("--service", help="Service name (for add)")
    parser.add_argument("--scopes", help="Required scopes (comma-separated)")
    parser.add_argument("--auto-import", action="store_true", 
                       help="Auto-import discovered credentials (for discover)")
    parser.add_argument("--no-prompt", action="store_true",
                       help="Skip interactive prompts (for scripts)")
    
    args = parser.parse_args()
    
    mgr = CredentialManager()
    
    if args.command == "status":
        print("\n🔐 Credential Status\n" + "="*60)
        status = mgr.status()
        
        if not status:
            print("No credentials configured")
        else:
            for name, info in sorted(status.items()):
                icon = "✅" if info.validation_status == "valid" else "❓"
                print(f"\n{icon} {name}")
                print(f"   Service: {info.service}")
                print(f"   Source: {info.source}")
                print(f"   Token: {info.masked_value}")
                print(f"   Scopes: {', '.join(info.scopes) or 'N/A'}")
                print(f"   Created: {info.created_at[:10]}")
                if info.last_used:
                    print(f"   Last used: {info.last_used[:10]}")
        
            # Show audit stats
        stats = mgr.get_audit_stats(days=7)
        print(f"\n📊 Audit (7 days): {stats['total_operations']} ops, "
              f"{stats['successful']} success")
        
        # Auto-discovery on first run
        creds_dir = mgr.file_storage.base_dir
        if check_first_run_status(creds_dir):
            print("\n🔍 First run detected - scanning for existing credentials...")
            discovered = CredentialDiscovery()
            found = discovered.discover_all()
            
            if found:
                print(f"\n✨ Found {len(found)} credential(s) to import:")
                for cred in found:
                    print(f"  • {cred.service.upper()}: {cred.suggested_name} (from {cred.source})")
                
                if not args.no_prompt:
                    print("\nRun: python3 lib/credential_manager.py discover")
                    print("To import these credentials with review.")
                
                mark_discovery_completed(creds_dir)
    
    elif args.command == "add":
        if not args.name or not args.value or not args.service:
            print("Usage: credential_manager.py add --name NAME --value VALUE --service SERVICE")
            sys.exit(1)
        
        scopes = args.scopes.split(",") if args.scopes else []
        
        if mgr.add(args.name, args.value, args.service, scopes):
            print(f"✅ Added credential: {args.name}")
        else:
            print("❌ Failed to add credential")
            sys.exit(1)
    
    elif args.command == "get":
        if not args.name:
            print("Usage: credential_manager.py get --name NAME")
            sys.exit(1)
        
        value = mgr.get(args.name)
        if value:
            print(value)  # Just print the value (for scripts)
        else:
            print(f"Credential '{args.name}' not found", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == "validate":
        if not args.name:
            print("Usage: credential_manager.py validate --name NAME")
            sys.exit(1)
        
        print(f"Validating {args.name}...")
        result = mgr.validate(args.name)
        print(f"Result: {result.value}")
    
    elif args.command == "delete":
        if not args.name:
            print("Usage: credential_manager.py delete --name NAME")
            sys.exit(1)
        
        if mgr.delete(args.name):
            print(f"✅ Deleted: {args.name}")
        else:
            print(f"❌ Failed to delete: {args.name}")
    
    elif args.command == "discover":
        print("\n🔍 Scanning for credentials...")
        discovery = CredentialDiscovery()
        found = discovery.discover_all()
        
        if not found:
            print("No credentials found in common locations.")
            print("\nSearched:")
            print("  • Environment variables")
            print("  • ~/.openclaw/credentials/*.env")
            print("  • ~/.openclaw/workspace/config/*.yaml")
            print("  • Common .env files")
        else:
            print(f"\n✨ Found {len(found)} credential(s):\n")
            print(discovery.generate_report())
            
            if args.auto_import:
                print("\n🚀 Auto-importing non-critical credentials...")
                imported = 0
                skipped = 0
                
                for cred in found:
                    # Check if already exists
                    if mgr.exists(cred.suggested_name):
                        print(f"  ⏭️  {cred.suggested_name}: already exists")
                        skipped += 1
                        continue
                    
                    # Critical services require manual review
                    from discover import CredentialDiscovery
                    patterns = CredentialDiscovery.CREDENTIAL_PATTERNS
                    config = patterns.get(cred.service, {})
                    
                    if config.get('critical') and not args.no_prompt:
                        print(f"  ⚠️  {cred.suggested_name}: critical service, manual import required")
                        print(f"      Run: python3 lib/credential_manager.py add --name {cred.suggested_name} --service {cred.service}")
                        skipped += 1
                        continue
                    
                    # Import
                    if mgr.add(cred.suggested_name, cred.value, cred.service, cred.scopes):
                        print(f"  ✅ {cred.suggested_name}: imported")
                        imported += 1
                    else:
                        print(f"  ❌ {cred.suggested_name}: failed to import")
                        skipped += 1
                
                print(f"\n Imported: {imported}, Skipped: {skipped}")
            else:
                print("\nTo import, run with --auto-import flag:")
                print("  python3 lib/credential_manager.py discover --auto-import")


# Self-test
if __name__ == "__main__" and not any(arg.startswith("-") for arg in sys.argv if arg != __file__):
    print("Running self-verification tests...\n")
    
    # Create temp storage for tests
    import tempfile
    test_dir = Path(tempfile.mkdtemp(prefix="cred_test_"))
    
    mgr = CredentialManager()
    mgr.file_storage.base_dir = test_dir
    
    # Test add/get
    assert mgr.add("test_github", "ghp_test12345", "github", ["repo"])
    assert mgr.get("test_github") == "ghp_test12345"
    print("✓ Add/Get works")
    
    # Test status
    status = mgr.status()
    assert "test_github" in status
    print("✓ Status works")
    
    # Test delete
    assert mgr.delete("test_github")
    assert mgr.get("test_github") is None
    print("✓ Delete works")
    
    # Cleanup
    import shutil
    shutil.rmtree(test_dir)
    
    print("\n✓ All credential manager tests passed")
