"""Evaluation framework for workflow outputs."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, ValidationError

from .state import EvaluationResult


class BaseMetric(ABC):
    """Base class for evaluation metrics."""
    
    @abstractmethod
    def evaluate(self, input_text: str, actual_output: Dict[str, Any], 
                expected_output: Optional[Dict[str, Any]] = None) -> float:
        """Evaluate and return a score between 0 and 1."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Metric name."""
        pass


class SchemaValidityMetric(BaseMetric):
    """Validates JSON structure compliance via Pydantic."""
    
    def __init__(self, schema_class: Type[BaseModel]):
        self.schema_class = schema_class
    
    @property
    def name(self) -> str:
        return "schema_validity"
    
    def evaluate(self, input_text: str, actual_output: Dict[str, Any], 
                expected_output: Optional[Dict[str, Any]] = None) -> float:
        try:
            self.schema_class.model_validate(actual_output)
            return 1.0
        except ValidationError:
            return 0.0


class CategoryClassificationMetric(BaseMetric):
    """Evaluates correct categorization for work item triaging."""
    
    @property
    def name(self) -> str:
        return "category_classification_accuracy"
    
    def evaluate(self, input_text: str, actual_output: Dict[str, Any], 
                expected_output: Optional[Dict[str, Any]] = None) -> float:
        if not expected_output:
            return 0.0
        
        # Check if the right categories were created
        expected_categories = set()
        actual_categories = set()
        
        if expected_output.get("work_requests"):
            expected_categories.add("work_requests")
        if expected_output.get("work_orders"):
            expected_categories.add("work_orders")
        if expected_output.get("tasks"):
            expected_categories.add("tasks")
        
        if actual_output.get("work_requests"):
            actual_categories.add("work_requests")
        if actual_output.get("work_orders"):
            actual_categories.add("work_orders")
        if actual_output.get("tasks"):
            actual_categories.add("tasks")
        
        if expected_categories == actual_categories:
            return 1.0
        
        # Partial credit for overlapping categories
        intersection = expected_categories.intersection(actual_categories)
        union = expected_categories.union(actual_categories)
        return len(intersection) / len(union) if union else 0.0


class AssetIdentificationMetric(BaseMetric):
    """Evaluates accurate mapping of assets to asset IDs."""
    
    ASSET_MAPPINGS = {
        "tunnel-001": ["tunnel washer 1", "tunnel 1", "tunnel one"],
        "tunnel-002": ["tunnel washer 2", "tunnel 2", "tunnel two"],
        "dryer-012": ["dryer 12", "clm 12", "clm dryer 12"],
        "dryer-022": ["dryer 22", "incline dryer 22"],
        "ironer-004": ["ironer 4", "iron 4", "ironer number 4"]
    }
    
    @property
    def name(self) -> str:
        return "asset_identification_accuracy"
    
    def evaluate(self, input_text: str, actual_output: Dict[str, Any], 
                expected_output: Optional[Dict[str, Any]] = None) -> float:
        # Extract mentioned assets from input
        input_lower = input_text.lower()
        expected_assets = set()
        
        for asset_id, variations in self.ASSET_MAPPINGS.items():
            for variation in variations:
                if variation in input_lower:
                    expected_assets.add(asset_id)
                    break
        
        if not expected_assets:
            return 1.0  # No assets mentioned, so perfect score
        
        # Extract asset_ids from actual output
        actual_assets = set()
        for category in ["work_requests", "work_orders", "tasks"]:
            items = actual_output.get(category, [])
            for item in items:
                asset_id = item.get("asset_id")
                if asset_id:
                    actual_assets.add(asset_id)
        
        if expected_assets == actual_assets:
            return 1.0
        
        # Calculate overlap
        intersection = expected_assets.intersection(actual_assets)
        return len(intersection) / len(expected_assets)


class DowntimeExtractionMetric(BaseMetric):
    """Evaluates correct identification of equipment downtime vs work duration."""
    
    @property
    def name(self) -> str:
        return "downtime_extraction_accuracy"
    
    def evaluate(self, input_text: str, actual_output: Dict[str, Any], 
                expected_output: Optional[Dict[str, Any]] = None) -> float:
        if not expected_output:
            return 0.0
        
        expected_downtime = expected_output.get("equipment_downtime")
        actual_downtime = actual_output.get("equipment_downtime")
        
        if expected_downtime == actual_downtime:
            return 1.0
        
        # For numeric values, calculate relative accuracy
        if isinstance(expected_downtime, (int, float)) and isinstance(actual_downtime, (int, float)):
            if expected_downtime == 0:
                return 1.0 if actual_downtime == 0 else 0.0
            
            relative_error = abs(expected_downtime - actual_downtime) / expected_downtime
            return max(0.0, 1.0 - relative_error)
        
        return 0.0


class CompletenessMetric(BaseMetric):
    """Evaluates if all relevant work details are captured."""
    
    @property
    def name(self) -> str:
        return "completeness_score"
    
    def evaluate(self, input_text: str, actual_output: Dict[str, Any], 
                expected_output: Optional[Dict[str, Any]] = None) -> float:
        if not expected_output:
            return 0.0
        
        # Check for required fields
        required_fields = ["title", "description", "status"]
        score = 0.0
        total_items = 0
        
        for category in ["work_requests", "work_orders", "tasks"]:
            items = actual_output.get(category, [])
            expected_items = expected_output.get(category, [])
            
            for i, item in enumerate(items):
                total_items += 1
                item_score = 0.0
                
                # Check required fields
                for field in required_fields:
                    if field in item and item[field]:
                        item_score += 1
                
                # Normalize by number of required fields
                item_score /= len(required_fields)
                score += item_score
        
        return score / total_items if total_items > 0 else 0.0


class EvaluationFramework:
    """Main evaluation framework that orchestrates metrics."""
    
    def __init__(self):
        self.metrics = {}
    
    def add_metric(self, metric: BaseMetric):
        """Add a metric to the framework."""
        self.metrics[metric.name] = metric
    
    def evaluate(self, input_text: str, actual_output: Dict[str, Any], 
                expected_output: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Run all metrics and return scores."""
        scores = {}
        
        for name, metric in self.metrics.items():
            try:
                score = metric.evaluate(input_text, actual_output, expected_output)
                scores[name] = score
            except Exception as e:
                scores[name] = 0.0
                print(f"Error in metric {name}: {e}")
        
        return scores
    
    def get_aggregate_score(self, scores: Dict[str, float]) -> float:
        """Calculate aggregate score from individual metrics."""
        if not scores:
            return 0.0
        return sum(scores.values()) / len(scores)
