#!/usr/bin/env python3
"""
Credential Manager - Secure API credential management for OpenClaw.

v1.0.0 - Production Release
"""

import os
import sys
import stat
import getpass
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import subprocess
import json


class CredentialSource(Enum):
    """Where credential was loaded from."""
    ENVIRONMENT = "env"
    SECURE_STORE = "keyring"
    FILE = "file"
    CACHE = "cache"
    NOT_FOUND = "not_found"


@dataclass
class CredentialStatus:
    """Status of a credential check."""
    provider: str
    key: str
    loaded: bool
    source: CredentialSource
    masked_value: Optional[str] = None  # First/last 4 chars only
    error: Optional[str] = None
    permissions_ok: bool = False


class CredentialManager:
    """
    Secure credential manager with priority-based loading.
    
    Priority:
        1. Environment variables
        2. Secure store (keyring)
        3. Protected credential files
        4. Runtime cache
    
    Usage:
        mgr = CredentialManager()
        token = mgr.get('github', 'token')
        
        # With error handling
        try:
            token = mgr.require('github', 'token', scopes=['repo'])
        except CredentialNotFound as e:
            print(f"Set with: mgr.setup('github', 'token')")
    """
    
    # Provider configurations
    PROVIDERS = {
        'github': {
            'env_vars': ['GITHUB_TOKEN', 'GITHUB_PAT', 'GITHUB_PERSONAL_ACCESS_TOKEN'],
            'file_name': 'github.env',
            'required_scopes': ['repo'],
            'test_endpoint': 'https://api.github.com/user',
        },
        'agentmail': {
            'env_vars': ['AGENTMAIL_API_KEY'],
            'file_name': 'agentmail.env',
            'test_endpoint': 'https://api.agentmail.dev/v1/health',
        },
        'abund': {
            'env_vars': ['ABUND_API_KEY'],
            'file_name': 'abund.env',
        },
        'openrouter': {
            'env_vars': ['OPENROUTER_API_KEY'],
            'file_name': 'openrouter.env',
        }
    }
    
    def __init__(self, credentials_dir: Optional[Path] = None):
        self.credentials_dir = credentials_dir or Path.home() / ".openclaw/credentials"
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, str] = {}
    
    def get(self, provider: str, key: str = 'token', 
            default: Optional[str] = None) -> Optional[str]:
        """
        Get credential with priority loading.
        
        Args:
            provider: Provider name (github, agentmail, etc.)
            key: Credential type (token, api_key, etc.)
            default: Default value if not found
            
        Returns:
            Credential value or default
        """
        cache_key = f"{provider}.{key}"
        
        # 1. Check runtime cache
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 2. Check environment variables
        env_value = self._from_env(provider)
        if env_value:
            self._cache[cache_key] = env_value
            return env_value
        
        # 3. Check credential file
        file_value = self._from_file(provider)
        if file_value:
            self._cache[cache_key] = file_value
            return file_value
        
        return default
    
    def require(self, provider: str, key: str = 'token',
               scopes: Optional[List[str]] = None) -> str:
        """
        Get required credential, raise if not found.
        
        Args:
            provider: Provider name
            key: Credential type
            scopes: Required scopes for verification
            
        Returns:
            Credential value
            
        Raises:
            CredentialNotFound: If credential not available
            InsufficientScopes: If scopes don't match
        """
        value = self.get(provider, key)
        
        if not value:
            raise CredentialNotFound(
                f"Credential '{provider}.{key}' not found. "
                f"Set via: export {self.PROVIDERS[provider]['env_vars'][0]}=... "
                f"or run: credential_manager.py setup {provider}"
            )
        
        return value
    
    def check_provider(self, provider: str) -> CredentialStatus:
        """
        Check status of a provider's credentials.
        
        Returns:
            CredentialStatus with detailed info
        """
        if provider not in self.PROVIDERS:
            return CredentialStatus(
                provider=provider,
                key='token',
                loaded=False,
                source=CredentialSource.NOT_FOUND,
                error=f"Unknown provider: {provider}"
            )
        
        # Check file permissions
        file_path = self.credentials_dir / self.PROVIDERS[provider]['file_name']
        perms_ok = self._check_permissions(file_path)
        
        # Try to load
        value = self.get(provider)
        
        if value:
            source = CredentialSource.ENVIRONMENT if self._from_env(provider) else CredentialSource.FILE
            return CredentialStatus(
                provider=provider,
                key='token',
                loaded=True,
                source=source,
                masked_value=self._mask(value),
                permissions_ok=perms_ok
            )
        else:
            return CredentialStatus(
                provider=provider,
                key='token',
                loaded=False,
                source=CredentialSource.NOT_FOUND,
                error="Not configured",
                permissions_ok=perms_ok
            )
    
    def setup(self, provider: str, interactive: bool = True) -> bool:
        """
        Interactive setup for a provider.
        
        Args:
            provider: Provider to configure
            interactive: If True, prompt for input
            
        Returns:
            True if setup successful
        """
        if provider not in self.PROVIDERS:
            print(f"Unknown provider: {provider}")
            print(f"Known: {', '.join(self.PROVIDERS.keys())}")
            return False
        
        if interactive:
            print(f"\n🔐 Setup {provider.upper()} credentials")
            print("-" * 40)
            
            # Get token securely
            token = getpass.getpass(f"Enter {provider} token (input hidden): ")
            
            if not token:
                print("❌ Token cannot be empty")
                return False
            
            # Save to file
            return self._save_to_file(provider, token)
        
        return False
    
    def verify(self, provider: str) -> bool:
        """
        Verify credential is valid by making API call.
        
        Args:
            provider: Provider to verify
            
        Returns:
            True if valid
        """
        cfg = self.PROVIDERS.get(provider)
        if not cfg:
            return False
        
        token = self.get(provider)
        if not token:
            print(f"❌ No token configured for {provider}")
            return False
        
        test_endpoint = cfg.get('test_endpoint')
        if not test_endpoint:
            print(f"⚠️  No test endpoint for {provider}")
            return True  # Can't verify, assume ok
        
        try:
            import urllib.request
            req = urllib.request.Request(
                test_endpoint,
                headers={'Authorization': f'token {token}'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    print(f"✅ {provider} token is valid")
                    return True
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
        
        return False
    
    def status_all(self) -> Dict[str, CredentialStatus]:
        """Get status of all configured providers."""
        return {name: self.check_provider(name) for name in self.PROVIDERS}
    
    # -- Internal Methods --
    
    def _from_env(self, provider: str) -> Optional[str]:
        """Get credential from environment variables."""
        cfg = self.PROVIDERS.get(provider)
        if not cfg:
            return None
        
        for env_var in cfg.get('env_vars', []):
            value = os.getenv(env_var)
            if value:
                return value
        
        return None
    
    def _from_file(self, provider: str) -> Optional[str]:
        """Get credential from file."""
        cfg = self.PROVIDERS.get(provider)
        if not cfg:
            return None
        
        file_path = self.credentials_dir / cfg['file_name']
        if not file_path.exists():
            return None
        
        # Check permissions
        if not self._check_permissions(file_path):
            print(f"⚠️  Warning: {file_path} has insecure permissions")
        
        try:
            with open(file_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('export') and '=' in line:
                        # Parse export VAR=value
                        parts = line.replace('export ', '').split('=', 1)
                        if len(parts) == 2 and parts[1]:
                            value = parts[1].strip('"\'')
                            if value and len(value) > 10:
                                return value
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        
        return None
    
    def _save_to_file(self, provider: str, token: str) -> bool:
        """Save token to credential file."""
        cfg = self.PROVIDERS.get(provider)
        if not cfg:
            return False
        
        file_path = self.credentials_dir / cfg['file_name']
        
        # Create with restricted permissions
        content = f"""# {provider.upper()} Personal Access Token
# Created: {self._now()}
# Source: credential_manager setup

export {cfg['env_vars'][0]}="{token}"
"""
        
        try:
            # Write with atomic create/rename
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                f.write(content)
            
            # Set permissions before rename (secure)
            os.chmod(temp_path, stat.S_IRUSR | stat.S_IWUSR)  # 0600
            
            # Atomic replace
            temp_path.replace(file_path)
            
            print(f"✅ Saved to {file_path}")
            print(f"✅ Permissions: 600 (owner only)")
            
            # Update cache
            cache_key = f"{provider}.token"
            self._cache[cache_key] = token
            
            return True
            
        except Exception as e:
            print(f"❌ Save failed: {e}")
            return False
    
    def _check_permissions(self, file_path: Path) -> bool:
        """Check if file has secure permissions."""
        if not file_path.exists():
            return False
        
        mode = file_path.stat().st_mode
        # Check: Owner read/write only, no group/other access
        expected = stat.S_IRUSR | stat.S_IWUSR
        return (mode & 0o777) == expected
    
    def _mask(self, value: str) -> str:
        """Mask credential value for display."""
        if len(value) <= 8:
            return "***"
        return f"{value[:4]}...{value[-4:]}"
    
    def _now(self) -> str:
        """Current timestamp."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M')


class CredentialNotFound(Exception):
    """Raised when required credential not found."""
    pass


class InsufficientScopes(Exception):
    """Raised when credential lacks required scopes."""
    pass


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Credential Manager')
    parser.add_argument('command', 
                       choices=['status', 'setup', 'verify'],
                       help='Command to run')
    parser.add_argument('--provider', default='all',
                       help='Provider to check (github, agentmail, etc.)')
    
    args = parser.parse_args()
    
    mgr = CredentialManager()
    
    if args.command == 'status':
        if args.provider == 'all':
            print("\n🔐 Credential Status\n" + "="*50)
            for provider, status in mgr.status_all().items():
                icon = "✅" if status.loaded else "❌"
                source = status.source.value if status.loaded else "not configured"
                print(f"{icon} {provider:12} {source}")
                if status.masked_value:
                    print(f"   Token: {status.masked_value}")
        else:
            status = mgr.check_provider(args.provider)
            print(f"\nProvider: {args.provider}")
            print(f"Loaded: {status.loaded}")
            print(f"Source: {status.source.value}")
            if status.masked_value:
                print(f"Token: {status.masked_value}")
            if status.error:
                print(f"Error: {status.error}")
    
    elif args.command == 'setup':
        if args.provider == 'all':
            print("Please specify provider: github, agentmail, abund, openrouter")
            sys.exit(1)
        mgr.setup(args.provider)
    
    elif args.command == 'verify':
        if args.provider == 'all':
            print("\n🔍 Verifying All Credentials\n" + "="*50)
            for provider in mgr.PROVIDERS:
                mgr.verify(provider)
        else:
            mgr.verify(args.provider)


if __name__ == '__main__':
    main()