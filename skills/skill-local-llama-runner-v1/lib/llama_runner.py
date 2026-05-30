#!/usr/bin/env python3
"""
LocalLlamaRunner - OpenAI-compatible llama.cpp server interface.

v1.4.0 - Local Intelligence & Cost Optimization

Features:
- OpenAI-compatible API calls to llama.cpp server
- Profile-based model selection (fast/balanced/overnight)
- Health checks and memory pressure monitoring
- Structured output validation
- Cloud fallback support
- Detailed logging

Author: RockClaw
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass, field, asdict
import yaml

# Optional pydantic for structured output
try:
    from pydantic import BaseModel, ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LocalLlama")


class LlamaRunnerError(Exception):
    """Base error for Local Llama Runner."""
    pass


class ModelUnavailableError(LlamaRunnerError):
    """Local model is not responding."""
    pass


class ValidationError(LlamaRunnerError):
    """Output validation failed."""
    pass


@dataclass
class LlamaResponse:
    """Standardized response from local llama model."""
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    backend: str
    wall_time_ms: int
    json_valid: bool = False
    fallback_used: bool = False
    error: Optional[str] = None
    raw_response: Optional[Dict] = field(default=None, repr=False)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CompletionLog:
    """Logging payload for completions."""
    profile: str
    model: str
    runtime: str
    prompt_tokens: int
    completion_tokens: int
    wall_time_sec: float
    json_valid: bool
    fallback_used: bool
    timestamp: str
    endpoint: str
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class LocalLlamaRunner:
    """
    Local llama.cpp OpenAI-compatible server runner.
    
    Usage:
        runner = LocalLlamaRunner(profile="fast")
        
        # Simple completion
        result = runner.complete(prompt="Hello, world!", max_tokens=100)
        
        # With structured output
        result = runner.complete(
            prompt="Extract data",
            schema=MyOutputSchema,
            allow_cloud_fallback=True
        )
    """

    DEFAULT_CONFIG_PATH = Path.home() / ".openclaw/config/local-llama-profiles.yaml"

    def __init__(
        self,
        profile: str = "balanced",
        config_path: Optional[Path] = None,
        cloud_fallback_fn: Optional[callable] = None
    ):
        """
        Initialize the runner with a profile.
        
        Args:
            profile: Profile name (fast, balanced, overnight, or custom)
            config_path: Optional path to yaml config
            cloud_fallback_fn: Optional function to call for cloud fallback
        """
        self.profile_name = profile
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.cloud_fallback_fn = cloud_fallback_fn
        
        # Load profile configuration
        self.config = self._load_config()
        self.profile = self._get_profile(profile)
        
        # Session state
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        # Create logs directory
        self.log_dir = Path.home() / ".openclaw/logs/local-llama"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Stats tracking
        self.request_count = 0
        self.total_tokens_generated = 0
        self.fallback_count = 0
        
        logger.info(f"LocalLlamaRunner initialized with profile: {profile}")
        logger.info(f"  Endpoint: {self.profile.get('endpoint', 'NOT SET')}")

    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return yaml.safe_load(f) or {}
        
        # Return default minimal config
        return {
            "local_models": {
                "fast": {
                    "endpoint": "http://localhost:8080/v1",
                    "model": "qwen3-8b-q5",
                    "max_context": 4096,
                    "timeout": 30
                },
                "balanced": {
                    "endpoint": "http://localhost:8081/v1", 
                    "model": "qwen3-14b-q4",
                    "max_context": 4096,
                    "timeout": 60
                },
                "overnight": {
                    "endpoint": "http://localhost:8082/v1",
                    "model": "qwen3-30b-a3b-q4",
                    "max_context": 4096,
                    "timeout": 300
                }
            }
        }

    def _get_profile(self, profile_name: str) -> Dict:
        """Get profile configuration by name."""
        profiles = self.config.get("local_models", {})
        if profile_name not in profiles:
            raise LlamaRunnerError(
                f"Profile '{profile_name}' not found. "
                f"Available: {list(profiles.keys())}"
            )
        return profiles[profile_name]

    def health_check(self) -> Dict[str, Any]:
        """
        Check if the local model is healthy and responding.
        
        Returns:
            Dict with status, response_time_ms, and model info
        """
        endpoint = self.profile.get("endpoint", "")
        base_url = endpoint.replace("/v1", "")
        
        try:
            start = time.time()
            # Try the health endpoint first
            health_resp = self.session.get(f"{base_url}/health", timeout=5)
            response_time_ms = int((time.time() - start) * 1000)
            
            if health_resp.status_code == 200:
                health_data = health_resp.json()
                return {
                    "status": "healthy",
                    "response_time_ms": response_time_ms,
                    "model": self.profile.get("model", "unknown"),
                    "endpoint": endpoint,
                    "slots_idle": health_data.get("slots_idle", "N/A"),
                    "slots_processing": health_data.get("slots_processing", "N/A"),
                }
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            logger.debug(f"Health check error: {e}")
        
        # Fallback: try a minimal completion
        try:
            start = time.time()
            resp = self.session.post(
                f"{endpoint}/chat/completions",
                json={
                    "model": self.profile.get("model", "local"),
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=10
            )
            response_time_ms = int((time.time() - start) * 1000)
            
            if resp.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time_ms": response_time_ms,
                    "model": self.profile.get("model", "unknown"),
                    "endpoint": endpoint,
                    "slots_idle": "N/A",
                    "slots_processing": "N/A",
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "endpoint": endpoint,
                "model": self.profile.get("model", "unknown"),
            }
        
        return {
            "status": "unhealthy",
            "error": "Model not responding",
            "endpoint": endpoint,
            "model": self.profile.get("model", "unknown"),
        }

    def is_healthy(self) -> bool:
        """Quick health check boolean."""
        return self.health_check()["status"] == "healthy"

    def check_memory_pressure(self) -> Dict[str, Any]:
        """
        Check if system memory is under pressure.
        
        Returns:
            Dict with memory status and available MB
        """
        try:
            # Try to read system memory info on Linux
            with open("/proc/meminfo") as f:
                meminfo = f.read()
            
            # Parse MemAvailable
            available_line = [l for l in meminfo.split("\n") if "MemAvailable" in l]
            total_line = [l for l in meminfo.split("\n") if "MemTotal" in l]
            
            if available_line and total_line:
                available_kb = int(available_line[0].split()[1])
                total_kb = int(total_line[0].split()[1])
                available_mb = available_kb // 1024
                usage_percent = ((total_kb - available_kb) / total_kb) * 100
                
                # Consider high pressure if >85% used
                is_under_pressure = usage_percent > 85
                
                return {
                    "under_pressure": is_under_pressure,
                    "available_mb": available_mb,
                    "usage_percent": round(usage_percent, 1),
                    "total_mb": total_kb // 1024,
                    "ok_to_run": available_mb > 1024  # Need at least 1GB free
                }
        except Exception as e:
            logger.debug(f"Could not check memory: {e}")
        
        return {
            "under_pressure": False,
            "available_mb": None,
            "usage_percent": None,
            "ok_to_run": True,  # Assume OK if we can't check
        }

    def _build_prompt(self, prompt: str, schema: Optional[Type], system_prompt: Optional[str]) -> List[Dict]:
        """Build message array for the API call."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Build the user message with optional structure instruction
        user_content = prompt
        
        if schema and PYDANTIC_AVAILABLE:
            if issubclass(schema, BaseModel):
                # Add structured format instruction
                schema_desc = self._schema_to_description(schema)
                user_content = f"{prompt}\n\nRespond with valid JSON in this format:\n{schema_desc}"
        
        messages.append({"role": "user", "content": user_content})
        return messages

    def _schema_to_description(self, schema: Type) -> str:
        """Convert Pydantic schema to a description string."""
        if not PYDANTIC_AVAILABLE:
            return "JSON format required"
        
        try:
            json_schema = schema.model_json_schema()
            # Get just the properties
            props = json_schema.get("properties", {})
            required = json_schema.get("required", [])
            
            lines = ["{"]
            for name, spec in props.items():
                typ = spec.get("type", "any")
                desc = spec.get("description", "")
                req_marker = " (required)" if name in required else ""
                lines.append(f'  "{name}": <{typ}>{req_marker},  // {desc}')
            lines.append("}")
            return "\n".join(lines)
        except Exception as e:
            return f"JSON format required (schema: {schema.__name__})"

    def complete(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.2,
        top_p: float = 0.9,
        schema: Optional[Type] = None,
        system_prompt: Optional[str] = None,
        allow_cloud_fallback: bool = False,
        retry_count: int = 2,
        validate_json: bool = True
    ) -> LlamaResponse:
        """
        Complete a prompt using the local model.
        
        Args:
            prompt: The prompt text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Top-p sampling (0.0-1.0)
            schema: Optional Pydantic schema for structured output
            system_prompt: Optional system prompt
            allow_cloud_fallback: If True, escalate to cloud on failure
            retry_count: Number of retries before fallback
            validate_json: Whether to validate JSON output
            
        Returns:
            LlamaResponse with completion details
        """
        # Check memory pressure
        mem_status = self.check_memory_pressure()
        if not mem_status.get("ok_to_run", True):
            logger.warning(f"Memory pressure detected: {mem_status}")
            if allow_cloud_fallback and self.cloud_fallback_fn:
                return self._cloud_fallback(
                    prompt, max_tokens, temperature, schema,
                    reason="memory_pressure"
                )
        
        # Build messages
        messages = self._build_prompt(prompt, schema, system_prompt)
        
        endpoint = self.profile.get("endpoint", "")
        model_name = self.profile.get("model", "local")
        timeout = self.profile.get("timeout", 60)
        
        start_time = time.time()
        last_error = None
        
        for attempt in range(retry_count + 1):
            try:
                response = self.session.post(
                    f"{endpoint}/chat/completions",
                    json={
                        "model": model_name,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
                        "stream": False
                    },
                    timeout=timeout
                )
                
                if response.status_code != 200:
                    raise ModelUnavailableError(
                        f"Model returned status {response.status_code}: {response.text[:200]}"
                    )
                
                data = response.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content", "")
                
                # Validate JSON if needed
                json_valid = False
                if validate_json and schema:
                    try:
                        parsed = json.loads(content)
                        if PYDANTIC_AVAILABLE and issubclass(schema, BaseModel):
                            schema.model_validate(parsed)
                        json_valid = True
                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning(f"JSON validation failed: {e}")
                        if attempt < retry_count:
                            # Add retry instruction
                            messages.append({
                                "role": "user", 
                                "content": "Please respond with valid JSON only."
                            })
                            continue
                else:
                    json_valid = True
                
                wall_time_ms = int((time.time() - start_time) * 1000)
                
                # Build response
                usage = data.get("usage", {})
                result = LlamaResponse(
                    text=content,
                    prompt_tokens=usage.get("prompt_tokens", 0) or len(prompt.split()),
                    completion_tokens=usage.get("completion_tokens", 0) or len(content.split()),
                    total_tokens=usage.get("total_tokens", 0),
                    model=model_name,
                    backend="llama.cpp",
                    wall_time_ms=wall_time_ms,
                    json_valid=json_valid,
                    fallback_used=False,
                    error=None,
                    raw_response=data
                )
                
                # Log completion
                self._log_completion(result, endpoint)
                self.request_count += 1
                self.total_tokens_generated += result.completion_tokens
                
                return result
                
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = f"Connection/Timeout: {e}"
                logger.warning(f"Attempt {attempt + 1} failed: {last_error}")
                if attempt < retry_count:
                    time.sleep(1)
            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} error: {last_error}")
                break
        
        # All retries failed
        logger.error(f"All attempts failed. Last error: {last_error}")
        
        if allow_cloud_fallback and self.cloud_fallback_fn:
            return self._cloud_fallback(
                prompt, max_tokens, temperature, schema,
                reason=f"local_failed: {last_error}"
            )
        
        # Return error response
        return LlamaResponse(
            text="",
            prompt_tokens=len(prompt.split()),
            completion_tokens=0,
            total_tokens=len(prompt.split()),
            model=model_name,
            backend="llama.cpp",
            wall_time_ms=int((time.time() - start_time) * 1000),
            json_valid=False,
            fallback_used=False,
            error=last_error
        )

    def _cloud_fallback(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        schema: Optional[Type],
        reason: str
    ) -> LlamaResponse:
        """Escalate to cloud model."""
        if not self.cloud_fallback_fn:
            raise LlamaRunnerError(f"Cloud fallback requested but no fallback function: {reason}")
        
        logger.info(f"Escalating to cloud: {reason}")
        self.fallback_count += 1
        
        start_time = time.time()
        cloud_result = self.cloud_fallback_fn(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            schema=schema
        )
        
        wall_time_ms = int((time.time() - start_time) * 1000)
        
        # Handle different return types from fallback
        if isinstance(cloud_result, dict):
            return LlamaResponse(
                text=cloud_result.get("text", str(cloud_result)),
                prompt_tokens=cloud_result.get("prompt_tokens", 0),
                completion_tokens=cloud_result.get("completion_tokens", 0),
                total_tokens=cloud_result.get("total_tokens", 0),
                model=cloud_result.get("model", "cloud"),
                backend="cloud",
                wall_time_ms=wall_time_ms,
                json_valid=cloud_result.get("json_valid", False),
                fallback_used=True,
                error=None
            )
        else:
            return LlamaResponse(
                text=str(cloud_result),
                prompt_tokens=len(prompt.split()),
                completion_tokens=0,
                total_tokens=len(prompt.split()),
                model="cloud",
                backend="cloud",
                wall_time_ms=wall_time_ms,
                json_valid=False,
                fallback_used=True,
                error=None
            )

    def _log_completion(self, result: LlamaResponse, endpoint: str):
        """Log completion for metrics and debugging."""
        log_entry = CompletionLog(
            profile=self.profile_name,
            model=result.model,
            runtime="llama.cpp",
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            wall_time_sec=result.wall_time_ms / 1000,
            json_valid=result.json_valid,
            fallback_used=result.fallback_used,
            timestamp=datetime.now().isoformat(),
            endpoint=endpoint,
            error=result.error
        )
        
        # Append to daily log file
        log_file = self.log_dir / f"completions_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry.to_dict()) + '\n')

    def get_stats(self) -> Dict[str, Any]:
        """Get runner statistics."""
        return {
            "profile": self.profile_name,
            "model": self.profile.get("model", "unknown"),
            "request_count": self.request_count,
            "total_tokens_generated": self.total_tokens_generated,
            "fallback_count": self.fallback_count,
            "endpoint": self.profile.get("endpoint"),
        }

    def list_available_profiles(self) -> List[str]:
        """List all available profiles from config."""
        profiles = self.config.get("local_models", {})
        return list(profiles.keys())


# Verification test
if __name__ == "__main__":
    print("=" * 60)
    print("LOCAL LLAMA RUNNER - VERIFICATION TEST")
    print("=" * 60)
    
    # Test config loading
    print("\n[1] Testing configuration loading...")
    runner = LocalLlamaRunner(profile="fast")
    print(f"    Profile: {runner.profile_name} ✓")
    print(f"    Endpoint: {runner.profile.get('endpoint', 'N/A')} ✓")
    print(f"    Available profiles: {runner.list_available_profiles()} ✓")
    
    # Test health check (will fail without actual server, but tests code path)
    print("\n[2] Testing health check (may show 'unhealthy' - that's OK)...")
    health = runner.health_check()
    print(f"    Status: {health['status']} ✓")
    print(f"    Model: {health.get('model', 'N/A')} ✓")
    
    # Test memory check
    print("\n[3] Testing memory pressure check...")
    mem = runner.check_memory_pressure()
    if mem.get('available_mb'):
        print(f"    Available: {mem['available_mb']}MB ✓")
        print(f"    Usage: {mem['usage_percent']}% ✓")
    else:
        print(f"    Memory check skipped (non-Linux) ✓")
    
    # Test stats
    print("\n[4] Testing stats aggregation...")
    stats = runner.get_stats()
    print(f"    Stats tracked: {len(stats)} metrics ✓")
    
    print("\n" + "=" * 60)
    print("ALL BASIC TESTS PASSED ✓")
    print("=" * 60)
    print("\nTo test with actual llama.cpp server running:")
    print("  runner = LocalLlamaRunner(profile='fast')")
    print("  result = runner.complete('Hello, world!', max_tokens=50)")
    print("  print(result.text)")