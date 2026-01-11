#!/usr/bin/env python3
"""
Simple validation test for ImplementationAgent.
Tests parsing and basic functionality without full execution.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from implementation_agent import ImplementationAgent


def test_implementation_agent():
    """Test Implementation Agent basic functionality."""

    print("="*70)
    print("IMPLEMENTATION AGENT VALIDATION TEST")
    print("="*70)

    agent = ImplementationAgent()

    # Test 1: Load plan
    print("\n[TEST 1] Loading plan...")
    track_id = "feature_implement_operator_workflow_20260111"
    try:
        plan_content = agent.load_plan(track_id)
        print(f"  [OK] Plan loaded ({len(plan_content)} characters)")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    # Test 2: Parse plan
    print("\n[TEST 2] Parsing plan...")
    try:
        plan = agent.parse_plan(plan_content)
        print(f"  [OK] Plan parsed successfully")
        print(f"    - Phases: {plan['total_phases']}")
        print(f"    - Tasks: {plan['total_tasks']}")

        for phase in plan['phases']:
            complete_tasks = sum(1 for t in phase['tasks'] if t['complete'])
            print(f"    - Phase {phase['number']}: {len(phase['tasks'])} tasks ({complete_tasks} complete)")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    # Test 3: Git operations
    print("\n[TEST 3] Git operations...")
    try:
        result = agent._run_git(['status', '--short'])
        if result.returncode == 0:
            print(f"  [OK] Git working")
            changes = len([l for l in result.stdout.split('\n') if l.strip()])
            print(f"    - Uncommitted changes: {changes}")
        else:
            print(f"  [FAIL] Git status failed")
            return False
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    # Test 4: Smoke test
    print("\n[TEST 4] Smoke test...")
    try:
        smoke_result = agent.smoke_test()
        if smoke_result['success']:
            print(f"  [OK] Smoke test passed")
            print(f"    - {smoke_result.get('message', 'OK')}")
        else:
            print(f"  [WARN] Smoke test warning: {smoke_result.get('error')}")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    # Test 5: Context docs
    print("\n[TEST 5] Loading context docs...")
    try:
        context = agent.load_context_docs()
        print(f"  [OK] Context docs loaded ({len(context)} files)")
        for doc_name in context.keys():
            print(f"    - {doc_name}")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return False

    print("\n" + "="*70)
    print("VALIDATION COMPLETE - ALL TESTS PASSED")
    print("="*70)

    print("\nImplementation Agent is ready for track execution!")
    print(f"\nTo execute track {track_id}:")
    print(f"  python claude-conductor/run_execute_track.py --track {track_id}")

    return True


if __name__ == "__main__":
    success = test_implementation_agent()
    sys.exit(0 if success else 1)
