#!/usr/bin/env python3
"""
Credential validation for various services.
Tests tokens against live APIs (when safe).

v1.0.2 - Production Release
"""

import json
import urllib.request
from typing import Optional, List, Tuple
from enum import Enum


class ValidationResult(Enum):
    """Validation status of a credential."""
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"
    NETWORK_ERROR = "network_error"
    EXPIRED = "expired"
    INSUFFICIENT_SCOPES = "insufficient_scopes"


class CredentialValidator:
    """
    Validates credentials against live APIs.
    
    Usage:
        validator = CredentialValidator()
        status, scopes = validator.validate_github(token)
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def validate_github(self, token: str) -> Tuple[ValidationResult, Optional[List[str]], Optional[str]]:
        """
        Validate GitHub Personal Access Token.
        
        Returns:
            Tuple of (status, scopes_list, error_message)
        """
        test_endpoints = [
            "https://api.github.com/user",
            "https://api.github.com/rate_limit"
        ]
        
        for endpoint in test_endpoints:
            try:
                req = urllib.request.Request(
                    endpoint,
                    headers={
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28"
                    }
                )
                
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        
                        # Extract scopes from headers if available
                        headers = dict(response.headers)
                        oauth_scopes = headers.get('X-OAuth-Scopes', '').split(', ')
                        oauth_scopes = [s.strip() for s in oauth_scopes if s.strip()]
                        
                        return ValidationResult.VALID, oauth_scopes, None
                        
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    return ValidationResult.INVALID, None, "Token unauthorized (401)"
                elif e.code == 403:
                    return ValidationResult.INSUFFICIENT_SCOPES, None, f"Forbidden (403): {e.reason}"
                elif e.code == 404:
                    continue  # Try next endpoint
                else:
                    return ValidationResult.NETWORK_ERROR, None, f"HTTP {e.code}: {e.reason}"
                    
            except urllib.error.URLError as e:
                return ValidationResult.NETWORK_ERROR, None, f"Network error: {e.reason}"
                
            except Exception as e:
                return ValidationResult.UNKNOWN, None, f"Error: {e}"
        
        return ValidationResult.UNKNOWN, None, "All endpoints failed"
    
    def validate_agentmail(self, api_key: str) -> Tuple[ValidationResult, Optional[List[str]], Optional[str]]:
        """Validate AgentMail API key."""
        try:
            req = urllib.request.Request(
                "https://api.agentmail.dev/v1/inboxes",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    return ValidationResult.VALID, [], None
                    
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return ValidationResult.INVALID, None, "Invalid API key"
        except Exception as e:
            return ValidationResult.NETWORK_ERROR, None, str(e)
        
        return ValidationResult.UNKNOWN, None, "Unknown error"
    
    def check_required_scopes(self, available: List[str], 
                              required: List[str]) -> Tuple[bool, List[str]]:
        """
        Check if available scopes meet requirements.
        
        Returns:
            Tuple of (has_all, missing_scopes)
        """
        available_set = set(s.strip().lower() for s in available)
        required_set = set(s.strip().lower() for s in required)
        
        missing = list(required_set - available_set)
        return len(missing) == 0, missing


# Self-test
if __name__ == "__main__":
    print("Testing Validator...")
    
    validator = CredentialValidator()
    
    # Test scope checking
    available = ["repo", "workflow", "read:org"]
    required = ["repo", "workflow"]
    has_all, missing = validator.check_required_scopes(available, required)
    
    assert has_all, "Should have all required scopes"
    assert len(missing) == 0, "Should have no missing"
    print("✓ Scope checking works")
    
    # Test missing scopes
    required2 = ["repo", "admin:org"]
    has_all2, missing2 = validator.check_required_scopes(available, required2)
    
    assert not has_all2, "Should detect missing scope"
    assert "admin:org" in [m.lower() for m in missing2], "Should report missing scope"
    print("✓ Missing scope detection works")
    
    print("\n✓ All validator tests passed")
