#!/usr/bin/env python3
"""
Comprehensive Credential Discovery System
Intelligently finds and imports existing credentials from all likely locations.

v1.0.2 - Production Release
"""

import os
import re
import json
import glob
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DiscoveredCredential:
    """Represents a discovered credential ready for import."""
    name: str
    value: str
    service: str
    source: str
    confidence: float
    detected_scopes: List[str] = field(default_factory=list)
    validation_status: str = "pending"
    is_critical: bool = False
    import_recommendation: str = "manual"  # auto, manual, skip
    
    @property
    def masked_value(self) -> str:
        """Return masked value for display."""
        if len(self.value) <= 8:
            return "***"
        return f"{self.value[:4]}...{self.value[-4:]}"


class CredentialDiscovery:
    """
    Comprehensive credential discovery from all likely locations.
    
    Searches in priority order:
    1. Environment variables
    2. OpenClaw native locations
    3. Standard config locations
    4. Common tool configs
    5. GitHub CLI, Docker helpers
    """
    
    # Service definitions with detection patterns
    SERVICES = {
        'github': {
            'patterns': [
                r'^ghp_[a-zA-Z0-9]{36}$',      # Personal access token
                r'^gho_[a-zA-Z0-9]{36}$',      # OAuth token
                r'^github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}$',  # Fine-grained PAT
            ],
            'env_vars': ['GITHUB_TOKEN', 'GITHUB_PAT', 'GH_TOKEN', 'GITHUB_API_TOKEN'],
            'file_patterns': ['*github*.env', '.github_token', 'gh_token'],
            'is_critical': True,
            'validation_endpoint': 'https://api.github.com/user',
            'scopes': ['repo', 'workflow', 'read:org', 'write:packages'],
        },
        'openrouter': {
            'patterns': [
                r'^sk-or-[a-zA-Z0-9]{48}$',
                r'^sk-or-v1-[a-zA-Z0-9]{48}$',
            ],
            'env_vars': ['OPENROUTER_API_KEY', 'OPENROUTER_KEY', 'OR_API_KEY'],
            'file_patterns': ['*openrouter*', '*openrouter*.env'],
            'is_critical': True,
            'validation_endpoint': 'https://openrouter.ai/api/v1/models',
        },
        'agentmail': {
            'patterns': [
                r'^[a-z0-9]{32,64}$',
                r'^agent_[a-zA-Z0-9]{32,48}$',
            ],
            'env_vars': ['AGENTMAIL_API_KEY', 'AGENTMAIL_KEY', 'AGENTMAIL_TOKEN'],
            'file_patterns': ['*agentmail*', '*agentmail*.env'],
            'is_critical': True,
            'validation_endpoint': 'https://api.agentmail.to/v1/health',
        },
        'abund': {
            'patterns': [
                r'^abund_[a-zA-Z0-9]{32,64}$',
                r'^[a-f0-9]{64}$',
            ],
            'env_vars': ['ABUND_API_KEY', 'ABUND_KEY', 'ABUND_TOKEN'],
            'file_patterns': ['*abund*', '*abund*.env'],
            'is_critical': False,
        },
        'ollama': {
            'patterns': [
                r'^ollama_[a-zA-Z0-9]{16,32}$',
            ],
            'env_vars': ['OLLAMA_API_KEY', 'OLLAMA_HOST', 'OLLAMA_API_BASE'],
            'file_patterns': ['*ollama*', '.ollama*'],
            'is_critical': False,
            'config_files': ['~/.ollama/config.json', '~/.config/ollama/config.json'],
        },
        'anthropic': {
            'patterns': [
                r'^sk-ant-[a-zA-Z0-9]{32,64}$',
            ],
            'env_vars': ['ANTHROPIC_API_KEY', 'ANTHROPIC_KEY', 'CLAUDE_API_KEY'],
            'file_patterns': ['*anthropic*', '*claude*.env'],
            'is_critical': True,
        },
        'openai': {
            'patterns': [
                r'^sk-[a-zA-Z0-9]{48}$',
                r'^sk-proj-[a-zA-Z0-9]{20}-[a-zA-Z0-9]{20}-[a-zA-Z0-9]{20}-[a-zA-Z0-9]{20}$',
            ],
            'env_vars': ['OPENAI_API_KEY', 'OPENAI_KEY'],
            'file_patterns': ['*openai*', '.openai'],
            'is_critical': True,
        },
    }
    
    def __init__(self):
        self.discovered: List[DiscoveredCredential] = []
        self.home = Path.home()
        self.openclaw_dir = self.home / ".openclaw"
        self.workspace_dir = self.openclaw_dir / "workspace"
        
    def discover_all(self, include_validation: bool = False) -> List[DiscoveredCredential]:
        """
        Run comprehensive discovery across all sources.
        
        Args:
            include_validation: Whether to validate credentials against APIs
            
        Returns:
            List of discovered credentials
        """
        self.discovered = []
        
        # Priority 1: Environment variables
        self._scan_environment()
        
        # Priority 2: OpenClaw native locations
        self._scan_openclaw_locations()
        
        # Priority 3: Standard locations
        self._scan_standard_locations()
        
        # Priority 4: Common tool configs
        self._scan_tool_configs()
        
        # Priority 5: GitHub CLI & Docker
        self._scan_cli_tools()
        
        # De-duplicate and score
        self._deduplicate()
        self._set_import_recommendations()
        
        # Optional validation
        if include_validation:
            self._validate_discovered()
        
        return self.discovered
    
    def _scan_environment(self):
        """Scan environment variables for credentials."""
        for service_name, config in self.SERVICES.items():
            for env_var in config.get('env_vars', []):
                value = os.getenv(env_var)
                if value and self._looks_like_credential(value):
                    confidence = self._calculate_confidence(value, config['patterns'])
                    self._add_credential(
                        name=f"{service_name}_{self._get_suffix(service_name)}",
                        value=value,
                        service=service_name,
                        source=f"environment:${env_var}",
                        confidence=confidence,
                        is_critical=config.get('is_critical', False)
                    )
    
    def _scan_openclaw_locations(self):
        """Scan OpenClaw-specific directories."""
        locations = [
            self.openclaw_dir / "credentials" / "*.env",
            self.workspace_dir / "config" / "*.yaml",
            self.workspace_dir / "config" / "*.yml",
            self.workspace_dir / "*.env",
            self.openclaw_dir / "*.env",
        ]
        
        for pattern in locations:
            for file_path in glob.glob(str(pattern)):
                self._parse_file(Path(file_path))
    
    def _scan_standard_locations(self):
        """Scan standard configuration locations."""
        locations = [
            self.home / ".env",
            self.home / ".config" / "env",
            self.workspace_dir.parent / ".env" if self.workspace_dir.parent != self.home else None,
        ]
        
        for file_path in locations:
            if file_path and file_path.exists():
                self._parse_file(file_path)
        
        # Hidden env files
        for hidden in self.home.glob(".*env*"):
            if hidden.is_file():
                self._parse_file(hidden)
    
    def _scan_tool_configs(self):
        """Scan common tool configuration directories."""
        # OpenRouter
        openrouter_paths = [
            self.home / ".config" / "openrouter" / "config.json",
            self.home / ".config" / "openrouter" / ".env",
            self.home / ".openrouter",
        ]
        
        for path in openrouter_paths:
            if path.exists():
                if path.suffix == '.json':
                    self._parse_json_file(path, 'openrouter')
                else:
                    self._parse_file(path)
        
        # Ollama
        ollama_paths = [
            self.home / ".ollama" / "config.json",
            self.home / ".config" / "ollama" / "config.json",
        ]
        
        for path in ollama_paths:
            if path.exists():
                self._parse_json_file(path, 'ollama')
    
    def _scan_cli_tools(self):
        """Scan CLI tool authentication status."""
        # GitHub CLI
        try:
            result = subprocess.run(
                ['gh', 'auth', 'token'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                token = result.stdout.strip()
                self._add_credential(
                    name="github_cli_token",
                    value=token,
                    service="github",
                    source="gh auth token",
                    confidence=0.95,
                    is_critical=True
                )
        except:
            pass
        
        # Docker credential helper (basic check)
        docker_config = self.home / ".docker" / "config.json"
        if docker_config.exists():
            try:
                with open(docker_config) as f:
                    config = json.load(f)
                    if 'credsStore' in config or 'credHelpers' in config:
                        # Found docker credential helper, but we can't extract
                        pass
            except:
                pass
    
    def _parse_file(self, file_path: Path):
        """Parse a file for credential patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check each line
            for line_num, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Look for KEY=VALUE patterns
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip().upper()
                value = value.strip().strip('"\'')
                
                if len(value) < 10:
                    continue
                
                if not self._looks_like_credential(value):
                    continue
                
                # Detect service from key name
                for service_name, config in self.SERVICES.items():
                    if any(var.lower() in key.lower() for var in config.get('env_vars', [])):
                        confidence = self._calculate_confidence(value, config['patterns'])
                        suggested_name = self._suggest_name(service_name, file_path.stem)
                        
                        self._add_credential(
                            name=suggested_name,
                            value=value,
                            service=service_name,
                            source=f"{file_path}:{line_num}",
                            confidence=confidence,
                            is_critical=config.get('is_critical', False)
                        )
                        break
        except Exception as e:
            pass  # Silently skip unreadable files
    
    def _parse_json_file(self, file_path: Path, service_hint: str = None):
        """Parse JSON config files."""
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            # Search recursively
            self._search_json_tree(data, str(file_path), service_hint)
        except:
            pass
    
    def _search_json_tree(self, data: Any, path: str, service_hint: str = None, key: str = ""):
        """Recursively search JSON for credentials."""
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{key}.{k}" if key else k
                self._search_json_tree(v, path, service_hint, new_key)
                
                # Check common key names
                if k.lower() in ['token', 'api_key', 'key', 'secret', 'password']:
                    if isinstance(v, str) and self._looks_like_credential(v):
                        service = service_hint or self._detect_service_from_key(k)
                        if service:
                            config = self.SERVICES.get(service, {})
                            confidence = self._calculate_confidence(v, config.get('patterns', []))
                            
                            self._add_credential(
                                name=f"{service}_json_{k}",
                                value=v,
                                service=service,
                                source=f"{path} (key: {new_key})",
                                confidence=confidence,
                                is_critical=config.get('is_critical', False)
                            )
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._search_json_tree(item, path, service_hint, f"{key}[{i}]")
    
    def _add_credential(self, name: str, value: str, service: str, 
                       source: str, confidence: float, is_critical: bool = False):
        """Add a discovered credential."""
        cred = DiscoveredCredential(
            name=name,
            value=value,
            service=service,
            source=source,
            confidence=confidence,
            is_critical=is_critical
        )
        self.discovered.append(cred)
    
    def _deduplicate(self):
        """Remove duplicates, keeping highest confidence."""
        seen = {}
        unique = []
        
        for cred in self.discovered:
            # Hash the value to detect duplicates
            value_hash = hash(cred.value) % 100000000
            
            if value_hash not in seen:
                seen[value_hash] = cred
                unique.append(cred)
            elif cred.confidence > seen[value_hash].confidence:
                # Replace with higher confidence
                idx = unique.index(seen[value_hash])
                unique[idx] = cred
                seen[value_hash] = cred
        
        self.discovered = unique
    
    def _set_import_recommendations(self):
        """Set import recommendation for each credential."""
        for cred in self.discovered:
            if cred.confidence < 0.5:
                cred.import_recommendation = "skip"  # Low confidence
            elif cred.is_critical:
                cred.import_recommendation = "manual"  # Needs review
            else:
                cred.import_recommendation = "auto"  # Safe to auto-import
    
    def _validate_discovered(self):
        """Validate discovered credentials against live APIs."""
        # This would make API calls to validate tokens
        # For safety, we skip this by default but could implement
        pass
    
    def _looks_like_credential(self, value: str) -> bool:
        """Quick heuristic check if value is a credential."""
        if not value or len(value) < 20 or len(value) > 300:
            return False
        if ' ' in value or '\n' in value or '\t' in value:
            return False
        if value.lower() in ['true', 'false', 'null', 'none', 'undefined']:
            return False
        
        # Check against known patterns
        for config in self.SERVICES.values():
            for pattern in config.get('patterns', []):
                if re.match(pattern, value):
                    return True
        
        return False
    
    def _calculate_confidence(self, value: str, patterns: List[str]) -> float:
        """Calculate confidence score for a credential match."""
        if not patterns:
            return 0.5
        
        for pattern in patterns:
            if re.match(pattern, value):
                base = 0.9
                # Boost for longer tokens (more secure)
                if len(value) > 40:
                    base += 0.05
                return min(base, 1.0)
        
        return 0.5
    
    def _get_suffix(self, service: str) -> str:
        """Get appropriate suffix for credential name."""
        suffixes = {
            'github': 'token',
            'openrouter': 'api_key',
            'agentmail': 'api_key',
            'abund': 'api_key',
            'ollama': 'config',
            'anthropic': 'api_key',
            'openai': 'api_key',
        }
        return suffixes.get(service, 'key')
    
    def _suggest_name(self, service: str, context: str) -> str:
        """Suggest a descriptive name for the credential."""
        suffix = self._get_suffix(service)
        
        # Clean context
        clean_context = re.sub(r'[^a-zA-Z0-9]', '_', context.lower())
        clean_context = re.sub(r'_+', '_', clean_context)
        clean_context = clean_context.strip('_')
        
        if clean_context and clean_context not in ['env', 'env_', '_env']:
            return f"{service}_{clean_context}_{suffix}"
        
        return f"{service}_{suffix}"
    
    def _detect_service_from_key(self, key: str) -> Optional[str]:
        """Detect service from a JSON key name."""
        key_lower = key.lower()
        
        service_hints = {
            'github': ['github', 'gh_'],
            'openrouter': ['openrouter', 'or_'],
            'agentmail': ['agentmail', 'agent_mail'],
            'abund': ['abund'],
            'ollama': ['ollama'],
            'anthropic': ['anthropic', 'claude'],
            'openai': ['openai'],
        }
        
        for service, hints in service_hints.items():
            if any(hint in key_lower for hint in hints):
                return service
        
        return None
    
    def generate_report(self) -> str:
        """Generate human-readable discovery report."""
        if not self.discovered:
            return """🔍 CREDENTIAL DISCOVERY REPORT
============================================================

No credentials found in common locations.

Searched:
  ✅ Environment variables
  ✅ ~/.openclaw/credentials/*.env
  ✅ ~/.openclaw/workspace/config/*.yaml
  ~/.openclaw/workspace/*.env
  ✅ ~/.env and hidden env files
  ✅ ~/.config/openrouter/*
  ✅ ~/.ollama/config.json
  ✅ GitHub CLI (gh auth status)

To manually add credentials:
  python3 lib/credential_manager.py add --name my_token --service github
"""
        
        lines = [
            "🔍 CREDENTIAL DISCOVERY REPORT",
            "=" * 60,
            f"\n✨ Found {len(self.discovered)} credential(s):\n"
        ]
        
        # Group by import recommendation
        auto_import = [c for c in self.discovered if c.import_recommendation == "auto"]
        manual_review = [c for c in self.discovered if c.import_recommendation == "manual"]
        skip = [c for c in self.discovered if c.import_recommendation == "skip"]
        
        if auto_import:
            lines.append(f"\n✅ Safe to Auto-Import ({len(auto_import)}):")
            for cred in auto_import:
                lines.append(f"  • {cred.service.upper()}: {cred.name}")
                lines.append(f"    Source: {cred.source}")
                lines.append(f"    Value: {cred.masked_value} (confidence: {cred.confidence:.0%})")
                lines.append("")
        
        if manual_review:
            lines.append(f"\n⚠️  Requires Manual Review ({len(manual_review)}):")
            for cred in manual_review:
                icon = "🔴" if cred.is_critical else "🟡"
                lines.append(f"  {icon} {cred.service.upper()}: {cred.name}")
                lines.append(f"     Source: {cred.source}")
                lines.append(f"     Value: {cred.masked_value} (confidence: {cred.confidence:.0%})")
                if cred.is_critical:
                    lines.append(f"     ⚠️  Critical service - requires explicit approval")
                lines.append("")
        
        if skip:
            lines.append(f"\n⏭️  Skipped (Low Confidence) ({len(skip)}):")
            for cred in skip:
                lines.append(f"  • {cred.service}: {cred.name} ({cred.confidence:.0%} confidence)")
        
        lines.append("\n" + "=" * 60)
        lines.append("\nNext Steps:")
        
        if auto_import:
            lines.append("  Run: python3 lib/credential_manager.py discover --auto-import")
            lines.append("       (to automatically import safe credentials)")
        
        if manual_review:
            lines.append("  Run: python3 lib/credential_manager.py discover")
            lines.append("       (to review and selectively import critical credentials)")
        
        return "\n".join(lines)
    
    def import_to_manager(self, manager, auto_only: bool = False, 
                         dry_run: bool = False) -> Dict[str, int]:
        """
        Import discovered credentials to the manager.
        
        Args:
            manager: CredentialManager instance
            auto_only: Only import auto-recommended credentials
            dry_run: Preview only, don't actually import
            
        Returns:
            Dict with import stats
        """
        stats = {"imported": 0, "skipped": 0, "failed": 0}
        
        for cred in self.discovered:
            # Skip low confidence
            if cred.confidence < 0.5:
                stats["skipped"] += 1
                continue
            
            # Skip manual review items if auto_only
            if auto_only and cred.import_recommendation != "auto":
                stats["skipped"] += 1
                continue
            
            # Check for duplicates
            if hasattr(manager, 'exists') and manager.exists(cred.name):
                stats["skipped"] += 1
                continue
            
            if dry_run:
                print(f"Would import: {cred.name} ({cred.service})")
                stats["imported"] += 1
                continue
            
            # Perform import
            try:
                from credential_manager import CredentialManager
                if isinstance(manager, CredentialManager):
                    if manager.add(cred.name, cred.value, cred.service):
                        stats["imported"] += 1
                    else:
                        stats["failed"] += 1
                else:
                    stats["failed"] += 1
            except Exception as e:
                print(f"Failed to import {cred.name}: {e}")
                stats["failed"] += 1
        
        return stats


# Self-test
if __name__ == "__main__":
    import tempfile
    import os
    
    print("Running credential discovery self-test...\n")
    
    # Create test credentials
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write('# Test credentials\n')
        f.write('GITHUB_TOKEN=ghp_test1234567890abcdef1234567890abcd\n')
        f.write('OPENROUTER_API_KEY=sk-or-test1234567890abcdef1234567890abcdef1234567890ab\n')
        test_env_path = f.
