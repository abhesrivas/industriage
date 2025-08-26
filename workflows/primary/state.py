"""State management for primary workflow - Work Item Triaging."""

from typing import List, Optional
from pydantic import BaseModel, Field


class WorkRequest(BaseModel):
    """Work request schema."""
    title: str = Field(max_length=100)
    description: str
    status: str = "pending"
    asset_id: Optional[str] = None
    work_type_id: Optional[str] = None
    assigned_to: Optional[str] = None


class WorkOrder(BaseModel):
    """Work order schema."""
    title: str = Field(max_length=100)
    user_query: str
    description: str
    status: str = "pending"
    asset_id: Optional[str] = None
    work_type_id: Optional[str] = None
    assigned_to: Optional[str] = None


class Task(BaseModel):
    """Task schema."""
    title: str = Field(max_length=100)
    description: str
    task_type: str
    status: str = "pending"
    asset_id: Optional[str] = None
    assigned_to: Optional[str] = None


class PrimaryWorkflowOutput(BaseModel):
    """Output schema for primary workflow."""
    work_requests: List[WorkRequest] = Field(default_factory=list)
    work_orders: List[WorkOrder] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)