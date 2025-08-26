"""State management for secondary workflow - Closing Comment."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ClosingCommentOutput(BaseModel):
    """Output schema for secondary workflow - maintenance closing comments."""
    work_summary: str = Field(description="Summary of work completed")
    equipment_downtime: Optional[float] = Field(description="Equipment downtime in hours", default=None)
    work_duration: Optional[float] = Field(description="Total work duration in hours", default=None)
    parts_used: List[str] = Field(default_factory=list, description="List of parts/materials used")
    issues_found: List[str] = Field(default_factory=list, description="Issues discovered during work")
    follow_up_required: bool = Field(default=False, description="Whether follow-up work is needed")
    follow_up_details: Optional[str] = Field(default=None, description="Details about required follow-up")
    technician_notes: Optional[str] = Field(default=None, description="Additional technician observations")
    completion_status: str = Field(description="Status of work completion", default="completed")
    asset_condition: Optional[str] = Field(default=None, description="Final condition of asset")
