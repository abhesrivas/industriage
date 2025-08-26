"""Main workflow runner with dataset integration."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.progress import Progress, TaskID
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.base.state import WorkflowConfig
from workflows.primary.workflow import PrimaryWorkflow
from workflows.secondary.workflow import SecondaryWorkflow
from src.display import ResultsPresenter

app = typer.Typer()
console = Console()


def load_dataset(dataset_path: str) -> List[Dict]:
    """Load dataset from JSON file."""
    with open(dataset_path, 'r') as f:
        return json.load(f)


def get_workflow_class(workflow_name: str):
    """Get workflow class by name."""
    workflows = {
        "primary": PrimaryWorkflow,
        "secondary": SecondaryWorkflow
    }
    
    if workflow_name not in workflows:
        raise ValueError(f"Unknown workflow: {workflow_name}. Available: {list(workflows.keys())}")
    
    return workflows[workflow_name]


def create_output_directory(workflow_name: str, model_name: str, base_output_path: str = "outputs") -> Path:
    """Create structured output directory for workflow run."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_clean = model_name.replace("-", "_").replace(".", "_")
    
    output_dir = Path(base_output_path) / workflow_name / f"{timestamp}_{model_clean}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    console.print(f"📁 Created output directory: {output_dir}")
    return output_dir


@app.command()
def run(
    workflow: str = typer.Argument(..., help="Workflow name (primary/secondary)"),
    dataset: str = typer.Argument(..., help="Path to dataset JSON file"),
    model: str = typer.Option("gpt-4", help="Model to use (gpt-4, claude-3-sonnet, etc.)"),
    temperature: float = typer.Option(0.1, help="Model temperature"),
    output_path: str = typer.Option("outputs", help="Base output directory path"),
    display_format: str = typer.Option("rich", help="Display format (rich/html/json)"),
    max_items: Optional[int] = typer.Option(None, help="Maximum number of items to process")
):
    """Run workflow evaluation on dataset."""
    
    console.print(f"🚀 Running {workflow} workflow evaluation", style="bold blue")
    
    # Load dataset
    try:
        dataset_items = load_dataset(dataset)
        if max_items:
            dataset_items = dataset_items[:max_items]
        console.print(f"📊 Loaded {len(dataset_items)} items from dataset")
    except Exception as e:
        console.print(f"❌ Error loading dataset: {e}", style="bold red")
        raise typer.Exit(1)
    
    # Setup workflow
    workflow_path = Path(f"workflows/{workflow}")
    if not workflow_path.exists():
        console.print(f"❌ Workflow directory not found: {workflow_path}", style="bold red")
        raise typer.Exit(1)
    
    config = WorkflowConfig(
        model_name=model,
        temperature=temperature,
        max_tokens=None,
        retry_attempts=3,
        timeout=60
    )
    
    # Initialize workflow
    try:
        workflow_class = get_workflow_class(workflow)
        workflow_instance = workflow_class(workflow_path, config)
        console.print(f"✅ Initialized {workflow} workflow with {model}")
    except Exception as e:
        console.print(f"❌ Error initializing workflow: {e}", style="bold red")
        raise typer.Exit(1)
    
    # Create output directory
    output_dir = create_output_directory(workflow, model, output_path)
    
    # Run evaluation
    console.print("🔄 Running evaluation...")
    
    with Progress() as progress:
        task = progress.add_task("Processing items...", total=len(dataset_items))
        
        try:
            results = []
            for i, item in enumerate(dataset_items):
                result = workflow_instance.run_evaluation([item])[0]
                results.append(result)
                progress.update(task, advance=1)
                
                # Show progress every 5 items
                if (i + 1) % 5 == 0:
                    success_rate = sum(1 for r in results if r.success) / len(results)
                    console.print(f"Progress: {i+1}/{len(dataset_items)} | Success rate: {success_rate:.2%}")
        
        except KeyboardInterrupt:
            console.print("\n⚠️ Interrupted by user", style="yellow")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"\n❌ Error during evaluation: {e}", style="bold red")
            raise typer.Exit(1)
    
    # Present results and save all outputs
    presenter = ResultsPresenter()
    
    # Always generate all output formats in the structured directory
    console.print("📊 Generating comprehensive outputs...")
    
    # 1. HTML Dashboard
    html_output = output_dir / "dashboard.html"
    presenter.generate_html_report(results, html_output)
    console.print(f"📄 Dashboard saved to: {html_output}")
    
    # 2. JSON Results
    json_output = output_dir / "results.json"
    presenter.save_json_results(results, json_output)
    console.print(f"💾 JSON results saved to: {json_output}")
    
    # 3. Text Classification Report
    txt_output = output_dir / "classification_report.txt"
    presenter.generate_text_report(results, txt_output)
    console.print(f"📝 Text report saved to: {txt_output}")
    
    # 4. Workflow Graph PNG
    graph_png = output_dir / "workflow_graph.png"
    presenter.generate_workflow_graph(workflow_instance, graph_png)
    console.print(f"🖼️ Workflow graph saved to: {graph_png}")
    
    # 5. Mermaid Diagram
    mermaid_output = output_dir / "workflow_diagram.mmd"
    presenter.generate_mermaid_diagram(workflow_instance, mermaid_output)
    console.print(f"🔄 Mermaid diagram saved to: {mermaid_output}")
    
    # Display format for console output
    if display_format == "rich":
        presenter.display_rich_summary(results)
    
    # Summary
    success_rate = sum(1 for r in results if r.success) / len(results)
    avg_time = sum(r.execution_time for r in results) / len(results)
    
    console.print(f"\n📈 Final Results:", style="bold green")
    console.print(f"   Success Rate: {success_rate:.2%}")
    console.print(f"   Average Time: {avg_time:.2f}s")
    console.print(f"   Total Items: {len(results)}")
    console.print(f"   Output Directory: {output_dir}")


@app.command()
def list_workflows():
    """List available workflows."""
    workflows_dir = Path("workflows")
    if not workflows_dir.exists():
        console.print("❌ No workflows directory found", style="bold red")
        return
    
    console.print("📋 Available workflows:", style="bold blue")
    for workflow_dir in workflows_dir.iterdir():
        if workflow_dir.is_dir():
            graph_file = workflow_dir / "graph.json"
            if graph_file.exists():
                console.print(f"  • {workflow_dir.name}")
            else:
                console.print(f"  • {workflow_dir.name} (incomplete - missing graph.json)", style="yellow")


@app.command()
def validate_workflow(
    workflow: str = typer.Argument(..., help="Workflow name to validate")
):
    """Validate workflow configuration."""
    workflow_path = Path(f"workflows/{workflow}")
    
    if not workflow_path.exists():
        console.print(f"❌ Workflow not found: {workflow}", style="bold red")
        raise typer.Exit(1)
    
    console.print(f"🔍 Validating {workflow} workflow...")
    
    # Check required files
    required_files = ["graph.json", "state.py", "workflow.py"]
    missing_files = []
    
    for file in required_files:
        if not (workflow_path / file).exists():
            missing_files.append(file)
    
    if missing_files:
        console.print(f"❌ Missing required files: {missing_files}", style="bold red")
        raise typer.Exit(1)
    
    # Check agents directory
    agents_dir = workflow_path / "agents"
    if not agents_dir.exists() or not list(agents_dir.glob("*.json")):
        console.print("⚠️ No agents found in agents/ directory", style="yellow")
    
    console.print("✅ Workflow validation passed", style="bold green")


if __name__ == "__main__":
    app()