"""Base state management for workflows."""

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class BaseState(TypedDict):
    """Base state for all workflows."""
    input_data: str
    output_data: Optional[Dict[str, Any]]
    errors: List[str]
    metadata: Dict[str, Any]
    step_results: Dict[str, Any]


class WorkflowConfig(BaseModel):
    """Configuration for workflow execution."""
    model_name: str = Field(default="gpt-4", description="LLM model to use")
    temperature: float = Field(default=0.1, description="Model temperature")
    max_tokens: Optional[int] = Field(default=None, description="Max tokens for response")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    timeout: int = Field(default=60, description="Timeout in seconds")


class EvaluationResult(BaseModel):
    """Result of evaluation for a single input."""
    input_text: str
    expected_output: Optional[Dict[str, Any]] = None
    actual_output: Optional[Dict[str, Any]] = None
    metrics: Dict[str, float] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    execution_time: float = 0.0
    success: bool = False
