# Skill: Credential Manager
# Secure credential management for OpenClaw swarm
# v1.0.2

from .credential_manager import CredentialManager, get_credential
from .storage import CredentialEntry, FileStorage, EnvVarFallback, ChainedStorage
from .validator import CredentialValidator, ValidationResult
from .audit import AuditLogger

__version__ = "1.0.2"
__all__ = [
    "CredentialManager",
    "get_credential", 
    "CredentialEntry",
    "FileStorage",
    "EnvVarFallback",
    "ChainedStorage",
    "CredentialValidator",
    "ValidationResult",
    "AuditLogger"
]
