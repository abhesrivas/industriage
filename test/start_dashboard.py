#!/usr/bin/env python3
"""Quick start script for the agent testing dashboard."""

import subprocess
import sys
from pathlib import Path

def main():
    """Start the agent testing dashboard."""
    print("🚀 Starting Agent Testing Dashboard...")
    print("📋 Make sure you have:")
    print("   - Set up your .env file with API keys")
    print("   - Installed dependencies with: uv sync")
    print("")
    
    # Change to test directory
    test_dir = Path(__file__).parent
    
    try:
        # Run the Flask app
        subprocess.run([
            sys.executable, 
            str(test_dir / "agent_tester.py")
        ], cwd=test_dir.parent)
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    main()
