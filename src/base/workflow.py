"""Base workflow implementation."""

import json
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel

from .state import BaseState, WorkflowConfig, EvaluationResult


class BaseWorkflow(ABC):
    """Base class for all workflows."""
    
    def __init__(self, workflow_path: Path, config: WorkflowConfig):
        self.workflow_path = workflow_path
        self.config = config
        self.agents = self._load_agents()
        self.graph_config = self._load_graph_config()
        self.llm = self._create_llm()
    
    def _load_agents(self) -> Dict[str, Dict[str, Any]]:
        """Load agent configurations from the agents directory."""
        agents = {}
        agents_dir = self.workflow_path / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.json"):
                with open(agent_file, 'r') as f:
                    agent_config = json.load(f)
                    agents[agent_config["name"]] = agent_config
        return agents
    
    def _load_graph_config(self) -> Dict[str, Any]:
        """Load graph configuration."""
        graph_file = self.workflow_path / "graph.json"
        if graph_file.exists() and graph_file.stat().st_size > 0:
            with open(graph_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _create_llm(self) -> BaseLanguageModel:
        """Create LLM instance based on config."""
        if "gpt" in self.config.model_name.lower():
            return ChatOpenAI(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
        elif "claude" in self.config.model_name.lower():
            return ChatAnthropic(
                model=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
        else:
            raise ValueError(f"Unsupported model: {self.config.model_name}")
    
    @abstractmethod
    def get_output_schema(self) -> Type[BaseModel]:
        """Return the expected output schema for this workflow."""
        pass
    
    @abstractmethod
    def process_input(self, input_text: str) -> Dict[str, Any]:
        """Process a single input through the workflow."""
        pass
    
    @abstractmethod
    def evaluate_output(self, input_text: str, actual_output: Dict[str, Any], 
                       expected_output: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Evaluate the output and return metrics."""
        pass
    
    def run_evaluation(self, dataset: List[Dict[str, Any]]) -> List[EvaluationResult]:
        """Run evaluation on a dataset."""
        results = []
        
        for item in dataset:
            start_time = time.time()
            result = EvaluationResult(input_text=item["input"])
            
            try:
                # Process input
                actual_output = self.process_input(item["input"])
                result.actual_output = actual_output
                
                # Get expected output if available
                expected_output = item.get("expected_output")
                result.expected_output = expected_output
                
                # Evaluate
                metrics = self.evaluate_output(
                    item["input"], 
                    actual_output, 
                    expected_output
                )
                result.metrics = metrics
                result.success = True
                
            except Exception as e:
                result.errors.append(str(e))
                result.success = False
            
            result.execution_time = time.time() - start_time
            results.append(result)
        
        return results
