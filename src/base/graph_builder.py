"""LangGraph graph builder for workflows."""

import json
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .state import BaseState


class GraphBuilder:
    """Builds LangGraph execution graphs for workflows."""
    
    def __init__(self, workflow):
        self.workflow = workflow
        self.graph = None
        self.graph_config = self._load_graph_config()
    
    def _load_graph_config(self) -> Dict[str, Any]:
        """Load graph configuration from graph.json."""
        graph_path = self.workflow.workflow_path / "graph.json"
        with open(graph_path, 'r') as f:
            return json.load(f)
    
    def build_graph(self) -> StateGraph:
        """Build the execution graph based on workflow configuration."""
        graph = StateGraph(BaseState)
        
        # Add agent nodes dynamically from config
        for agent_name in self.graph_config["agents"]:
            graph.add_node(agent_name, self._create_agent_node(agent_name))
        
        # Add validation node
        graph.add_node("validate_output", self._validate_output_node)
        
        # Add edges from config
        for edge in self.graph_config["edges"]:
            from_node, to_node = edge
            if from_node == "START":
                graph.set_entry_point(to_node)
            elif to_node == "END":
                # Add validation before END
                graph.add_edge(from_node, "validate_output")
                graph.add_edge("validate_output", END)
            else:
                graph.add_edge(from_node, to_node)
        
        self.graph = graph.compile()
        return self.graph
    
    def _create_agent_node(self, agent_name: str):
        """Create a node function for the specified agent."""
        def agent_node(state: BaseState) -> BaseState:
            try:
                agent = self.workflow.agents[agent_name]
                
                # Create prompt template
                prompt = ChatPromptTemplate.from_messages([
                    ("system", agent["config"]["prompt"]),
                    ("human", "{input}")
                ])
                
                # Create chain
                chain = prompt | self.workflow.llm | JsonOutputParser()
                
                # Process input
                result = chain.invoke({"input": state["input_data"]})
                
                state["output_data"] = result
                state["step_results"][agent_name] = result
                
            except Exception as e:
                error_msg = f"Error in {agent_name}: {str(e)}"
                state["errors"].append(error_msg)
                state["output_data"] = None
                print(f" {error_msg}")  # Debug output
            
            return state
        
        return agent_node
    
    def _validate_output_node(self, state: BaseState) -> BaseState:
        """Validate output against schema."""
        try:
            if state["output_data"]:
                # Validate against workflow schema
                schema_class = self.workflow.get_output_schema()
                validated = schema_class.model_validate(state["output_data"])
                state["step_results"]["validate_output"] = {
                    "valid": True,
                    "validated_data": validated.model_dump()
                }
            else:
                state["step_results"]["validate_output"] = {
                    "valid": False,
                    "error": "No output data to validate"
                }
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            state["errors"].append(error_msg)
            state["step_results"]["validate_output"] = {
                "valid": False,
                "error": error_msg
            }
        
        return state
    
    def execute(self, input_text: str) -> Dict[str, Any]:
        """Execute the workflow on input text."""
        if not self.graph:
            self.build_graph()
        
        initial_state = BaseState(
            input_data=input_text,
            output_data=None,
            errors=[],
            metadata={},
            step_results={}
        )
        
        result = self.graph.invoke(initial_state)
        return result
