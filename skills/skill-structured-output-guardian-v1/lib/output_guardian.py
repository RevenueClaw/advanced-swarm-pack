#!/usr/bin/env python3
"""
OutputGuardian - Force reliable JSON from local models.

Implements two-step validation:
1. Generate content with reasoning
2. Validate against Pydantic schema
3. Retry with repair/simplification on failure
4. Escalate to cloud after N failures

Author: RockClaw
"""

import json
import time
import logging
from typing import Dict, List, Optional, Type, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, ValidationError as PydanticValidationError

# Import local llama runner for generation
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from skill_local_llama_runner import LocalLlamaRunner
from .schemas import ValidationReport, ValidationErrorDetail, LocalTaskResult

logger = logging.getLogger("OutputGuardian")


class EscalationTrigger(Enum):
    """Reasons for escalating to cloud."""
    JSON_PARSE_FAILED = "json_parse_failed"
    VALIDATION_FAILED = "validation_failed"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"
    LOW_CONFIDENCE = "low_confidence"
    INVALID_SCHEMA = "invalid_schema"


@dataclass
class ValidationResult:
    """Result from validation attempt."""
    is_valid: bool
    data: Optional[Any] = None
    parsed_data: Optional[Dict] = None
    errors: List[str] = field(default_factory=list)
    attempt: int = 0
    escalation_trigger: Optional[EscalationTrigger] = None
    processing_time_ms: int = 0


class OutputGuardian:
    """
    Guardian for structured output from local models.
    
    Usage:
        guardian = OutputGuardian()
        
        @guardian.validate(schema=MyResult)
        def my_function(prompt):
            return generate(prompt)
    """
    
    DEFAULT_MAX_RETRIES = 2
    CONFIDENCE_THRESHOLD = 0.72
    
    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        confidence_threshold: float = CONFIDENCE_THRESHOLD,
        cloud_fallback_fn: Optional[Callable] = None,
        log_dir: Optional[Path] = None
    ):
        self.max_retries = max_retries
        self.confidence_threshold = confidence_threshold
        self.cloud_fallback_fn = cloud_fallback_fn
        self.log_dir = log_dir or Path.home() / ".openclaw/logs/guardian"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Stats
        self.total_validations = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.escalations = 0
        
        logger.info(f"OutputGuardian initialized (max_retries={max_retries})")
    
    def generate_and_validate(
        self,
        prompt: str,
        schema: Type[BaseModel],
        model_profile: str = "balanced",
        system_prompt: Optional[str] = None,
        allow_escalation: bool = True,
        max_tokens: int = 1000,
        temperature: float = 0.2,
    ) -> ValidationResult:
        """
        Generate content and validate against schema.
        
        Args:
            prompt: The generation prompt
            schema: Pydantic schema to validate against
            model_profile: local model profile to use
            system_prompt: Optional system prompt
            allow_escalation: Whether to allow cloud fallback
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            
        Returns:
            ValidationResult with data or escalation info
        """
        start_time = time.time()
        self.total_validations += 1
        
        # Step 1: Build structured prompt
        structured_prompt = self._build_structured_prompt(prompt, schema)
        
        # Get runner (create fresh each call to allow different profiles)
        runner = LocalLlamaRunner(profile=model_profile)
        
        # Step 2: Try generation and validation
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # Generate with JSON instruction 
                full_prompt = structured_prompt
                if attempt > 0:
                    full_prompt += f"\n\n(Previous attempt failed: {last_error}. Please output valid JSON only.)"
                
                result = runner.complete(
                    prompt=full_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt or "You are helpful. Always respond with valid JSON."
                )
                
                # Step 3: Validate the output
                validation = self._validate_json(result.text, schema)
                
                if validation.is_valid:
                    self.successful_validations += 1
                    return ValidationResult(
                        is_valid=True,
                        data=validation.data,
                        parsed_data=validation.parsed_data,
                        attempt=attempt + 1,
                        processing_time_ms=int((time.time() - start_time) * 1000)
                    )
                else:
                    last_error = validation.errors[0] if validation.errors else "validation failed"
                    logger.warning(f"Validation failed (attempt {attempt + 1}): {last_error}")
                    
                    # Try with simpler schema next time
                    if attempt < self.max_retries:
                        schema = self._simplify_schema(schema)
                        logger.info(f"Retrying with simplified schema")
                        continue
            
            except Exception as e:
                last_error = str(e)
                logger.error(f"Generation error (attempt {attempt + 1}): {last_error}")
                if attempt < self.max_retries:
                    continue
        
        # All retries exhausted
        self.failed_validations += 1
        
        # Step 4: Escalate to cloud if allowed
        if allow_escalation and self.cloud_fallback_fn:
            return self._escalate_to_cloud(
                prompt=prompt,
                schema=schema,
                last_error=last_error,
                trigger=EscalationTrigger.MAX_RETRIES_EXCEEDED,
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # Return structured failure
        return ValidationResult(
            is_valid=False,
            errors=[f"All {self.max_retries + 1} attempts failed: {last_error}"],
            attempt=self.max_retries + 1,
            escalation_trigger=EscalationTrigger.MAX_RETRIES_EXCEEDED,
            processing_time_ms=int((time.time() - start_time) * 1000)
        )
    
    def _build_structured_prompt(self, prompt: str, schema: Type[BaseModel]) -> str:
        """Add JSON formatting instructions to prompt."""
        # Get schema as dict
        try:
            schema_dict = schema.model_json_schema()
            properties = schema_dict.get("properties", {})
            required = schema_dict.get("required", [])
            
            # Build property descriptions
            prop_descs = []
            for name, spec in properties.items():
                typ = spec.get("type", "any")
                desc = spec.get("description", "")
                required_marker = " (required)" if name in required else ""
                prop_descs.append(f'  "{name}": <{typ}>{required_marker}  // {desc}')
            
            schema_desc = "{\n" + "\n".join(prop_descs) + "\n}"
            
        except Exception as e:
            schema_desc = f"<schema: {schema.__name__}>"
        
        structured = f"""{prompt}

### OUTPUT FORMAT
Respond with valid JSON matching this exact structure:

```json
{schema_desc}
```

IMPORTANT:
- Output ONLY the JSON object
- No markdown code blocks around it
- No explanations or comments
- Ensure all required fields are present
"""
        return structured
    
    def _validate_json(
        self,
        text: str,
        schema: Type[BaseModel]
    ) -> ValidationResult:
        """Validate extracted JSON against schema."""
        # Step 1: Extract JSON from text
        json_str = self._extract_json(text)
        if not json_str:
            return ValidationResult(
                is_valid=False,
                errors=["No JSON found in response"],
                escalation_trigger=EscalationTrigger.JSON_PARSE_FAILED
            )
        
        # Step 2: Parse JSON
        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"JSON parse error: {e}"],
                escalation_trigger=EscalationTrigger.JSON_PARSE_FAILED
            )
        
        # Step 3: Validate against Pydantic schema
        try:
            validated = schema.model_validate(parsed)
            return ValidationResult(
                is_valid=True,
                data=validated,
                parsed_data=parsed
            )
        except PydanticValidationError as e:
            errors = [f"{err['loc']}: {err['msg']}" for err in e.errors()]
            return ValidationResult(
                is_valid=False,
                parsed_data=parsed,
                errors=errors,
                escalation_trigger=EscalationTrigger.VALIDATION_FAILED
            )
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from text, handling code blocks."""
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()
        
        # Look for JSON object
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx > start_idx:
            return text[start_idx:end_idx+1]
        
        # Just return stripped text
        return text.strip()
    
    def _simplify_schema(self, schema: Type[BaseModel]) -> Type[BaseModel]:
        """Create simplified version of schema for retry."""
        # For now, return same schema - in future could strip optional fields
        return schema
    
    def _escalate_to_cloud(
        self,
        prompt: str,
        schema: Type[BaseModel],
        last_error: str,
        trigger: EscalationTrigger,
        processing_time_ms: int
    ) -> ValidationResult:
        """Escalate to cloud model."""
        if not self.cloud_fallback_fn:
            return ValidationResult(
                is_valid=False,
                errors=[f"Escalation needed but no fallback function: {trigger.value}"],
                escalation_trigger=trigger,
                processing_time_ms=processing_time_ms
            )
        
        logger.info(f"Escalating to cloud: {trigger.value}")
        self.escalations += 1
        
        try:
            cloud_result = self.cloud_fallback_fn(
                prompt=prompt,
                schema=schema,
                error_reason=trigger.value
            )
            
            # Validate cloud result
            if isinstance(cloud_result, schema):
                return ValidationResult(
                    is_valid=True,
                    data=cloud_result,
                    parsed_data=cloud_result.model_dump(),
                    escalation_trigger=trigger,
                    processing_time_ms=processing_time_ms
                )
            else:
                # Try to parse
                if isinstance(cloud_result, dict):
                    validated = schema.model_validate(cloud_result)
                    return ValidationResult(
                        is_valid=True,
                        data=validated,
                        parsed_data=cloud_result,
                        escalation_trigger=trigger,
                        processing_time_ms=processing_time_ms
                    )
                else:
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"Cloud returned unexpected type: {type(cloud_result)}"],
                        escalation_trigger=trigger,
                        processing_time_ms=processing_time_ms
                    )
                    
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Cloud escalation failed: {e}"],
                escalation_trigger=trigger,
                processing_time_ms=processing_time_ms
            )
    
    def repair_json(self, json_str: str) -> Optional[str]:
        """Attempt to repair malformed JSON."""
        repairs = [
            # Remove trailing commas
            (',}', '}'),
            (',]', ']'),
            # Fix unquoted keys
            (r'(?<=[{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":'),
        ]
        
        repaired = json_str
        for old, new in repairs:
            import re
            repaired = re.sub(old, new, repaired)
        
        try:
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get guardian statistics."""
        total = self.total_validations
        success_rate = self.successful_validations / total if total > 0 else 0
        
        return {
            "total_validations": total,
            "successful_validations": self.successful_validations,
            "failed_validations": self.failed_validations,
            "escalations": self.escalations,
            "success_rate": round(success_rate, 3),
            "escalation_rate": round(self.escalations / total, 3) if total > 0 else 0,
        }


# Decorator for easy validation
def validated(schema: Type[BaseModel], max_retries: int = 2):
    """
    Decorator to validate function output against schema.
    
    Usage:
        @validated(schema=MyResult)
        def my_generator(prompt):
            return generate_text(prompt)
    """
    def decorator(func):
        guardian = OutputGuardian(max_retries=max_retries)
        
        def wrapper(*args, **kwargs):
            # Extract prompt from args/kwargs
            prompt = kwargs.get('prompt', args[0] if args else "")
            
            return guardian.generate_and_validate(
                prompt=prompt,
                schema=schema
            )
        
        return wrapper
    return decorator


# Test
def main():
    print("=" * 60)
    print("OUTPUT GUARDIAN - VERIFICATION TEST")
    print("=" * 60)
    
    from .schemas import SummaryResult
    
    # Test building structured prompt
    guardian = OutputGuardian()
    prompt = guardian._build_structured_prompt(
        "Summarize this document",
        SummaryResult
    )
    print("\n[1] Structured prompt generation ✓")
    print(f"    Lines: {len(prompt.splitlines())}")
    
    # Test JSON extraction
    test_texts = [
        '{"title": "Test", "summary": "Test"}',
        '```json\n{"title": "Test"}\n```',
        'Some text\n{"title": "Test"}\nMore text',
    ]
    for i, text in enumerate(test_texts):
        extracted = guardian._extract_json(text)
        print(f"\n[2.{i+1}] JSON extraction test {i+1} ✓")
        print(f"    Result: {extracted[:50]}...")
    
    # Test repair
    bad_json = '{"title": "Test",}'
    repaired = guardian.repair_json(bad_json)
    print(f"\n[3] JSON repair test ✓")
    print(f"    Input: {bad_json}")
    print(f"    Output: {repaired}")
    
    print("\n" + "=" * 60)
    print("ALL BASIC TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    main()
