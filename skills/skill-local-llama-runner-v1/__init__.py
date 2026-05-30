"""
skill-local-llama-runner-v1 - Local llama.cpp model runner for OpenClaw swarm.

v1.4.0 Local Intelligence & Cost Optimization

Usage:
    from skill_local_llama_runner import LocalLlamaRunner
    
    runner = LocalLlamaRunner(profile="fast")
    result = runner.complete(
        prompt="Summarize this document",
        max_tokens=500,
        temperature=0.2,
        schema=MyOutputSchema,
        allow_cloud_fallback=True
    )
"""

__version__ = "1.0.0"
__author__ = "RockClaw"

from .lib.llama_runner import LocalLlamaRunner, LlamaRunnerError
from .lib.model_profiles import ModelProfile, ProfileRegistry

__all__ = [
    "LocalLlamaRunner",
    "LlamaRunnerError", 
    "ModelProfile",
    "ProfileRegistry",
]
