"""Transformation utilities for primary workflow."""

import re
from typing import Dict, List, Optional


class AssetMapper:
    """Maps asset mentions to standardized asset IDs."""
    
    ASSET_MAPPINGS = {
        "tunnel-001": [
            "tunnel washer 1", "tunnel 1", "tunnel one", "tw1", "tw 1"
        ],
        "tunnel-002": [
            "tunnel washer 2", "tunnel 2", "tunnel two", "tw2", "tw 2"
        ],
        "dryer-012": [
            "dryer 12", "clm 12", "clm dryer 12", "d12", "dryer twelve"
        ],
        "dryer-022": [
            "dryer 22", "incline dryer 22", "d22", "dryer twenty two"
        ],
        "ironer-004": [
            "ironer 4", "iron 4", "ironer number 4", "i4", "ironer four"
        ]
    }
    
    @classmethod
    def extract_asset_id(cls, text: str) -> Optional[str]:
        """Extract asset ID from text."""
        text_lower = text.lower()
        
        for asset_id, variations in cls.ASSET_MAPPINGS.items():
            for variation in variations:
                if variation in text_lower:
                    return asset_id
        
        return None


class WorkTypeClassifier:
    """Classifies work type based on urgency indicators."""
    
    WORK_TYPE_MAPPINGS = {
        "emergency-001": [
            "emergency", "critical", "safety hazard", "production stopped", 
            "leak", "failure", "down", "broken", "not working"
        ],
        "urgent-002": [
            "urgent", "asap", "as soon as possible", "high priority", 
            "priority", "soon", "quickly"
        ],
        "routine-003": [
            "routine", "scheduled", "preventive", "pm", "regular", 
            "maintenance", "inspection"
        ],
        "low-004": [
            "when possible", "low priority", "whenever", "non-urgent", 
            "eventually", "sometime"
        ]
    }
    
    @classmethod
    def classify_work_type(cls, text: str) -> Optional[str]:
        """Classify work type based on text content."""
        text_lower = text.lower()
        
        for work_type_id, keywords in cls.WORK_TYPE_MAPPINGS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return work_type_id
        
        return None


class CategoryClassifier:
    """Classifies input into work requests, work orders, or tasks."""
    
    @classmethod
    def classify_category(cls, text: str) -> str:
        """Determine the appropriate category based on explicit mentions."""
        text_lower = text.lower()
        
        # Explicit work request indicators
        if any(phrase in text_lower for phrase in [
            "work request", "create a work request", "put in a work request"
        ]):
            return "work_request"
        
        # Explicit work order indicators
        if any(phrase in text_lower for phrase in [
            "work order", "create a work order", "generate a work order"
        ]):
            return "work_order"
        
        # Task indicators
        if any(phrase in text_lower for phrase in [
            "inspection", "check", "verify", "inspect"
        ]):
            return "inspection_task"
        
        if any(phrase in text_lower for phrase in [
            "order", "call", "coordinate", "administrative", "admin"
        ]):
            return "general_task"
        
        # Default based on urgency
        work_type = WorkTypeClassifier.classify_work_type(text)
        if work_type in ["emergency-001", "urgent-002"]:
            return "work_order"
        else:
            return "work_request"


class PersonnelExtractor:
    """Extracts personnel assignments from text."""
    
    @classmethod
    def extract_assigned_to(cls, text: str) -> Optional[str]:
        """Extract personnel assignment from text."""
        # Look for patterns like "assign to John", "for Mike", "send to Sarah"
        patterns = [
            r"assign(?:ed)?\s+to\s+(\w+)",
            r"for\s+(\w+)",
            r"send\s+to\s+(\w+)",
            r"give\s+to\s+(\w+)",
            r"(\w+)\s+should\s+handle",
            r"(\w+)\s+can\s+do"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).title()
        
        return None