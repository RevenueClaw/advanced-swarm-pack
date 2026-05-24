#!/usr/bin/env python3
"""
Credential Discovery & Import Module
Intelligently scans and imports existing credentials from common locations.

v1.0.2 Enhancement - Production Ready
"""

import os
import re
import glob
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import yaml


@dataclass
class DiscoveredCredential:
    """Represents a discovered but not yet imported credential."""
    source: str          # File path or 'environment'
    credential_type: str  # 'github_token', 'openrouter_api_key', etc.
    service: str          # 'github', 'openrouter', 'agentmail', etc.
    value: str           # The actual token/key
    confidence: float     # 0-1, based on regex pattern match
    scopes: Optional[List[str]] = None
    source_line: Optional[str] = None  # The original line from file
    suggested_name: str = ""


class CredentialDiscovery:
    """
    Discovers existing credentials from various sources.
    
    Priority (higher = preferred):
    1. Environment variables (current session)
    2. ~/.openclaw/credentials/*.env
    3. ~/.openclaw/workspace/config/*.{yaml,yml}
    4. Common root .env files
    5. Ollama configs
    
    Safety: Never auto-import without user review for sensitive credentials.
    """
    
    # Credential patterns to detect
    CREDENTIAL_PATTERNS = {
        'github': {
            'env_vars': ['GITHUB_TOKEN', 'GITHUB_PAT', 'GITHUB_PERSONAL_ACCESS_TOKEN', 'GITHUB_API_TOKEN'],
            'file_patterns': ['github.env', '*github*.env', '.github_token'],
            'regex': r'(?:ghp_|gho_|ghu_|ghs_|ghr_)[a-zA-Z0-9]{36}',
            'service': 'github',
            'critical': True,  # Requires user confirmation
        },
        'agentmail': {
            'env_vars': ['AGENTMAIL_API_KEY', 'AGENTMAIL_KEY', 'AGENTMAIL_TOKEN'],
            'file_patterns': ['agentmail.env', '*agentmail*'],
            'regex': r'(?:agent_)?[a-zA-Z0-9]{32,64}',
            'service': 'agentmail',
            'critical': True,
        },
        'openrouter': {
            'env_vars': ['OPENROUTER_API_KEY', 'OPENROUTER_KEY'],
            'file_patterns': ['openrouter*', '.openrouter*'],
            'regex': r'sk-or-[a-zA-Z0-9]{48}',
            'service': 'openrouter',
            'critical': True,
        },
        'abund': {
            'env_vars': ['ABUND_API_KEY', 'ABUND_KEY', 'ABUND_TOKEN'],
            'file_patterns': ['abund*', '.abund*'],
            'regex': r'abund_[a-zA-Z0-9]{32,48}',
            'service': 'abund',
            'critical': True,
        },
        'ollama': {
            'env_vars': ['OLLAMA_HOST', 'OLLAMA_API_KEY'],
            'file_patterns': ['ollama.conf', '.ollama*'],
            'regex': r'ollama[_-]?[a-zA-Z0-9]{16,32}',
            'service': 'ollama',
            'critical': False,  # Can auto-import
        },
    }
    
    def __init__(self):
        self.discovered: List[DiscoveredCredential] = []
        self.home = Path.home()
        self.workspace = self.home / ".openclaw/workspace"
    
    def discover_all(self) -> List[DiscoveredCredential]:
        """
        Run full discovery scan across all sources.
        
        Returns:
            List of discovered credentials (may include duplicates)
        """
        self.discovered = []
        
        # Source 1: Environment variables
        self._scan_environment()
        
        # Source 2: ~/.openclaw/credentials/*.env
        self._scan_old_credentials()
        
        # Source 3: Config files
        self._scan_configs()
        
        # Source 4: Common root .env files
        self._scan_root_envs()
        
        # Source 5: Ollama configs
        self._scan_ollama_configs()
        
        # Deduplicate (prefer higher confidence, then env vars)
        return self._deduplicate()
    
    def _scan_environment(self):
        """Scan environment variables for credentials."""
        for cred_type, config in self.CREDENTIAL_PATTERNS.items():
            for env_var in config['env_vars']:
                value = os.getenv(env_var)
                if value and len(value) > 10:  # Basic validation
                    confidence = self._calculate_confidence(value, config['regex'])
                    self.discovered.append(DiscoveredCredential(
                        source='environment',
                        credential_type=f"{cred_type}_token",
                        service=config['service'],
                        value=value,
                        confidence=min(confidence * 1.2, 1.0),  # Boost env vars
                        scopes=None,
                        suggested_name=f"{cred_type}_{self._token_suffix(cred_type)}"
                    ))
    
    def _scan_old_credentials(self):
        """Scan ~/.openclaw/credentials/*.env files."""
        creds_dir = self.home / ".openclaw/credentials"
        if not creds_dir.exists():
            return
        
        for env_file in creds_dir.glob("*.env"):
            self._parse_env_file(str(env_file), env_file.name)
    
    def _scan_configs(self):
        """Scan YAML config files."""
        config_dir = self.workspace / "config"
        if not config_dir.exists():
            return
        
        for yaml_file in config_dir.glob("*.yaml"):
            self._parse_yaml_file(yaml_file)
        
        for yml_file in config_dir.glob("*.yml"):
            self._parse_yaml_file(yml_file)
    
    def _scan_root_envs(self):
        """Scan common root-level .env or config files."""
        # Root level common locations
        root_paths = [
            self.workspace / ".env",
            self.workspace / "config.env",
            self.workspace / "secrets.env",
        ]
        
        for path in root_paths:
            if path.exists():
                self._parse_env_file(str(path), path.name)
    
    def _scan_ollama_configs(self):
        """Scan Ollama configuration files."""
        ollama_paths = [
            self.home / ".ollama" / "config.json",
            self.workspace / "ollama.conf",
            Path("/etc/ollama/config.json"),
        ]
        
        for path in ollama_paths:
            if path.exists():
                self._parse_json_config(path, 'ollama')
    
    def _parse_env_file(self, filepath: str, filename: str):
        """Parse a .env file for credentials."""
        try:
            with open(filepath) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Look for KEY=value patterns
                    if '=' not in line:
                        continue
                    
                    # Try to detect credential type from key name
                    key, value = line.split('=', 1)
                    key = key.strip().upper()
                    value = value.strip().strip('"\'')
                    
                    if len(value) < 10:
                        continue  # Too short to be valid
                    
                    # Detect service from key name
                    for cred_type, config in self.CREDENTIAL_PATTERNS.items():
                        if any(var in key.lower() for var in 
                               [v.lower().replace('_', '') for v in config['env_vars']]):
                            
                            confidence = self._calculate_confidence(value, config['regex'])
                            self.discovered.append(DiscoveredCredential(
                                source=f"{filepath}:{line_num}",
                                credential_type=f"{cred_type}_token",
                                service=config['service'],
                                value=value,
                                confidence=confidence,
                                source_line=line,
                                suggested_name=f"{cred_type}_{filename.split('.')[0]}"
                            ))
                            break
        except Exception as e:
            print(f"Warning: Could not parse {filepath}: {e}")
    
    def _parse_yaml_file(self, filepath: Path):
        """Parse YAML config for credentials."""
        try:
            with open(filepath) as f:
                data = yaml.safe_load(f) or {}
            
            # Recursive search for credential-like keys
            self._search_yaml_tree(data, str(filepath))
        except Exception as e:
            print(f"Warning: Could not parse YAML {filepath}: {e}")
    
    def _search_yaml_tree(self, data, path: str, key: str = ""):
        """Recursively search YAML tree for credentials."""
        if isinstance(data, dict):
            for k, v in data.items():
                self._search_yaml_tree(v, path, k)
        elif isinstance(data, str):
            # Check if value looks like a credential
            if self._looks_like_credential(data):
                for cred_type, config in self.CREDENTIAL_PATTERNS.items():
                    if re.search(config['regex'], data, re.IGNORECASE):
                        confidence = self._calculate_confidence(data, config['regex'])
                        self.discovered.append(DiscoveredCredential(
                            source=f"{path} (key: {key})",
                            credential_type=f"{cred_type}_token",
                            service=config['service'],
                            value=data,
                            confidence=confidence,
                            suggested_name=f"{cred_type}_{Path(path).stem}"
                        ))
    
    def _parse_json_config(self, filepath: Path, service: str):
        """Parse JSON config file."""
        try:
            import json
            with open(filepath) as f:
                data = json.load(f)
            
            # Look for known keys in JSON
            for key in ['token', 'api_key', 'key', 'secret']:
                if key in data:
                    value = data[key]
                    if isinstance(value, str) and len(value) > 10:
                        config = self.CREDENTIAL_PATTERNS.get(service, {})
                        confidence = self._calculate_confidence(
                            value, 
                            config.get('regex', r'\w+')
                        )
                        self.discovered.append(DiscoveredCredential(
                            source=str(filepath),
                            credential_type=f"{service}_token",
                            service=service,
                            value=value,
                            confidence=confidence,
                            suggested_name=f"{service}_json_key"
                        ))
        except Exception as e:
            print(f"Warning: Could not parse JSON {filepath}: {e}")
    
    def _calculate_confidence(self, value: str, pattern: str) -> float:
        """Calculate confidence score for a credential match."""
        if not value or len(value) < 10:
            return 0.0
        
        # Regex match
        if re.search(pattern, value):
            base_confidence = 0.9
        else:
            base_confidence = 0.5
        
        # Length heuristic
        if len(value) > 30:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _looks_like_credential(self, value: str) -> bool:
        """Quick heuristics for credential-like strings."""
        if not value or len(value) < 20:
            return False
        if len(value) > 300:
            return False  # Probably not a key
        if ' ' in value:
            return False  # Has spaces
        if '\n' in value:
            return False
        
        # Check for common token patterns
        credential_indicators = [
            r'^ghp_',          # GitHub personal
            r'^sk-',           # OpenRouter/Stripe style
            r'^agent_',        # AgentMail
            r'^abund_',        # Abund
            r'^[a-f0-9]{32}',  # Hex hash style
            r'^[A-Za-z0-9]{20,}',  # Base64-like
        ]
        
        for pattern in credential_indicators:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        
        return False
    
    def _deduplicate(self) -> List[DiscoveredCredential]:
        """
        Remove duplicates, keeping highest confidence entry.
        Prefer environment variables over files.
        """
        seen = {}  # value_hash -> DiscoveredCredential
        
        # Sort by source priority (env first, then by confidence)
        sorted_creds = sorted(
            self.discovered,
            key=lambda x: (0 if x.source == 'environment' else 1, -x.confidence)
        )
        
        for cred in sorted_creds:
            # Create hash of value
            value_hash = hash(cred.value) % 1000000
            
            if value_hash not in seen:
                seen[value_hash] = cred
            elif cred.confidence > seen[value_hash].confidence:
                seen[value_hash] = cred
        
        return list(seen.values())
    
    def _token_suffix(self, cred_type: str) -> str:
        """Generate appropriate suffix for credential name."""
        suffixes = {
            'github': 'token',
            'agentmail': 'api_key',
            'openrouter': 'api_key',
            'abund': 'api_key',
            'ollama': 'config',
        }
        return suffixes.get(cred_type, 'key')
    
    def generate_report(self) -> str:
        """Generate human-readable discovery report."""
        discovered = self.discover_all()
        
        if not discovered:
            return "No credentials discovered in common locations."
        
        lines = [
            "🔍 CREDENTIAL DISCOVERY REPORT",
            "=" * 60,
            f"Found {len(discovered)} potential credential(s):\n"
        ]
        
        for i, cred in enumerate(discovered, 1):
            icon = "✅" if cred.confidence > 0.8 else "🟡"
            mask = cred.value[:4] + "***" + cred.value[-4:] if len(cred.value) > 12 else "***"
            
            lines.append(f"{i}. {icon} {cred.service.upper()} - Confidence: {cred.confidence:.0%}")
            lines.append(f"   Suggested name: {cred.suggested_name}")
            lines.append(f"   Source: {cred.source}")
            lines.append(f"   Token preview: {mask}")
            
            if config := self.CREDENTIAL_PATTERNS.get(cred.service):
                if config.get('critical'):
                    lines.append(f"   ⚠️  Requires user confirmation (critical service)")
            lines.append("")
        
        return "\n".join(lines)


# Self-test
if __name__ == "__main__":
    print("Running credential discovery self-test...\n")
    
    # Set up test environment
    os.environ['TEST_DISCOVERY_TOKEN'] = 'ghp_test1234567890abcdef1234567890123456'
    
    # Temporarily add to patterns
    CredentialDiscovery.CREDENTIAL_PATTERNS['test'] = {
        'env_vars': ['TEST_DISCOVERY_TOKEN'],
        'service': 'test',
        'regex': r'^ghp_',
        'critical': False,
    }
    
    discoverer = CredentialDiscovery()
    
    # Check if environment scan works
    discoverer._scan_environment()
    
    if discoverer.discovered:
        print("✓ Environment variable discovery works")
        print(f"  Found {len(discoverer.discovered)} test credential(s)")
    else:
        print("⚠️ No credentials in test environment")