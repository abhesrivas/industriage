"""Primary workflow implementation - Work Item Triaging."""

from pathlib import Path
from typing import Any, Dict, Type

from src.base import BaseWorkflow, GraphBuilder, EvaluationFramework
from src.base.evaluator import SchemaValidityMetric, CategoryClassificationMetric, AssetIdentificationMetric
from .state import PrimaryWorkflowOutput


class PrimaryWorkflow(BaseWorkflow):
    """Work Item Triaging workflow from voice transcriptions."""
    
    def __init__(self, workflow_path: Path, config):
        super().__init__(workflow_path, config)
        self.graph_builder = GraphBuilder(self)
        self.evaluation_framework = self._setup_evaluation()
    
    def get_output_schema(self) -> Type[PrimaryWorkflowOutput]:
        """Return the expected output schema."""
        return PrimaryWorkflowOutput
    
    def process_input(self, input_text: str) -> Dict[str, Any]:
        """Process voice transcription through the workflow."""
        result = self.graph_builder.execute(input_text)
        
        if result["output_data"]:
            return result["output_data"]
        else:
            # Return empty structure if processing failed
            return {
                "work_requests": [],
                "work_orders": [],
                "tasks": []
            }
    
    def evaluate_output(self, input_text: str, actual_output: Dict[str, Any], 
                       expected_output: Dict[str, Any] = None) -> Dict[str, float]:
        """Evaluate output using primary workflow metrics."""
        return self.evaluation_framework.evaluate(input_text, actual_output, expected_output)
    
    def _setup_evaluation(self) -> EvaluationFramework:
        """Setup evaluation metrics for primary workflow."""
        framework = EvaluationFramework()
        
        # Add primary workflow metrics
        framework.add_metric(SchemaValidityMetric(PrimaryWorkflowOutput))
        framework.add_metric(CategoryClassificationMetric())
        framework.add_metric(AssetIdentificationMetric())
        
        return framework