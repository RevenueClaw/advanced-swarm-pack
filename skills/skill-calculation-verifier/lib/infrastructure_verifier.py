#!/usr/bin/env python3
"""
Infrastructure Verifier - Safe editing verification for Docker/infra tasks.

Extends calculation verifier with infrastructure-specific checks:
- Docker command validation
- Volume mount verification
- File operation safety
- Path resolution checks
- Container health validation

Author: RockClaw
Version: 1.0.0 (v1.3.0 refinement)
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class VerificationStatus(Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class VerificationResult:
    """Result of an infrastructure verification check."""
    check_name: str
    status: str  # passed, warning, failed, blocked
    message: str
    remediation: Optional[str]
    severity: str  # info, low, medium, high, critical


class InfrastructureVerifier:
    """
    Verifies infrastructure operations for safety.
    
    Usage:
        verifier = InfrastructureVerifier()
        
        # Verify Docker command
        result = verifier.verify_docker_command(
            "docker-compose up -d",
            working_dir="/path/to/project"
        )
        
        # Verify file operation
        result = verifier.verify_file_operation(
            operation="write",
            target="/path/to/file.yml",
            content=new_content
        )
        
        # Full safe edit verification
        checklist = verifier.get_safe_edit_checklist("docker-compose.yml")
    """
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.results: List[VerificationResult] = []
    
    def verify_docker_command(
        self,
        command: str,
        working_dir: Optional[str] = None
    ) -> List[VerificationResult]:
        """Verify a Docker command is safe to execute."""
        results = []
        cmd_lower = command.lower()
        
        # Check 1: Validate compose file exists if referenced
        if 'docker-compose' in cmd_lower or 'docker compose' in cmd_lower:
            compose_files = [
                self.project_path / "docker-compose.yml",
                self.project_path / "docker-compose.yaml"
            ]
            if not any(f.exists() for f in compose_files):
                results.append(VerificationResult(
                    check_name="docker_compose_file_exists",
                    status=VerificationStatus.BLOCKED.value,
                    message="No docker-compose.yml found in project directory",
                    remediation="Create docker-compose.yml or verify path",
                    severity="critical"
                ))
            else:
                results.append(VerificationResult(
                    check_name="docker_compose_file_exists",
                    status=VerificationStatus.PASSED.value,
                    message="docker-compose.yml found",
                    remediation=None,
                    severity="info"
                ))
        
        # Check 2: Warn about -f (force) flags
        if ' -f ' in command or ' --force' in command:
            results.append(VerificationResult(
                check_name="force_flag_check",
                status=VerificationStatus.WARNING.value,
                message="Force flag detected - may bypass safety checks",
                remediation="Verify force is necessary and backup exists",
                severity="high"
            ))
        
        # Check 3: Check for --no-cache (might be intentional)
        if '--no-cache' in command:
            results.append(VerificationResult(
                check_name="no_cache_flag",
                status=VerificationStatus.PASSED.value,
                message="--no-cache detected: will rebuild from scratch",
                remediation=None,
                severity="info"
            ))
        
        # Check 4: Validate docker binary available
        if not self._docker_available():
            results.append(VerificationResult(
                check_name="docker_available",
                status=VerificationStatus.BLOCKED.value,
                message="Docker not available in PATH",
                remediation="Install Docker or check PATH",
                severity="critical"
            ))
        
        return results
    
    def verify_volume_mount(
        self,
        source: str,
        target: str,
        mount_type: str = "bind"
    ) -> List[VerificationResult]:
        """Verify a volume mount configuration is safe."""
        results = []
        
        # Check 1: Absolute paths for bind mounts
        if mount_type == "bind":
            if not source.startswith('/'):
                results.append(VerificationResult(
                    check_name="absolute_path_check",
                    status=VerificationStatus.WARNING.value,
                    message=f"Relative path in bind mount: {source}",
                    remediation="Use absolute path for bind mounts",
                    severity="medium"
                ))
            else:
                results.append(VerificationResult(
                    check_name="absolute_path_check",
                    status=VerificationStatus.PASSED.value,
                    message="Bind mount uses absolute path",
                    remediation=None,
                    severity="info"
                ))
        
        # Check 2: Database paths
        if any(db in target.lower() for db in ['postgres', 'mysql', 'db', 'database']):
            if mount_type == "bind":
                results.append(VerificationResult(
                    check_name="database_in_bind_mount",
                    status=VerificationStatus.WARNING.value,
                    message="Database in bind mount - performance/corruption risk",
                    remediation="Use named volume for databases",
                    severity="high"
                ))
        
        # Check 3: Check if source exists
        if not Path(source).exists() and not source.startswith('/'):
            # Might be a named volume, not a bind mount
            pass
        elif not Path(source).exists():
            results.append(VerificationResult(
                check_name="source_exists",
                status=VerificationStatus.WARNING.value,
                message=f"Bind mount source does not exist: {source}",
                remediation="Create source directory or verify path",
                severity="medium"
            ))
        
        return results
    
    def verify_file_operation(
        self,
        operation: str,
        target: str,
        content: Optional[str] = None,
        has_backup: bool = False
    ) -> List[VerificationResult]:
        """Verify a file operation is safe."""
        results = []
        target_path = Path(target)
        
        # Check 1: Backup exists
        if not has_backup and target_path.exists():
            results.append(VerificationResult(
                check_name="backup_check",
                status=VerificationStatus.BLOCKED.value,
                message="No backup exists for target file",
                remediation="Create timestamped backup before editing",
                severity="critical"
            ))
        else:
            results.append(VerificationResult(
                check_name="backup_check",
                status=VerificationStatus.PASSED.value,
                message="Backup exists or is not needed",
                remediation=None,
                severity="info"
            ))
        
        # Check 2: Target is writable
        if target_path.exists() and not target_path.parent.exists():
            results.append(VerificationResult(
                check_name="parent_directory_exists",
                status=VerificationStatus.BLOCKED.value,
                message=f"Parent directory does not exist: {target_path.parent}",
                remediation="Create parent directories first",
                severity="critical"
            ))
        
        # Check 3: Content validation (if provided)
        if content and target.endswith('.yml') or target.endswith('.yaml'):
            import yaml
            try:
                yaml.safe_load(content)
                results.append(VerificationResult(
                    check_name="yaml_syntax",
                    status=VerificationStatus.PASSED.value,
                    message="YAML syntax validated",
                    remediation=None,
                    severity="info"
                ))
            except yaml.YAMLError as e:
                results.append(VerificationResult(
                    check_name="yaml_syntax",
                    status=VerificationStatus.BLOCKED.value,
                    message=f"YAML syntax error: {e}",
                    remediation="Fix YAML syntax before writing",
                    severity="critical"
                ))
        
        # Check 4: SCP append check
        if '>>' in str(operation) or ('scp' in str(operation).lower() and '>>' in str(operation)):
            results.append(VerificationResult(
                check_name="scp_append_check",
                status=VerificationStatus.BLOCKED.value,
                message="SCP append mode detected - never use >> with SCP",
                remediation="Use atomic write: cat > file << 'EOF' or rsync",
                severity="critical"
            ))
        
        return results
    
    def verify_import_time_safety(self, file_path: str) -> List[VerificationResult]:
        """Check Python file for import-time side effects."""
        results = []
        path = Path(file_path)
        
        if not path.exists() or not path.suffix == '.py':
            return results
        
        try:
            content = path.read_text()
        except:
            return results
        
        # Check 1: DB connections at module level
        if re.search(r'^[\\s]*(?:db|conn|client|mongo|postgres)\\s*=\\s*(?:connect|MongoClient|Client)',
                     content, re.MULTILINE):
            results.append(VerificationResult(
                check_name="import_time_db_connection",
                status=VerificationStatus.WARNING.value,
                message="Database connection at module level (import-time side effect)",
                remediation="Move connection to function or lazy initialization",
                severity="high"
            ))
        
        # Check 2: Network calls at module level
        if re.search(r'^[\\s]*(?:requests|urllib|http)\.[a-z]+\\s*\(', content, re.MULTILINE):
            results.append(VerificationResult(
                check_name="import_time_network_call",
                status=VerificationStatus.WARNING.value,
                message="Network call at module level",
                remediation="Defer network calls to runtime",
                severity="high"
            ))
        
        # Check 3: File writes at module level
        if re.search(r'^[\\s]*with\\s+open\\s*\([^)]*[\'"]w', content, re.MULTILINE):
            results.append(VerificationResult(
                check_name="import_time_file_write",
                status=VerificationStatus.WARNING.value,
                message="File write at module level",
                remediation="Defer file operations to runtime",
                severity="medium"
            ))
        
        return results
    
    def get_safe_edit_checklist(
        self,
        file_type: str,
        has_docker: bool = False
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get a safe edit checklist for a given file type."""
        checklist = {
            "mandatory": [
                {"check": "Create timestamped backup", "command": f"cp {file_type} {file_type}.backup_$(date +%Y%m%d_%H%M%S)"},
                {"check": "Use atomic write (temp + rename)", "command": "cat > .tmp.$(pid) && mv .tmp.$(pid) target"},
                {"check": "Verify content after write", "command": "diff <(cat target) <(expected) || rollback"}
            ],
            "for_yaml": [
                {"check": "Validate YAML syntax", "command": "python3 -c 'import yaml; yaml.safe_load(open(\"target.yml\"))'"}
            ],
            "for_docker": [
                {"check": "Validate docker-compose", "command": "docker compose config -q"},
                {"check": "Check container health", "command": "docker ps --filter health=unhealthy"},
                {"check": "Inspect volume mounts", "command": "docker inspect <container> --format '{{ json .Mounts }}'"}
            ],
            "for_python": [
                {"check": "Check import-time side effects", "command": "grep -E '^(db|conn|client)\\s*=.*connect' file.py"},
                {"check": "Runtime path resolution", "command": "grep -E 'DB_PATH\\s*=\\s*os.path' file.py"}
            ],
            "rollback": [
                {"check": "Stop if unhealthy", "command": "docker compose stop || true"},
                {"check": "Restore from backup", "command": "cp backup_file target_file"},
                {"check": "Verify rollback", "command": "diff target_file backup_file"}
            ]
        }
        
        return checklist
    
    def _docker_available(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False


def verify_safe_edit(
    target_file: str,
    new_content: str,
    file_type: str = "yaml"
) -> Dict[str, Any]:
    """
    One-call verification for safe file editing.
    
    Returns dict with passed, blocked, and warnings lists.
    """
    verifier = InfrastructureVerifier()
    
    # Run all checks
    file_results = verifier.verify_file_operation(
        operation="write",
        target=target_file,
        content=new_content,
        has_backup=True  # Assume backup created by caller
    )
    
    import_results = verifier.verify_import_time_safety(target_file)
    
    all_results = file_results + import_results
    
    return {
        "passed": [r for r in all_results if r.status == "passed"],
        "blocked": [r for r in all_results if r.status == "blocked"],
        "warnings": [r for r in all_results if r.status == "warning"],
        "can_proceed": len([r for r in all_results if r.status == "blocked"]) == 0
    }


if __name__ == "__main__":
    print("=" * 60)
    print("INFRASTRUCTURE VERIFIER")
    print("=" * 60)
    print("\nUsage:")
    print("  from lib.infrastructure_verifier import InfrastructureVerifier")
    print("  verifier = InfrastructureVerifier('/project/path')")
    print("  results = verifier.verify_docker_command('docker compose up')")
    print("\nOr use one-call:")
    print("  result = verify_safe_edit('docker-compose.yml', content)")
    print("=" * 60)
