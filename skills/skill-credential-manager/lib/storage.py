#!/usr/bin/env python3
"""
Storage backends for credential manager.
Pluggable architecture supporting multiple storage methods.

v1.0.2 - Production Release
"""

import os
import stat
import json
import hashlib
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime


class CredentialEntry:
    """Represents a stored credential."""
    def __init__(self, name: str, value: str, service: str,
                 scopes: Optional[list] = None, metadata: Optional[dict] = None):
        self.name = name
        self.value = value
        self.service = service
        self.scopes = scopes or []
        self.created_at = datetime.now().isoformat()
        self.last_used = None
        self.validation_status = "pending"
        self.metadata = metadata or {}
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "service": self.service,
            "scopes": self.scopes,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "validation_status": self.validation_status,
            "metadata": self.metadata
            # Note: value is NOT stored in dict for security
        }
    
    def mark_used(self):
        """Update last_used timestamp."""
        self.last_used = datetime.now().isoformat()


class StorageBackend(ABC):
    """Abstract base class for credential storage."""
    
    @abstractmethod
    def get(self, name: str) -> Optional[CredentialEntry]:
        """Retrieve credential by name."""
        pass
    
    @abstractmethod
    def set(self, entry: CredentialEntry) -> bool:
        """Store credential entry."""
        pass
    
    @abstractmethod
    def delete(self, name: str) -> bool:
        """Delete credential by name."""
        pass
    
    @abstractmethod
    def list_credentials(self) -> list:
        """List all stored credential names."""
        pass
    
    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if credential exists."""
        pass


class FileStorage(StorageBackend):
    """
    File-based storage with secure permissions (600).
    Stores each credential in a separate JSON file.
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path.home() / ".openclaw/credentials"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure directory is secure
        self._secure_path(self.base_dir, is_dir=True)
        
        # Index file for metadata
        self.index_file = self.base_dir / ".credential_index"
        self._init_index()
    
    def _init_index(self):
        """Initialize metadata index."""
        if not self.index_file.exists():
            self._write_index({})
    
    def _get_credential_file(self, name: str) -> Path:
        """Get path for credential file."""
        # Hash name for filename to avoid special characters
        filename = hashlib.sha256(name.encode()).hexdigest()[:16] + ".cred"
        return self.base_dir / filename
    
    def _read_index(self) -> dict:
        """Read metadata index."""
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _write_index(self, data: dict):
        """Write metadata index."""
        temp_file = self.index_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2)
        os.chmod(temp_file, stat.S_IRUSR | stat.S_IWUSR)
        temp_file.replace(self.index_file)
    
    def _secure_path(self, path: Path, is_dir: bool = False):
        """Ensure path has secure permissions."""
        if is_dir:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)  # 700
        else:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 600
    
    def get(self, name: str) -> Optional[CredentialEntry]:
        """Retrieve credential."""
        cred_file = self._get_credential_file(name)
        
        if not cred_file.exists():
            return None
        
        try:
            with open(cred_file, 'r') as f:
                data = json.load(f)
            
            entry = CredentialEntry(
                name=data["name"],
                value=data["value"],
                service=data["service"],
                scopes=data.get("scopes", []),
                metadata=data.get("metadata", {})
            )
            entry.created_at = data.get("created_at", entry.created_at)
            entry.last_used = data.get("last_used")
            entry.validation_status = data.get("validation_status", "pending")
            
            return entry
            
        except Exception as e:
            print(f"Error reading credential {name}: {e}")
            return None
    
    def set(self, entry: CredentialEntry) -> bool:
        """Store credential."""
        cred_file = self._get_credential_file(entry.name)
        
        try:
            # Write to temp file first
            temp_file = cred_file.with_suffix('.tmp')
            data = entry.to_dict()
            data["value"] = entry.value  # Include actual value only here
            
            with open(temp_file, 'w') as f:
                json.dump(data, f)
            
            # Secure permissions before moving
            self._secure_path(temp_file)
            
            # Atomic move
            temp_file.replace(cred_file)
            
            # Update index
            index = self._read_index()
            index[entry.name] = {
                "service": entry.service,
                "created_at": entry.created_at
            }
            self._write_index(index)
            
            return True
            
        except Exception as e:
            print(f"Error storing credential: {e}")
            return False
    
    def delete(self, name: str) -> bool:
        """Delete credential."""
        cred_file = self._get_credential_file(name)
        
        try:
            if cred_file.exists():
                cred_file.unlink()
            
            # Update index
            index = self._read_index()
            if name in index:
                del index[name]
                self._write_index(index)
            
            return True
            
        except Exception as e:
            print(f"Error deleting credential {name}: {e}")
            return False
    
    def list_credentials(self) -> list:
        """List all credential names."""
        index = self._read_index()
        return list(index.keys())
    
    def exists(self, name: str) -> bool:
        """Check if credential exists."""
        cred_file = self._get_credential_file(name)
        return cred_file.exists()
    
    def get_metadata(self, name: str) -> Optional[dict]:
        """Get metadata without value."""
        index = self._read_index()
        return index.get(name)


class EnvVarFallback(StorageBackend):
    """
    Fallback storage that checks environment variables.
    Read-only - doesn't store, only retrieves.
    """
    
    # Mapping of credential names to env vars
    ENV_MAP = {
        "github_token": ["GITHUB_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN"],
        "agentmail_api_key": ["AGENTMAIL_API_KEY", "AGENTMAIL_KEY"],
        "abund_api_key": ["ABUND_API_KEY", "ABUND_KEY"],
        "openrouter_api_key": ["OPENROUTER_API_KEY", "OPENROUTER_TOKEN"],
    }
    
    SERVICE_SCOPES = {
        "github": ["repo", "workflow", "read:org"],
        "agentmail": [],
        "abund": [],
        "openrouter": [],
    }
    
    def get(self, name: str) -> Optional[CredentialEntry]:
        """Try to get from env vars."""
        env_vars = self.ENV_MAP.get(name, [name.upper()])
        
        for var in env_vars:
            value = os.getenv(var)
            if value:
                # Determine service from name
                service = name.split('_')[0] if '_' in name else 'unknown'
                
                entry = CredentialEntry(
                    name=name,
                    value=value,
                    service=service,
                    scopes=self.SERVICE_SCOPES.get(service, []),
                    metadata={"source": "environment", "env_var": var}
                )
                entry.validation_status = "loaded_from_env"
                return entry
        
        return None
    
    def set(self, entry: CredentialEntry) -> bool:
        """Cannot set via env var backend."""
        return False
    
    def delete(self, name: str) -> bool:
        """Cannot delete env vars."""
        return False
    
    def list_credentials(self) -> list:
        """List env vars that match credentials."""
        found = []
        for name, vars in self.ENV_MAP.items():
            if any(os.getenv(v) for v in vars):
                found.append(name)
        return found
    
    def exists(self, name: str) -> bool:
        """Check if exists in env."""
        return self.get(name) is not None


class ChainedStorage(StorageBackend):
    """
    Chains multiple backends with priority order.
    Tries first backend, falls through to others.
    """
    
    def __init__(self, backends: list):
        self.backends = backends
    
    def get(self, name: str) -> Optional[CredentialEntry]:
        """Try each backend in order."""
        for backend in self.backends:
            entry = backend.get(name)
            if entry:
                return entry
        return None
    
    def set(self, entry: CredentialEntry) -> bool:
        """Store in first writable backend."""
        for backend in self.backends:
            if backend.set(entry):
                return True
        return False
    
    def delete(self, name: str) -> bool:
        """Delete from first backend that has it."""
        for backend in self.backends:
            if backend.exists(name):
                return backend.delete(name)
        return False
    
    def list_credentials(self) -> list:
        """Union of all credentials from all backends."""
        all_creds = set()
        for backend in self.backends:
            all_creds.update(backend.list_credentials())
        return list(all_creds)
    
    def exists(self, name: str) -> bool:
        """Check if exists in any backend."""
        return any(b.exists(name) for b in self.backends)


# Self-test
if __name__ == "__main__":
    print("Testing FileStorage...")
    
    # Test file storage
    storage = FileStorage()
    
    entry = CredentialEntry(
        name="test_github",
        value="ghp_test_token_12345",
        service="github",
        scopes=["repo"]
    )
    
    # Store
    assert storage.set(entry), "Failed to store"
    print("✓ Store successful")
    
    # Retrieve
    retrieved = storage.get("test_github")
    assert retrieved and retrieved.value == entry.value, "Retrieval failed"
    print("✓ Retrieve successful")
    
    # List
    creds = storage.list_credentials()
    assert "test_github" in creds, "List failed"
    print("✓ List successful")
    
    # Delete
    assert storage.delete("test_github"), "Delete failed"
    print("✓ Delete successful")
    
    # Cleanup
    print("\n✓ All storage tests passed")
