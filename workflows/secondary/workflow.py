"""Secondary workflow implementation - Closing Comment."""

from pathlib import Path
from typing import Any, Dict, Type

from src.base import BaseWorkflow, GraphBuilder, EvaluationFramework
from src.base.evaluator import SchemaValidityMetric, DowntimeExtractionMetric, CompletenessMetric
from .state import ClosingCommentOutput


class SecondaryWorkflow(BaseWorkflow):
    """Closing Comment workflow for maintenance completion notes."""
    
    def __init__(self, workflow_path: Path, config):
        super().__init__(workflow_path, config)
        self.graph_builder = GraphBuilder(self)
        self.evaluation_framework = self._setup_evaluation()
    
    def get_output_schema(self) -> Type[ClosingCommentOutput]:
        """Return the expected output schema."""
        return ClosingCommentOutput
    
    def process_input(self, input_text: str) -> Dict[str, Any]:
        """Process closing comment through the workflow."""
        result = self.graph_builder.execute(input_text)
        
        if result["output_data"]:
            return result["output_data"]
        else:
            # Return empty structure if processing failed
            print("❌ Processing failed")
            return {
                "work_summary": "",
                "equipment_downtime": None,
                "work_duration": None,
                "parts_used": [],
                "issues_found": [],
                "follow_up_required": False,
                "completion_status": "unknown"
            }
    
    def evaluate_output(self, input_text: str, actual_output: Dict[str, Any], 
                       expected_output: Dict[str, Any] = None) -> Dict[str, float]:
        """Evaluate output using secondary workflow metrics."""
        return self.evaluation_framework.evaluate(input_text, actual_output, expected_output)
    
    def _setup_evaluation(self) -> EvaluationFramework:
        """Setup evaluation metrics for secondary workflow."""
        framework = EvaluationFramework()
        
        # Add secondary workflow metrics
        framework.add_metric(SchemaValidityMetric(ClosingCommentOutput))
        framework.add_metric(DowntimeExtractionMetric())
        framework.add_metric(CompletenessMetric())
        
        return framework
