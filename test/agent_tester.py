"""Interactive agent testing tool for manual iteration and improvement."""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from src.base.state import WorkflowConfig
from workflows.primary.workflow import PrimaryWorkflow
from workflows.secondary.workflow import SecondaryWorkflow

# Load environment variables
load_dotenv()

app = Flask(__name__)

class AgentTester:
    """Interactive agent testing interface."""
    
    def __init__(self):
        self.workflows = {
            "primary": None,
            "secondary": None
        }
        self.test_history = []
        self.setup_workflows()
    
    def setup_workflows(self):
        """Initialize workflows for testing."""
        try:
            # Primary workflow
            primary_path = Path("workflows/primary")
            primary_config = WorkflowConfig(
                model_name="gpt-4o-mini",
                temperature=0.1,
                max_tokens=None,
                retry_attempts=3,
                timeout=60
            )
            self.workflows["primary"] = PrimaryWorkflow(primary_path, primary_config)
            
            # Secondary workflow  
            secondary_path = Path("workflows/secondary")
            secondary_config = WorkflowConfig(
                model_name="gpt-4o-mini", 
                temperature=0.1,
                max_tokens=None,
                retry_attempts=3,
                timeout=60
            )
            self.workflows["secondary"] = SecondaryWorkflow(secondary_path, secondary_config)
            
            print("✅ Workflows initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing workflows: {e}")
    
    def test_agent(self, workflow_name: str, input_text: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
        """Test an agent with given input."""
        try:
            # Update model if different
            if self.workflows[workflow_name].config.model_name != model:
                self.workflows[workflow_name].config.model_name = model
                self.workflows[workflow_name].llm = self.workflows[workflow_name]._create_llm()
            
            # Process input
            start_time = datetime.now()
            result = self.workflows[workflow_name].process_input(input_text)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            # Create test result
            test_result = {
                "timestamp": start_time.isoformat(),
                "workflow": workflow_name,
                "model": model,
                "input": input_text,
                "output": result,
                "processing_time": processing_time,
                "success": bool(result and result != {}),
                "error": None
            }
            
            # Add to history
            self.test_history.append(test_result)
            
            return test_result
            
        except Exception as e:
            error_result = {
                "timestamp": datetime.now().isoformat(),
                "workflow": workflow_name,
                "model": model,
                "input": input_text,
                "output": None,
                "processing_time": 0,
                "success": False,
                "error": str(e)
            }
            
            self.test_history.append(error_result)
            return error_result
    
    def get_agent_prompt(self, workflow_name: str) -> str:
        """Get the current agent prompt for editing."""
        try:
            workflow = self.workflows[workflow_name]
            if workflow and workflow.agents:
                agent_name = list(workflow.agents.keys())[0]
                return workflow.agents[agent_name].get("prompt", "")
            return ""
        except:
            return ""
    
    def update_agent_prompt(self, workflow_name: str, new_prompt: str) -> bool:
        """Update agent prompt for testing."""
        try:
            workflow = self.workflows[workflow_name]
            if workflow and workflow.agents:
                agent_name = list(workflow.agents.keys())[0]
                workflow.agents[agent_name]["prompt"] = new_prompt
                return True
            return False
        except:
            return False

# Global tester instance
tester = AgentTester()

@app.route('/')
def dashboard():
    """Main testing dashboard."""
    return render_template('agent_dashboard.html')

@app.route('/api/test', methods=['POST'])
def test_endpoint():
    """API endpoint for testing agents."""
    data = request.json
    
    workflow = data.get('workflow', 'primary')
    input_text = data.get('input', '')
    model = data.get('model', 'gpt-4o-mini')
    
    if not input_text.strip():
        return jsonify({"error": "Input text is required"}), 400
    
    result = tester.test_agent(workflow, input_text, model)
    return jsonify(result)

@app.route('/api/prompt/<workflow>', methods=['GET'])
def get_prompt(workflow):
    """Get current agent prompt."""
    prompt = tester.get_agent_prompt(workflow)
    return jsonify({"prompt": prompt})

@app.route('/api/prompt/<workflow>', methods=['POST'])
def update_prompt(workflow):
    """Update agent prompt."""
    data = request.json
    new_prompt = data.get('prompt', '')
    
    success = tester.update_agent_prompt(workflow, new_prompt)
    return jsonify({"success": success})

@app.route('/api/history')
def get_history():
    """Get test history."""
    return jsonify(tester.test_history[-20:])  # Last 20 tests

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear test history."""
    tester.test_history.clear()
    return jsonify({"success": True})

if __name__ == '__main__':
    print("🚀 Starting Agent Tester Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
