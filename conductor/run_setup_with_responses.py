#!/usr/bin/env python3
"""
Execute Conductor Setup with pre-collected responses.
"""

import json
from pathlib import Path
from setup_agent import SetupAgent

# Load responses
responses_file = Path(__file__).parent / "setup_responses.json"
with open(responses_file, 'r', encoding='utf-8') as f:
    responses = json.load(f)

# Run setup
agent = SetupAgent()
result = agent.run_setup(responses_dict=responses)

print(f"\nSetup result: {result['status']}")
