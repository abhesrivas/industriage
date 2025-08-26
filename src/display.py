"""Results presentation and display utilities."""

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns
import pandas as pd

from src.base.state import EvaluationResult


class ResultsPresenter:
    """Comprehensive results presentation system."""
    
    def __init__(self):
        self.console = Console()
    
    def display_rich_summary(self, results: List[EvaluationResult]):
        """Display rich console summary of evaluation results."""
        
        # Header
        self.console.print("\n" + "="*80, style="bold blue")
        self.console.print("📊 EVALUATION RESULTS SUMMARY", style="bold blue", justify="center")
        self.console.print("="*80 + "\n", style="bold blue")
        
        # Overall metrics
        self._display_overall_metrics(results)
        
        # Metrics breakdown
        self._display_metrics_breakdown(results)
        
        # Error analysis
        self._display_error_analysis(results)
        
        # Individual results (top failures and successes)
        self._display_sample_results(results)
    
    def _display_overall_metrics(self, results: List[EvaluationResult]):
        """Display overall performance metrics."""
        total = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total - successful
        avg_time = sum(r.execution_time for r in results) / total if results else 0
        
        # Create metrics table
        table = Table(title="📈 Overall Performance", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="green", width=15)
        table.add_column("Percentage", style="yellow", width=15)
        
        table.add_row("Total Items", str(total), "100%")
        table.add_row("Successful", str(successful), f"{successful/total*100:.1f}%" if total > 0 else "0%")
        table.add_row("Failed", str(failed), f"{failed/total*100:.1f}%" if total > 0 else "0%")
        table.add_row("Avg Time", f"{avg_time:.2f}s", "-")
        
        self.console.print(table)
        self.console.print()
    
    def _display_metrics_breakdown(self, results: List[EvaluationResult]):
        """Display breakdown of individual metrics."""
        if not results or not results[0].metrics:
            return
        
        # Collect all metric names
        all_metrics = set()
        for result in results:
            all_metrics.update(result.metrics.keys())
        
        if not all_metrics:
            return
        
        table = Table(title="🎯 Metrics Breakdown", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan", width=25)
        table.add_column("Average", style="green", width=12)
        table.add_column("Min", style="red", width=8)
        table.add_column("Max", style="green", width=8)
        table.add_column("Success Rate", style="yellow", width=15)
        
        for metric in sorted(all_metrics):
            values = [r.metrics.get(metric, 0) for r in results if metric in r.metrics]
            if values:
                avg_val = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                success_rate = sum(1 for v in values if v > 0.8) / len(values) * 100
                
                table.add_row(
                    metric.replace("_", " ").title(),
                    f"{avg_val:.3f}",
                    f"{min_val:.3f}",
                    f"{max_val:.3f}",
                    f"{success_rate:.1f}%"
                )
        
        self.console.print(table)
        self.console.print()
    
    def _display_error_analysis(self, results: List[EvaluationResult]):
        """Display error analysis."""
        failed_results = [r for r in results if not r.success]
        
        if not failed_results:
            self.console.print("✅ No errors found!", style="bold green")
            return
        
        # Count error types
        error_counts = {}
        for result in failed_results:
            for error in result.errors:
                error_type = error.split(":")[0] if ":" in error else "Unknown"
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        table = Table(title="❌ Error Analysis", show_header=True, header_style="bold red")
        table.add_column("Error Type", style="red", width=30)
        table.add_column("Count", style="yellow", width=10)
        table.add_column("Percentage", style="cyan", width=15)
        
        total_errors = sum(error_counts.values())
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / total_errors * 100
            table.add_row(error_type, str(count), f"{percentage:.1f}%")
        
        self.console.print(table)
        self.console.print()
    
    def _display_sample_results(self, results: List[EvaluationResult]):
        """Display sample successful and failed results."""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        # Show top failures
        if failed:
            self.console.print("🔍 Sample Failed Cases:", style="bold red")
            for i, result in enumerate(failed[:3]):
                panel_content = f"Input: {result.input_text[:100]}...\n"
                if result.errors:
                    panel_content += f"Error: {result.errors[0]}"
                
                panel = Panel(
                    panel_content,
                    title=f"Failed Case {i+1}",
                    border_style="red"
                )
                self.console.print(panel)
        
        # Show top successes
        if successful:
            self.console.print("\n✅ Sample Successful Cases:", style="bold green")
            # Sort by aggregate metric score
            successful_sorted = sorted(successful, 
                                     key=lambda x: sum(x.metrics.values()) / len(x.metrics) if x.metrics else 0, 
                                     reverse=True)
            
            for i, result in enumerate(successful_sorted[:2]):
                panel_content = f"Input: {result.input_text[:100]}...\n"
                if result.metrics:
                    avg_score = sum(result.metrics.values()) / len(result.metrics)
                    panel_content += f"Average Score: {avg_score:.3f}"
                
                panel = Panel(
                    panel_content,
                    title=f"Top Success {i+1}",
                    border_style="green"
                )
                self.console.print(panel)
    
    def generate_html_report(self, results: List[EvaluationResult], output_path: str):
        """Generate comprehensive HTML report."""
        
        # Calculate summary stats
        total = len(results)
        successful = sum(1 for r in results if r.success)
        success_rate = successful / total * 100 if total > 0 else 0
        avg_time = sum(r.execution_time for r in results) / total if results else 0
        
        # Collect metrics data
        metrics_data = {}
        if results and results[0].metrics:
            for metric in results[0].metrics.keys():
                values = [r.metrics.get(metric, 0) for r in results if metric in r.metrics]
                if values:
                    metrics_data[metric] = {
                        'average': sum(values) / len(values),
                        'min': min(values),
                        'max': max(values),
                        'success_rate': sum(1 for v in values if v > 0.8) / len(values) * 100
                    }
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Workflow Evaluation Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #333; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: bold; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .details {{ margin: 20px 0; }}
        .result-item {{ margin: 10px 0; padding: 15px; border-left: 4px solid #007bff; background: #f8f9fa; }}
        .error {{ border-left-color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Workflow Evaluation Results</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="metric-card">
                <div class="metric-value">{total}</div>
                <div class="metric-label">Total Items</div>
            </div>
            <div class="metric-card">
                <div class="metric-value success">{success_rate:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{avg_time:.2f}s</div>
                <div class="metric-label">Avg Time</div>
            </div>
        </div>
        
        <h2>📊 Metrics Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Average</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Success Rate (>0.8)</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for metric, data in metrics_data.items():
            html_content += f"""
                <tr>
                    <td>{metric.replace('_', ' ').title()}</td>
                    <td>{data['average']:.3f}</td>
                    <td>{data['min']:.3f}</td>
                    <td>{data['max']:.3f}</td>
                    <td>{data['success_rate']:.1f}%</td>
                </tr>
            """
        
        html_content += """
            </tbody>
        </table>
        
        <h2>📋 Individual Results</h2>
        <div class="details">
        """
        
        for i, result in enumerate(results):
            status_class = "success" if result.success else "error"
            status_text = "✅ Success" if result.success else "❌ Failed"
            
            html_content += f"""
            <div class="result-item {status_class}">
                <h4>Item {i+1} - {status_text}</h4>
                <p><strong>Input:</strong> {result.input_text[:200]}...</p>
                <p><strong>Execution Time:</strong> {result.execution_time:.2f}s</p>
            """
            
            if result.metrics:
                html_content += "<p><strong>Metrics:</strong> "
                for metric, score in result.metrics.items():
                    html_content += f"{metric}: {score:.3f} | "
                html_content += "</p>"
            
            if result.errors:
                html_content += f"<p><strong>Errors:</strong> {', '.join(result.errors)}</p>"
            
            html_content += "</div>"
        
        html_content += """
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def save_json_results(self, results: List[EvaluationResult], output_path: str):
        """Save results as JSON for further analysis."""
        json_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_items": len(results),
                "successful": sum(1 for r in results if r.success),
                "success_rate": sum(1 for r in results if r.success) / len(results) if results else 0,
                "average_execution_time": sum(r.execution_time for r in results) / len(results) if results else 0
            },
            "results": [
                {
                    "input_text": result.input_text,
                    "success": result.success,
                    "metrics": result.metrics,
                    "errors": result.errors,
                    "execution_time": result.execution_time,
                    "actual_output": result.actual_output,
                    "expected_output": result.expected_output
                }
                for result in results
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
    
    def create_comparison_report(self, results_list: List[List[EvaluationResult]], 
                               labels: List[str], output_path: str):
        """Create comparison report between different model runs."""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Model Comparison Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; }}
        .comparison-table th, .comparison-table td {{ padding: 12px; border: 1px solid #ddd; text-align: center; }}
        .comparison-table th {{ background-color: #f8f9fa; }}
        .best {{ background-color: #d4edda; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>🔄 Model Comparison Report</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <table class="comparison-table">
        <thead>
            <tr>
                <th>Model</th>
                <th>Success Rate</th>
                <th>Avg Time</th>
                <th>Total Items</th>
            </tr>
        </thead>
        <tbody>
        """
        
        for results, label in zip(results_list, labels):
            success_rate = sum(1 for r in results if r.success) / len(results) * 100 if results else 0
            avg_time = sum(r.execution_time for r in results) / len(results) if results else 0
            
            html_content += f"""
            <tr>
                <td>{label}</td>
                <td>{success_rate:.1f}%</td>
                <td>{avg_time:.2f}s</td>
                <td>{len(results)}</td>
            </tr>
            """
        
        html_content += """
        </tbody>
    </table>
</body>
</html>
        """
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def generate_workflow_graph(self, workflow_instance, output_path: str):
        """Generate PNG visualization using LangGraph's native export."""
        try:
            # Use LangGraph's built-in graph visualization
            if hasattr(workflow_instance, 'graph_builder') and workflow_instance.graph_builder.graph:
                # Get the compiled graph
                graph = workflow_instance.graph_builder.graph
                
                # Use LangGraph's native PNG export
                png_data = graph.get_graph().draw_mermaid_png()
                
                # Save the PNG data to file
                with open(output_path, 'wb') as f:
                    f.write(png_data)
            else:
                # Fallback: build graph first if not available
                workflow_instance.graph_builder.build_graph()
                graph = workflow_instance.graph_builder.graph
                
                png_data = graph.get_graph().draw_mermaid_png()
                with open(output_path, 'wb') as f:
                    f.write(png_data)
                    
        except Exception as e:
            self.console.print(f"Warning: Could not generate LangGraph PNG: {e}", style="yellow")
            # Fallback to custom visualization if LangGraph export fails
            self._generate_custom_graph(workflow_instance, output_path)
    
    def _generate_custom_graph(self, workflow_instance, output_path: str):
        """Fallback custom graph generation using matplotlib."""
        try:
            # Create figure and axis
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 8)
            ax.axis('off')
            
            # Get workflow information
            workflow_name = workflow_instance.__class__.__name__
            agents = list(workflow_instance.agents.keys())
            
            # Draw workflow components
            # Title
            ax.text(5, 7.5, f"{workflow_name} Architecture", 
                   fontsize=16, fontweight='bold', ha='center')
            
            # Input box
            input_box = FancyBboxPatch((0.5, 5.5), 2, 1, 
                                     boxstyle="round,pad=0.1", 
                                     facecolor='lightblue', 
                                     edgecolor='blue')
            ax.add_patch(input_box)
            ax.text(1.5, 6, 'Input\nText', ha='center', va='center', fontweight='bold')
            
            # Agent processing
            agent_box = FancyBboxPatch((4, 5.5), 2, 1, 
                                     boxstyle="round,pad=0.1", 
                                     facecolor='lightgreen', 
                                     edgecolor='green')
            ax.add_patch(agent_box)
            ax.text(5, 6, f'Agent\n{agents[0] if agents else "Processing"}', 
                   ha='center', va='center', fontweight='bold')
            
            # Validation
            validation_box = FancyBboxPatch((7.5, 5.5), 2, 1, 
                                          boxstyle="round,pad=0.1", 
                                          facecolor='lightyellow', 
                                          edgecolor='orange')
            ax.add_patch(validation_box)
            ax.text(8.5, 6, 'Schema\nValidation', ha='center', va='center', fontweight='bold')
            
            # Output
            output_box = FancyBboxPatch((4, 3.5), 2, 1, 
                                      boxstyle="round,pad=0.1", 
                                      facecolor='lightcoral', 
                                      edgecolor='red')
            ax.add_patch(output_box)
            ax.text(5, 4, 'Structured\nOutput', ha='center', va='center', fontweight='bold')
            
            # Draw arrows
            arrow_props = dict(arrowstyle='->', lw=2, color='black')
            ax.annotate('', xy=(3.8, 6), xytext=(2.7, 6), arrowprops=arrow_props)
            ax.annotate('', xy=(7.3, 6), xytext=(6.2, 6), arrowprops=arrow_props)
            ax.annotate('', xy=(5, 4.7), xytext=(8.5, 5.3), arrowprops=arrow_props)
            
            # Add metrics info
            metrics_text = "Evaluation Metrics:\n"
            if hasattr(workflow_instance, 'evaluation_framework'):
                metrics = list(workflow_instance.evaluation_framework.metrics.keys())
                for metric in metrics[:3]:  # Show first 3 metrics
                    metrics_text += f"• {metric.replace('_', ' ').title()}\n"
            
            ax.text(1, 2.5, metrics_text, fontsize=10, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            self.console.print(f"Warning: Could not generate custom graph: {e}", style="yellow")
    
    def generate_mermaid_diagram(self, workflow_instance, output_path: str):
        """Generate Mermaid diagram file for workflow visualization."""
        try:
            workflow_name = workflow_instance.__class__.__name__
            agents = list(workflow_instance.agents.keys())
            
            mermaid_content = f"""graph TD
    A[Input Text] --> B[{agents[0] if agents else 'Agent Processing'}]
    B --> C[Schema Validation]
    C --> D[Structured Output]
    
    subgraph "Evaluation Metrics"
        E[Schema Validity]
        F[Classification Accuracy]
        G[Asset Identification]
    end
    
    D --> E
    D --> F
    D --> G
    
    classDef inputClass fill:#e1f5fe
    classDef processClass fill:#e8f5e8
    classDef validateClass fill:#fff3e0
    classDef outputClass fill:#fce4ec
    classDef metricClass fill:#f3e5f5
    
    class A inputClass
    class B processClass
    class C validateClass
    class D outputClass
    class E,F,G metricClass
"""
            
            with open(output_path, 'w') as f:
                f.write(mermaid_content)
                
        except Exception as e:
            self.console.print(f"Warning: Could not generate mermaid diagram: {e}", style="yellow")
    
    def generate_text_report(self, results: List[EvaluationResult], output_path: str):
        """Generate comprehensive text classification report."""
        try:
            report_lines = []
            report_lines.append("=" * 80)
            report_lines.append("WORKFLOW EVALUATION CLASSIFICATION REPORT")
            report_lines.append("=" * 80)
            report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
            
            # Overall Statistics
            total = len(results)
            successful = sum(1 for r in results if r.success)
            failed = total - successful
            success_rate = successful / total * 100 if total > 0 else 0
            avg_time = sum(r.execution_time for r in results) / total if results else 0
            
            report_lines.append("OVERALL PERFORMANCE")
            report_lines.append("-" * 40)
            report_lines.append(f"Total Items Processed: {total}")
            report_lines.append(f"Successful: {successful} ({success_rate:.1f}%)")
            report_lines.append(f"Failed: {failed} ({(100-success_rate):.1f}%)")
            report_lines.append(f"Average Processing Time: {avg_time:.3f}s")
            report_lines.append("")
            
            # Metrics Breakdown
            if results and results[0].metrics:
                report_lines.append("METRICS BREAKDOWN")
                report_lines.append("-" * 40)
                
                all_metrics = set()
                for result in results:
                    all_metrics.update(result.metrics.keys())
                
                for metric in sorted(all_metrics):
                    values = [r.metrics.get(metric, 0) for r in results if metric in r.metrics]
                    if values:
                        avg_val = sum(values) / len(values)
                        min_val = min(values)
                        max_val = max(values)
                        success_count = sum(1 for v in values if v > 0.8)
                        success_rate_metric = success_count / len(values) * 100
                        
                        report_lines.append(f"{metric.replace('_', ' ').title()}:")
                        report_lines.append(f"  Average: {avg_val:.3f}")
                        report_lines.append(f"  Range: {min_val:.3f} - {max_val:.3f}")
                        report_lines.append(f"  Success Rate (>0.8): {success_rate_metric:.1f}%")
                        report_lines.append("")
            
            # Error Analysis
            failed_results = [r for r in results if not r.success]
            if failed_results:
                report_lines.append("ERROR ANALYSIS")
                report_lines.append("-" * 40)
                
                error_counts = {}
                for result in failed_results:
                    for error in result.errors:
                        error_type = error.split(":")[0] if ":" in error else "Unknown"
                        error_counts[error_type] = error_counts.get(error_type, 0) + 1
                
                total_errors = sum(error_counts.values())
                for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = count / total_errors * 100
                    report_lines.append(f"{error_type}: {count} ({percentage:.1f}%)")
                
                report_lines.append("")
            
            # Individual Results Summary
            report_lines.append("INDIVIDUAL RESULTS SUMMARY")
            report_lines.append("-" * 40)
            
            for i, result in enumerate(results):
                status = "SUCCESS" if result.success else "FAILED"
                report_lines.append(f"Item {i+1}: {status} ({result.execution_time:.3f}s)")
                
                if result.metrics:
                    avg_score = sum(result.metrics.values()) / len(result.metrics)
                    report_lines.append(f"  Average Score: {avg_score:.3f}")
                    
                    # Show individual metric scores
                    for metric, score in result.metrics.items():
                        report_lines.append(f"  {metric}: {score:.3f}")
                
                if result.errors:
                    report_lines.append(f"  Errors: {'; '.join(result.errors)}")
                
                report_lines.append("")
            
            # Write to file
            with open(output_path, 'w') as f:
                f.write('\n'.join(report_lines))
                
        except Exception as e:
            self.console.print(f"Warning: Could not generate text report: {e}", style="yellow")