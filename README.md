# Thunderbird Agentic Workflow System

A flexible, LangGraph-based evaluation framework for industrial maintenance workflows using large language models.

## 🏗️ Architecture

This system provides a modular framework for creating and evaluating agentic workflows:

```
├── src/
│   ├── base/                    # Core framework components
│   │   ├── workflow.py         # Base workflow class
│   │   ├── graph_builder.py    # LangGraph integration
│   │   ├── evaluator.py        # Evaluation metrics
│   │   └── state.py            # State management
│   └── display.py              # Results presentation
├── workflows/                   # Workflow implementations
│   ├── primary/                # Work Item Triaging
│   │   ├── agents/
│   │   ├── graph.json
│   │   ├── state.py
│   │   ├── workflow.py
│   │   └── transformations.py
│   └── secondary/              # Closing Comment
│       ├── agents/
│       ├── graph.json
│       ├── state.py
│       └── workflow.py
└── run_workflow.py             # Main execution script
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -e .

# Set up environment variables
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### 2. Run Evaluation

```bash
# Run primary workflow evaluation
python run_workflow.py run primary path/to/dataset.json

# Run with specific model and options
python run_workflow.py run primary dataset.json \
    --model gpt-4 \
    --temperature 0.1 \
    --display-format html \
    --output results.html \
    --max-items 10
```

### 3. Available Commands

```bash
# List available workflows
python run_workflow.py list-workflows

# Validate workflow configuration
python run_workflow.py validate-workflow primary

# Get help
python run_workflow.py --help
```

## 📊 Workflows

### Primary: Work Item Triaging

Transforms voice transcriptions from maintenance technicians into structured work items.

**Input**: Plain text voice transcription
**Output**: Categorized work requests, work orders, and tasks with asset mapping

**Metrics**:
- Schema Validity: JSON structure compliance
- Category Classification: Correct routing based on urgency
- Asset Identification: Accurate asset ID mapping

### Secondary: Closing Comment

Parses maintenance completion notes into structured records.

**Input**: Maintenance closing comments
**Output**: Work summary with downtime extraction and follow-up assessment

**Metrics**:
- Schema Validity: JSON structure compliance  
- Downtime Extraction: Equipment downtime vs work duration accuracy
- Completeness: All relevant details captured

## 🔧 Creating New Workflows

### 1. Create Workflow Directory

```bash
mkdir workflows/my_workflow
mkdir workflows/my_workflow/agents
```

### 2. Define State Schema

Create `workflows/my_workflow/state.py`:

```python
from pydantic import BaseModel
from typing import List

class MyWorkflowOutput(BaseModel):
    result: str
    confidence: float
    items: List[str]
```

### 3. Implement Workflow Class

Create `workflows/my_workflow/workflow.py`:

```python
from pathlib import Path
from typing import Any, Dict, Type
from src.base import BaseWorkflow, GraphBuilder, EvaluationFramework
from .state import MyWorkflowOutput

class MyWorkflow(BaseWorkflow):
    def get_output_schema(self) -> Type[MyWorkflowOutput]:
        return MyWorkflowOutput
    
    def process_input(self, input_text: str) -> Dict[str, Any]:
        result = self.graph_builder.execute(input_text)
        return result["output_data"] or {}
    
    def evaluate_output(self, input_text: str, actual_output: Dict[str, Any], 
                       expected_output: Dict[str, Any] = None) -> Dict[str, float]:
        return self.evaluation_framework.evaluate(input_text, actual_output, expected_output)
```

### 4. Configure Agent

Create `workflows/my_workflow/agents/my_agent.json`:

```json
{
    "name": "my_agent",
    "description": "Agent description",
    "prompt": "Your detailed system prompt here..."
}
```

### 5. Define Graph Structure

Create `workflows/my_workflow/graph.json`:

```json
{
    "workflow_name": "my_workflow",
    "description": "Workflow description",
    "nodes": [
        {
            "id": "process_input",
            "type": "agent_node", 
            "agent": "my_agent"
        }
    ],
    "edges": [
        {"from": "process_input", "to": "END"}
    ],
    "entry_point": "process_input"
}
```

### 6. Register Workflow

Add to `run_workflow.py`:

```python
from workflows.my_workflow.workflow import MyWorkflow

def get_workflow_class(workflow_name: str):
    workflows = {
        "primary": PrimaryWorkflow,
        "secondary": SecondaryWorkflow,
        "my_workflow": MyWorkflow,  # Add here
    }
    # ...
```

## 📈 Evaluation Metrics

### Built-in Metrics

- **SchemaValidityMetric**: Validates JSON structure via Pydantic
- **CategoryClassificationMetric**: Evaluates categorization accuracy
- **AssetIdentificationMetric**: Checks asset ID mapping
- **DowntimeExtractionMetric**: Validates downtime vs work duration
- **CompletenessMetric**: Ensures all required fields are captured

### Custom Metrics

Create custom metrics by extending `BaseMetric`:

```python
from src.base.evaluator import BaseMetric

class MyCustomMetric(BaseMetric):
    @property
    def name(self) -> str:
        return "my_custom_metric"
    
    def evaluate(self, input_text: str, actual_output: Dict[str, Any], 
                expected_output: Dict[str, Any] = None) -> float:
        # Return score between 0.0 and 1.0
        return 0.85
```

## 🎨 Results Presentation

### Rich Console Output

```bash
python run_workflow.py run primary dataset.json --display-format rich
```

### HTML Reports

```bash
python run_workflow.py run primary dataset.json --display-format html --output report.html
```

### JSON Export

```bash
python run_workflow.py run primary dataset.json --display-format json --output results.json
```

## 🔧 Configuration

### Model Configuration

Supported models:
- OpenAI: `gpt-4`, `gpt-3.5-turbo`
- Anthropic: `claude-3-sonnet`, `claude-3-haiku`

### Environment Variables

```bash
# Required for OpenAI models
export OPENAI_API_KEY="your-key"

# Required for Anthropic models  
export ANTHROPIC_API_KEY="your-key"

# Optional: Custom base URLs
export OPENAI_BASE_URL="https://custom-endpoint"
```

## 📝 Dataset Format

Expected JSON format for datasets:

```json
[
    {
        "input": "Voice transcription text here...",
        "expected_output": {
            "work_requests": [...],
            "work_orders": [...]
        }
    }
]
```

## 🧪 Testing

```bash
# Validate all workflows
python run_workflow.py validate-workflow primary
python run_workflow.py validate-workflow secondary

# Test with small dataset
python run_workflow.py run primary test_dataset.json --max-items 5
```

## 🤝 Contributing

1. Create new workflows in the `workflows/` directory
2. Follow the established patterns for state, workflow, and agent definitions
3. Add comprehensive evaluation metrics
4. Update the workflow registry in `run_workflow.py`

## 📄 License

MIT License - see LICENSE file for details.