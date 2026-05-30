#!/usr/bin/env python3
"""
Model Profiles - Configuration for different local model quality tiers.

Defines profiles for:
- fast: Quick responses, low resource usage, simple tasks
- balanced: Good quality, moderate resources, most tasks
- overnight: High quality, high resources, offline batch jobs
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class ModelProfile:
    """Configuration for a specific model profile."""
    provider: str = "llama_cpp"
    endpoint: str = "http://localhost:8080/v1"
    model: str = "qwen3-8b-q5"
    max_context: int = 4096
    timeout: int = 60
    use_for: List[str] = field(default_factory=list)
    description: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ModelProfile":
        return cls(
            provider=data.get("provider", "llama_cpp"),
            endpoint=data.get("endpoint", "http://localhost:8080/v1"),
            model=data.get("model", "qwen3-8b-q5"),
            max_context=data.get("max_context", 4096),
            timeout=data.get("timeout", 60),
            use_for=data.get("use_for", []),
            description=data.get("description", ""),
        )


class ProfileRegistry:
    """Registry of available model profiles."""
    
    DEFAULT_PROFILES = {
        "fast": {
            "provider": "llama_cpp",
            "endpoint": "http://rock-5c:8080/v1",
            "model": "qwen3-8b-q5",
            "max_context": 4096,
            "timeout": 30,
            "use_for": [
                "classification",
                "routing",
                "short_summary",
                "extraction",
                "quick_sorting",
            ],
            "description": "Fast, low-resource model for simple tasks",
        },
        "balanced": {
            "provider": "llama_cpp",
            "endpoint": "http://rock-5c:8081/v1",
            "model": "qwen3-14b-q4",
            "max_context": 4096,
            "timeout": 60,
            "use_for": [
                "query_rewrite",
                "medium_summary",
                "triage",
                "evidence_grading",
                "deduplication",
                "tagging",
            ],
            "description": "Balanced quality/speed for most tasks",
        },
        "overnight": {
            "provider": "llama_cpp",
            "endpoint": "http://rock-5c:8082/v1",
            "model": "qwen3-30b-a3b-q4",
            "max_context": 4096,
            "timeout": 300,
            "use_for": [
                "long_summary",
                "report_generation",
                "research_synthesis",
                "passive_code_review",
                "complex_analysis",
            ],
            "description": "High quality model for overnight batch jobs",
        },
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self.profiles: Dict[str, ModelProfile] = {}
        self._load_profiles()
    
    def _load_profiles(self):
        """Load profiles from config or use defaults."""
        if self.config_path and self.config_path.exists():
            with open(self.config_path) as f:
                data = yaml.safe_load(f) or {}
                profiles_data = data.get("local_models", {})
        else:
            profiles_data = self.DEFAULT_PROFILES
        
        for name, profile_data in profiles_data.items():
            self.profiles[name] = ModelProfile.from_dict(profile_data)
    
    def get(self, name: str) -> ModelProfile:
        """Get a profile by name."""
        if name not in self.profiles:
            raise ValueError(f"Profile '{name}' not found. Available: {list(self.profiles.keys())}")
        return self.profiles[name]
    
    def list_profiles(self) -> List[str]:
        """List available profile names."""
        return list(self.profiles.keys())
    
    def find_profile_for_task(self, task_type: str) -> Optional[str]:
        """Find the best profile for a task type."""
        for name, profile in self.profiles.items():
            if task_type in profile.use_for:
                return name
        return None


# Default instance
DEFAULT_REGISTRY = ProfileRegistry()
