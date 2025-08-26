# Run evaluation
# python run_workflow.py run primary examples/sample_dataset.json

# With options
python run_workflow.py run \
    primary \
    examples/sample_dataset.json \
    --model gpt-4o-mini \
    --display-format html \
    --output-path outputs

# Validate workflows
# python run_workflow.py validate-workflow primary