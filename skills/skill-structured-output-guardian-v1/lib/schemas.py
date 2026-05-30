#!/usr/bin/env python3
"""
Schemas - Pydantic models for structured output validation.

These schemas define the expected output formats from local models.
"""

from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator


class TaskClassification(BaseModel):
    """Classification of a task for routing."""
    task_type: str = Field(description="Type of task: summarization, extraction, classification, etc.")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(description="Risk assessment")
    complexity: Literal["simple", "moderate", "complex"] = Field(description="Task complexity")
    estimated_tokens: int = Field(description="Estimated token count needed")
    requires_privacy: bool = Field(description="Whether task needs local processing")
    
    # Routing decision
    recommended_profile: Literal["fast", "balanced", "overnight", "cloud"] = Field(
        description="Recommended model profile"
    )


class EvidencePack(BaseModel):
    """Evidence retrieved for RAG."""
    source_id: str = Field(description="Unique source identifier")
    title: str = Field(description="Source title")
    date: str = Field(description="Source date")
    chunk_id: str = Field(description="Chunk identifier")
    text: str = Field(description="Retrieved text content")
    retrieval_score: float = Field(description="Initial retrieval score", ge=0, le=1)
    rerank_score: float = Field(description="Reranking score", ge=0, le=1)


class LocalTaskResult(BaseModel):
    """
    Standard output format for local model tasks.
    """
    task_id: str = Field(description="Unique task identifier")
    status: Literal["success", "partial", "failed", "needs_cloud"] = Field(
        description="Task completion status"
    )
    confidence: float = Field(description="Model confidence 0.0-1.0", ge=0, le=1)
    evidence_grade: Literal["A", "B", "C", "D", "F"] = Field(
        description="Quality of supporting evidence"
    )
    summary: str = Field(description="Executive summary of findings")
    key_findings: List[str] = Field(default_factory=list, description="Key findings list")
    citations: List[str] = Field(default_factory=list, description="Source citations")
    needs_human_review: bool = Field(description="Flag for human review")
    escalation_reason: Optional[str] = Field(default=None, description="Why escalated to cloud")
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Confidence must be between 0 and 1')
        return round(v, 2)


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    field: str = Field(description="Field that failed validation")
    error_type: str = Field(description="Type of validation error")
    message: str = Field(description="Human-readable error message")
    

class ValidationReport(BaseModel):
    """Full validation report with metrics."""
    schema_name: str = Field(description="Name of validated schema")
    is_valid: bool = Field(description="Whether validation passed")
    confidence_score: float = Field(description="Overall confidence", ge=0, le=1)
    schema_compliance: float = Field(description="Schema compliance percentage", ge=0, le=1)
    errors: List[ValidationErrorDetail] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    processing_time_ms: int = Field(description="Time to validate in ms")
    

class SummaryResult(BaseModel):
    """Generic summary output."""
    title: str = Field(description="Generated title")
    summary: str = Field(description="Main summary text")
    key_points: List[str] = Field(default_factory=list, description="Bullet points")
    word_count: int = Field(description="Summary word count", ge=0)


class ExtractionResult(BaseModel):
    """Generic extraction output."""
    extracted_data: Dict[str, Any] = Field(description="Extracted key-value pairs")
    confidence: float = Field(description="Extraction confidence", ge=0, le=1)
    missing_fields: List[str] = Field(default_factory=list, description="Fields not found")
    raw_matches: List[str] = Field(default_factory=list, description="Raw matches found")


class ClassificationResult(BaseModel):
    """Classification output with confidence."""
    category: str = Field(description="Assigned category")
    confidence: float = Field(description="Classification confidence", ge=0, le=1)
    alternatives: List[Dict[str, float]] = Field(
        default_factory=list, 
        description="Alternative categories with scores"
    )
    reasoning: str = Field(description="Why this classification was chosen")


class ComparisonResult(BaseModel):
    """Document/item comparison output."""
    similarity_score: float = Field(description="Similarity 0.0-1.0", ge=0, le=1)
    is_duplicate: bool = Field(description="Whether items are duplicates")
    confidence: float = Field(description="Duplicate detection confidence", ge=0, le=1)
    key_differences: List[str] = Field(default_factory=list, description="Key differences found")
    merge_recommendation: Optional[str] = Field(None, description="Recommended merge action")


# Export all schemas
__all__ = [
    "TaskClassification",
    "EvidencePack", 
    "LocalTaskResult",
    "ValidationErrorDetail",
    "ValidationReport",
    "SummaryResult",
    "ExtractionResult",
    "ClassificationResult",
    "ComparisonResult",
]
