#!/usr/bin/env python3
"""
Create a new Conductor track with pre-collected responses.

Usage:
    python run_create_track.py --description "Add OAuth2 authentication"
"""

import json
import argparse
from pathlib import Path
from planning_agent import PlanningAgent


def create_example_track():
    """Create an example track for demonstration."""

    # Example: Create operator workflow feature
    responses = {
        "track_type": "feature",
        "priority": "High",
        "description": "Implement operator workflow with simplified interface for stencil selection and inspection execution",
        "user_value": "Operators can execute inspections without needing engineering privileges. Simplified interface reduces training time and errors.",
        "acceptance_criteria": """- Operator sees simplified interface on startup
- Can select stencil from dropdown list
- Can select predefined inspection program
- 'Start Inspection' button executes complete workflow
- Progress shown during execution
- Results displayed in simple format (OK/NOK)
- Cannot access engineering settings
- Session logged with operator ID""",
        "technical_considerations": """- Must integrate with existing consumo_lib modular structure
- Use RoleManager (to be created) for permission checking
- Simplified MainWindow view based on user role
- Leverage existing InspectionCoordinator for execution
- Database: Log operator actions in stencil history""",
        "scope_included": """- Role-based UI display (Operator vs Engineering)
- Simplified stencil selection interface
- Predefined program selection
- One-click inspection execution
- Operator session logging
- Basic results display (pass/fail)""",
        "scope_excluded": """- Recipe creation/editing (engineering only)
- Advanced inspection parameters
- Manual CNC controls
- System configuration changes
- Report generation (quality role)""",
        "dependencies": """- Requires role/permission system to be designed first
- Depends on existing InspectionCoordinator
- Depends on existing RecipeManager
- Blocks Quality workflow track""",
        "risks": """- Role system may need backend changes
- Existing GUI may not support easy role-based views
- Need to ensure operators cannot bypass restrictions
- Testing requires multiple user roles""",
        "estimated_phases": "Medium (3-4 phases)",
        "verification_approach": "Yes (Recommended)"
    }

    agent = PlanningAgent()
    result = agent.create_track(
        description="Implement operator workflow",
        responses=responses
    )

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        print("Creating example track...\n")
        result = create_example_track()

        if result.get("status") == "created":
            print(f"\n{'='*60}")
            print("TRACK CREATED SUCCESSFULLY!")
            print(f"{'='*60}")
            print(f"\nTrack ID: {result['track_id']}")
            print(f"Location: {result['track_dir']}")
            print(f"\nGenerated files:")
            print(f"  1. Spec: {result['spec_file']}")
            print(f"  2. Plan: {result['plan_file']}")
            print(f"  3. Metadata: {result['metadata_file']}")
            print(f"\nNext steps:")
            print(f"  1. Review spec.md to confirm requirements")
            print(f"  2. Review plan.md to confirm phases")
            print(f"  3. Start implementation with: /conductor:implement {result['track_id']}")
    else:
        print("Usage:")
        print("  python run_create_track.py --example    # Create example track")
        print("\nOr use directly with responses dictionary.")
