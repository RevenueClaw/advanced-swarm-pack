#!/usr/bin/env python3
"""
Docker & Infrastructure Analyzer for Codebase Understanding.

Analyzes Docker configurations, volume mounts, container dependencies,
and infrastructure risks in complex multi-container projects.

Author: RockClaw
Version: 1.1.0
"""

import re
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class DockerService:
    """Represents a Docker Compose service."""
    name: str
    image: Optional[str]
    build_context: Optional[str]
    volumes: List[Dict[str, str]]  # host:container, type: bind/named
    ports: List[str]
    environment: Dict[str, str]
    depends_on: List[str]
    entrypoint: Optional[str]
    command: Optional[str]
    networks: List[str]
    restart_policy: Optional[str]


@dataclass
class VolumeMount:
    """A volume mount configuration."""
    source: str  # Host path or volume name
    target: str  # Container path
    type: str    # bind, volume, tmpfs
    read_only: bool = False
    risks: List[str] = None
    
    def __post_init__(self):
        if self.risks is None:
            self.risks = []


@dataclass
class InfrastructureRisk:
    """Infrastructure-related risk."""
    category: str  # volume, network, dependency, startup
    severity: str  # critical, high, medium, low
    description: str
    affected_files: List[str]
    mitigation: str


@dataclass
class ImportTimeRisk:
    """Risk from import-time side effects."""
    file: str
    line: int
    risk_type: str  # db_connect, cache_init, network_call, file_io
    description: str
    safe_alternative: str


class DockerAnalyzer:
    """
    Analyzes Docker and infrastructure configurations.
    
    Usage:
        analyzer = DockerAnalyzer()
        infra = analyzer.analyze_project("/path/to/chipradar")
        
        # Check volume mount risks
        risks = analyzer.get_volume_risks()
        
        # Get startup order
        order = analyzer.get_container_startup_order()
        
        # Find import-time side effects
        side_effects = analyzer.find_import_time_risks()
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.docker_compose_files: List[Path] = []
        self.dockerfiles: List[Path] = []
        self.services: Dict[str, DockerService] = {}
        self.volumes: Dict[str, VolumeMount] = {}
        self.risks: List[InfrastructureRisk] = []
        self._parse_docker_configs()
    
    def _parse_docker_configs(self) -> None:
        """Find and parse all Docker configuration files."""
        # Find docker-compose files
        for pattern in ['docker-compose*.yml', 'docker-compose*.yaml']:
            self.docker_compose_files.extend(self.project_path.glob(pattern))
        
        # Find Dockerfiles
        self.dockerfiles = list(self.project_path.rglob("Dockerfile*"))
        
        # Parse compose files
        for compose_file in self.docker_compose_files:
            self._parse_compose_file(compose_file)
    
    def _parse_compose_file(self, compose_path: Path) -> None:
        """Parse a docker-compose file."""
        try:
            with open(compose_path) as f:
                config = yaml.safe_load(f)
            
            if not config or 'services' not in config:
                return
            
            for service_name, service_config in config['services'].items():
                service = self._extract_service(service_name, service_config)
                self.services[service_name] = service
                
                # Extract volumes
                for vol in service.volumes:
                    mount = VolumeMount(
                        source=vol.get('source', ''),
                        target=vol.get('target', ''),
                        type=vol.get('type', 'bind'),
                        read_only=vol.get('read_only', False)
                    )
                    self._assess_volume_risk(mount, service_name)
                    self.volumes[f"{service_name}:{mount.target}"] = mount
                
        except Exception as e:
            print(f"Warning: Failed to parse {compose_path}: {e}")
    
    def _extract_service(self, name: str, config: Dict) -> DockerService:
        """Extract service configuration from compose dict."""
        volumes = []
        for vol in config.get('volumes', []):
            if isinstance(vol, str):
                # Format: "host:container:mode"
                parts = vol.split(':')
                volumes.append({
                    'source': parts[0] if len(parts) > 0 else '',
                    'target': parts[1] if len(parts) > 1 else '',
                    'type': 'bind',
                    'read_only': len(parts) > 2 and 'ro' in parts[2]
                })
            else:
                volumes.append(vol)
        
        env = {}
        for env_var in config.get('environment', []):
            if isinstance(env_var, str) and '=' in env_var:
                k, v = env_var.split('=', 1)
                env[k] = v
            elif isinstance(env_var, dict):
                env.update(env_var)
        
        return DockerService(
            name=name,
            image=config.get('image'),
            build_context=config.get('build', {}).get('context') if isinstance(config.get('build'), dict) else config.get('build'),
            volumes=volumes,
            ports=[str(p) for p in config.get('ports', [])],
            environment=env,
            depends_on=list(config.get('depends_on', {}).keys()) if isinstance(config.get('depends_on'), dict) else config.get('depends_on', []),
            entrypoint=config.get('entrypoint'),
            command=config.get('command'),
            networks=list(config.get('networks', {}).keys()) if isinstance(config.get('networks'), dict) else config.get('networks', []),
            restart_policy=config.get('restart')
        )
    
    def _assess_volume_risk(self, mount: VolumeMount, service: str) -> None:
        """Assess risks for a volume mount."""
        # Risk: Database files in bind mount
        if any(db in mount.target.lower() for db in ['postgres', 'mysql', 'sqlite', 'db', 'database']):
            if mount.type == 'bind':
                mount.risks.append("Database in bind mount - performance/corruption risk")
        
        # Risk: Sensitive credentials
        if any(s in mount.target.lower() for s in ['credentials', 'secret', 'key', 'token']):
            mount.risks.append("Sensitive data in volume mount - verify permissions")
        
        # Risk: Log files filling disk
        if 'log' in mount.target.lower():
            mount.risks.append("Log directory - implement rotation")
        
        # Risk: Relative path
        if mount.source.startswith('.') or not mount.source.startswith('/'):
            mount.risks.append("Relative path in volume - portability issue")
    
    def get_volume_risks(self) -> List[Dict[str, Any]]:
        """Get all volume mount risks."""
        risks = []
        for key, mount in self.volumes.items():
            if mount.risks:
                risks.append({
                    'volume': key,
                    'source': mount.source,
                    'target': mount.target,
                    'type': mount.type,
                    'risks': mount.risks
                })
        return risks
    
    def get_container_startup_order(self) -> List[str]:
        """Calculate safe container startup order based on dependencies."""
        # Topological sort
        in_degree = {name: 0 for name in self.services}
        adjacency = defaultdict(list)
        
        for name, service in self.services.items():
            for dep in service.depends_on:
                adjacency[dep].append(name)
                in_degree[name] += 1
        
        # Find starting nodes
        queue = [name for name, degree in in_degree.items() if degree == 0]
        order = []
        
        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycles
        if len(order) != len(self.services):
            order.append("[CIRCULAR DEPENDENCY DETECTED]")
        
        return order
    
    def find_import_time_risks(self, source_files: List[Path]) -> List[ImportTimeRisk]:
        """Find risky import-time side effects in Python files."""
        risks = []
        
        risky_patterns = [
            (r'^[^#]*(?:import|from)\s+.*(?:db|database|mongo|postgres|mysql)',
             'db_connect', 'Database connection at import time'),
            (r'^[^#]*(redis|cache|memcached)\s*=', 'cache_init', 'Cache initialization at import'),
            (r'^[^#]*requests\.(get|post|put|delete)\s*\(', 'network_call', 'Network call on import'),
            (r'^[^#]*open\s*\([^)]*[\'"]w[\'"]', 'file_io', 'File write on import'),
            (r'^[^#]*(load|load_dotenv|yaml\.load)\s*\(', 'config_load', 'Config loading at import'),
        ]
        
        for file_path in source_files:
            if not file_path.suffix == '.py':
                continue
            
            try:
                with open(file_path) as f:
                    lines = f.readlines()
            except:
                continue
            
            for line_no, line in enumerate(lines, 1):
                for pattern, risk_type, description in risky_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        risks.append(ImportTimeRisk(
                            file=str(file_path),
                            line=line_no,
                            risk_type=risk_type,
                            description=description,
                            safe_alternative=f"Move {risk_type} to initialization function"
                        ))
        
        return risks
    
    def analyze_dockerfile(self, dockerfile: Path) -> Dict[str, Any]:
        """Analyze a Dockerfile for optimization and security."""
        try:
            with open(dockerfile) as f:
                content = f.read()
        except:
            return {}
        
        analysis = {
            'base_image': None,
            'layers': [],
            'risks': [],
            'optimizations': []
        }
        
        # Extract base image
        from_match = re.search(r'^FROM\s+(\S+)', content, re.MULTILINE)
        if from_match:
            analysis['base_image'] = from_match.group(1)
            if 'latest' in analysis['base_image']:
                analysis['risks'].append("Using 'latest' tag - not reproducible")
        
        # Check for root user
        if 'USER root' in content and 'USER' not in content.split('USER root')[-1]:
            analysis['risks'].append("Running as root - security risk")
        
        # Check layer ordering
        if re.search(r'^RUN.*apt.*&&.*pip', content, re.MULTILINE):
            analysis['optimizations'].append("Combine apt and pip RUN commands")
        
        # Check for secrets
        if re.search(r'(ENV|ARG)\s+.*(?:PASSWORD|SECRET|KEY|TOKEN)', content, re.IGNORECASE):
            analysis['risks'].append("Potential secret in Dockerfile - use build args or secrets")
        
        return analysis
    
    def get_infrastructure_summary(self) -> Dict[str, Any]:
        """Get complete infrastructure summary."""
        return {
            'services': len(self.services),
            'volumes': len(self.volumes),
            'container_order': self.get_container_startup_order(),
            'volume_risks': self.get_volume_risks(),
            'dockerfiles': [str(d) for d in self.dockerfiles],
            'compose_files': [str(c) for c in self.docker_compose_files]
        }


class SafeEditProtocol:
    """
    Safe editing protocol for Docker/infrastructure files.
    
    Guarantees:
    - Atomic writes (no partial files)
    - Timestamped backups before any change
    - Integrity verification after write
    - Rollback capability
    
    Usage:
        editor = SafeEditProtocol(project_path, backup_dir)
        
        # Safe edit with automatic backup
        result = editor.safe_edit(
            file_path="docker-compose.yml",
            content=new_content,
            verify_syntax=lambda c: yaml.safe_load(c)
        )
        
        # Rollback if needed
        editor.rollback("docker-compose.yml", result['backup_id'])
    """
    
    def __init__(self, project_path: str, backup_dir: Optional[str] = None):
        self.project_path = Path(project_path)
        self.backup_dir = Path(backup_dir) if backup_dir else self.project_path / ".backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_backup(self, file_path: Path) -> str:
        """Create timestamped backup."""
        import hashlib
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_content = file_path.read_text() if file_path.exists() else ""
        
        # Create backup filename with hash
        content_hash = hashlib.md5(original_content.encode()).hexdigest()[:8]
        backup_id = f"{file_path.name}_{timestamp}_{content_hash}"
        backup_path = self.backup_dir / backup_id
        
        backup_path.write_text(original_content)
        return backup_id
    
    def safe_edit(
        self,
        file_path: str,
        content: str,
        verify_syntax: Optional[callable] = None,
        verify_integrity: bool = True
    ) -> Dict[str, Any]:
        """
        Perform atomic safe edit with backup.
        
        Args:
            file_path: Path to file (relative to project_path)
            content: New content to write
            verify_syntax: Optional function to validate syntax
            verify_integrity: Whether to verify file after write
        
        Returns:
            Dict with success status, backup_id, and verification results
        """
        target = self.project_path / file_path
        result = {
            'success': False,
            'backup_id': None,
            'verification': {},
            'error': None
        }
        
        try:
            # Step 1: Create backup
            result['backup_id'] = self._create_backup(target)
            
            # Step 2: Verify syntax if requested
            if verify_syntax:
                try:
                    verify_syntax(content)
                    result['verification']['syntax'] = 'passed'
                except Exception as e:
                    return {**result, 'error': f'Syntax verification failed: {e}'}
            
            # Step 3: Atomic write using temp file + rename
            temp_path = target.parent / f".tmp_{target.name}.{os.getpid()}"
            temp_path.write_text(content)
            
            # Step 4: Verify temp file integrity
            if verify_integrity:
                written = temp_path.read_text()
                if written != content:
                    temp_path.unlink()
                    return {**result, 'error': 'Integrity check failed - written content differs'}
                result['verification']['integrity'] = 'passed'
            
            # Step 5: Atomic rename
            temp_path.rename(target)
            
            # Step 6: Final verification
            if verify_integrity and target.exists():
                final = target.read_text()
                if final == content:
                    result['verification']['final'] = 'passed'
                    result['success'] = True
                else:
                    return {**result, 'error': 'Final verification failed'}
            else:
                result['success'] = True
            
            return result
            
        except Exception as e:
            return {**result, 'error': str(e)}
    
    def rollback(self, file_path: str, backup_id: str) -> bool:
        """Restore file from backup."""
        try:
            target = self.project_path / file_path
            backup = self.backup_dir / backup_id
            
            if not backup.exists():
                return False
            
            # Current state backup first (in case we want to undo rollback)
            current_backup = self._create_backup(target)
            
            # Restore
            target.write_text(backup.read_text())
            return True
            
        except Exception:
            return False
    
    def get_backup_list(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        for backup in self.backup_dir.iterdir():
            if backup.is_file():
                if file_path is None or backup.name.startswith(file_path):
                    parts = backup.name.rsplit('_', 2)
                    if len(parts) >= 2:
                        backups.append({
                            'id': backup.name,
                            'file': parts[0],
                            'timestamp': parts[1] if len(parts) > 1 else 'unknown',
                            'size': backup.stat().st_size
                        })
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)


def demo():
    """Demo Docker analyzer."""
    print("=" * 60)
    print("DOCKER & INFRASTRUCTURE ANALYZER")
    print("=" * 60)
    
    # Example usage
    print("\nClass: DockerAnalyzer")
    print("  - analyze_project(path)")
    print("  - get_volume_risks()")
    print("  - get_container_startup_order()")
    print("  - find_import_time_risks(files)")
    print("\nClass: SafeEditProtocol")
    print("  - safe_edit(file, content, verify_syntax)")
    print("  - rollback(file, backup_id)")
    print("  - get_backup_list()")
    print("=" * 60)


if __name__ == "__main__":
    demo()
