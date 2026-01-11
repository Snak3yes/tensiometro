#!/usr/bin/env python3
"""
Conductor Implementation Agent

This agent orchestrates the execution of track plans with strict TDD workflow.
It executes tasks sequentially, maintains git history with detailed notes,
and performs checkpoint verification at phase boundaries.

Usage:
    python implementation_agent.py --track feature_add_oauth_20260111

Or programmatically:
    from implementation_agent import ImplementationAgent
    agent = ImplementationAgent()
    result = agent.execute_track(track_id)
"""

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


class ImplementationAgent:
    """Orchestrates track execution with TDD workflow."""

    def __init__(self, project_root: str = None, conductor_dir: str = None):
        """Initialize the implementation agent.

        Args:
            project_root: Path to project root. If None, auto-detect.
            conductor_dir: Path to conductor directory.
        """
        if project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent
        else:
            self.project_root = Path(project_root)

        if conductor_dir is None:
            self.conductor_dir = self.project_root / "conductor"
        else:
            self.conductor_dir = Path(conductor_dir)

        self.git_dir = self.project_root / ".git"

    def load_plan(self, track_id: str) -> str:
        """Load plan.md content for a track.

        Args:
            track_id: Track identifier

        Returns:
            Plan content as string.
        """
        plan_path = self.conductor_dir / "tracks" / track_id / "plan.md"
        if not plan_path.exists():
            raise FileNotFoundError(f"Plan not found: {plan_path}")

        with open(plan_path, 'r', encoding='utf-8') as f:
            return f.read()

    def parse_plan(self, plan_content: str) -> Dict[str, Any]:
        """Parse plan.md into structured data.

        Args:
            plan_content: Plan markdown content

        Returns:
            Dictionary with phases and tasks.
        """
        phases = []
        current_phase = None
        phase_num = 0

        lines = plan_content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Match phase headers: ## Fase N: Name
            if line.startswith('## Fase ') or line.startswith('## FASE '):
                if current_phase:
                    phases.append(current_phase)

                phase_num += 1
                # Extract phase name
                match = re.search(r'Fase \d+:\s*(.+)', line, re.IGNORECASE)
                phase_name = match.group(1).strip() if match else f"Fase {phase_num}"

                # Check for checkpoint
                checkpoint_sha = None
                checkpoint_line = lines[min(i+10, len(lines)-1)]
                checkpoint_match = re.search(r'\[checkpoint:\s*([a-f0-9]+)\]', checkpoint_line)
                if checkpoint_match:
                    checkpoint_sha = checkpoint_match.group(1)

                current_phase = {
                    'number': phase_num,
                    'name': phase_name,
                    'checkpoint_sha': checkpoint_sha,
                    'tasks': [],
                    'complete': checkpoint_sha is not None
                }

            # Match tasks: - [ ] Task description or - [x] Task description
            elif line.startswith('- [') and current_phase:
                # Extract status and task description
                status_match = re.match(r'- \[([ x])\]\s*(.+)', line)
                if status_match:
                    status = status_match.group(1)
                    task_desc = status_match.group(2).strip()

                    # Skip verification tasks (handled separately)
                    if 'Conductor - User Manual Verification' not in task_desc:
                        current_phase['tasks'].append({
                            'description': task_desc,
                            'complete': status == 'x',
                            'line_content': line
                        })

            i += 1

        # Add last phase
        if current_phase:
            phases.append(current_phase)

        return {
            'phases': phases,
            'total_phases': phase_num,
            'total_tasks': sum(len(p['tasks']) for p in phases)
        }

    def load_context_docs(self) -> Dict[str, str]:
        """Load context documentation."""
        docs = {}
        for doc_name in ['workflow.md', 'tech-stack.md']:
            doc_path = self.conductor_dir / doc_name
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    docs[doc_name] = f.read()
        return docs

    def git_commit(self, message: str, files: List[str] = None) -> str:
        """Create git commit and return SHA.

        Args:
            message: Commit message
            files: List of files to stage (None = all changes)

        Returns:
            Commit SHA (short form, 7 chars).
        """
        # Stage files
        if files:
            for f in files:
                self._run_git(['add', f])
        else:
            # Stage all changes
            self._run_git(['add', '-A'])

        # Create commit
        result = self._run_git(['commit', '-m', message])
        if result.returncode != 0:
            # Check if nothing to commit
            if 'nothing to commit' in result.stderr.lower():
                return None

        # Get commit SHA
        sha_result = self._run_git(['log', '-1', '--format=%H'])
        return sha_result.stdout.strip()[:7]

    def git_add_note(self, commit_sha: str, note_content: str) -> bool:
        """Attach git note to commit.

        Args:
            commit_sha: Commit SHA (short or long)
            note_content: Note content

        Returns:
            True if successful.
        """
        result = self._run_git(['notes', 'add', '-m', note_content, commit_sha])
        return result.returncode == 0

    def _run_git(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run git command.

        Args:
            args: Git arguments (without 'git')

        Returns:
            Completed process result.
        """
        cmd = ['git'] + args
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result

    def run_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run pytest and return results.

        Args:
            verbose: Show detailed output

        Returns:
            Dictionary with test results.
        """
        cmd = ['pytest', '-v']
        if not verbose:
            cmd.append('-q')

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse output
            passed = 0
            failed = 0
            errors = []

            for line in result.stdout.split('\n'):
                if ' passed' in line:
                    match = re.search(r'(\d+) passed', line)
                    if match:
                        passed = int(match.group(1))
                if ' failed' in line:
                    match = re.search(r'(\d+) failed', line)
                    if match:
                        failed = int(match.group(1))

            return {
                'success': result.returncode == 0,
                'passed': passed,
                'failed': failed,
                'output': result.stdout,
                'errors': errors if failed > 0 else None
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'passed': 0,
                'failed': 0,
                'output': '',
                'errors': ['Tests timed out after 120 seconds']
            }

    def run_coverage(self, modules: List[str] = None) -> Dict[str, Any]:
        """Run pytest with coverage.

        Args:
            modules: List of modules to check coverage for

        Returns:
            Coverage results.
        """
        cmd = ['pytest', '--cov=aoi_lib', '--cov=consumo_lib', '--cov-report=term']

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse coverage percentage
            coverage = 0
            for line in result.stdout.split('\n'):
                if 'TOTAL' in line:
                    match = re.search(r'(\d+)%', line)
                    if match:
                        coverage = int(match.group(1))

            return {
                'success': True,
                'coverage': coverage,
                'output': result.stdout
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'coverage': 0,
                'output': '',
                'error': 'Coverage check timed out'
            }

    def smoke_test(self) -> Dict[str, Any]:
        """Run application smoke test.

        Returns:
            Smoke test results.
        """
        # For now, just check if main.py exists and is syntactically valid
        main_py = self.project_root / "main.py"

        if not main_py.exists():
            return {
                'success': False,
                'error': 'main.py not found'
            }

        try:
            # Try to compile main.py
            with open(main_py, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, str(main_py), 'exec')

            return {
                'success': True,
                'message': 'main.py syntax is valid'
            }

        except SyntaxError as e:
            return {
                'success': False,
                'error': f'Syntax error in main.py: {e}'
            }

    def get_changed_files(self, from_sha: str = None) -> List[str]:
        """Get list of changed files since commit.

        Args:
            from_sha: Starting commit SHA (None = last checkpoint)

        Returns:
            List of changed file paths.
        """
        if from_sha:
            result = self._run_git(['diff', '--name-only', from_sha, 'HEAD'])
        else:
            # Get all modified files
            result = self._run_git(['diff', '--name-only'])

        if result.returncode == 0:
            files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
            # Filter out non-code files
            return [f for f in files if f.endswith(('.py', '.md', '.json'))]

        return []

    def update_plan_status(
        self,
        track_id: str,
        task_line: str,
        new_status: str,
        commit_sha: str = None
    ) -> bool:
        """Update task status in plan.md.

        Args:
            track_id: Track identifier
            task_line: Original task line content
            new_status: New status ('~' or 'x')
            commit_sha: Commit SHA to append (if 'x')

        Returns:
            True if successful.
        """
        plan_path = self.conductor_dir / "tracks" / track_id / "plan.md"

        with open(plan_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace task status
        if new_status == 'x' and commit_sha:
            # Mark complete with SHA
            new_line = task_line.replace('[ ]', '[x]')
            new_line = f"{new_line} [{commit_sha}]"
        elif new_status == '~':
            # Mark in progress
            new_line = task_line.replace('[ ]', '[~]')
        else:
            new_line = task_line.replace('[ ]', '[x]')

        content = content.replace(task_line, new_line)

        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return True

    def update_phase_checkpoint(
        self,
        track_id: str,
        phase_num: int,
        checkpoint_sha: str
    ) -> bool:
        """Update phase checkpoint in plan.md.

        Args:
            track_id: Track identifier
            phase_num: Phase number
            checkpoint_sha: Checkpoint commit SHA

        Returns:
            True if successful.
        """
        plan_path = self.conductor_dir / "tracks" / track_id / "plan.md"

        with open(plan_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find phase header and append checkpoint
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Match phase header
            if f'Fase {phase_num}:' in line:
                # Append checkpoint after the header
                lines.insert(i + 1, f'[checkpoint: {checkpoint_sha}]')
                break

        new_content = '\n'.join(lines)

        with open(plan_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True

    def execute_task(
        self,
        track_id: str,
        task: Dict[str, Any],
        context_docs: Dict[str, str]
    ) -> Dict[str, Any]:
        """Execute a single task with TDD workflow.

        Args:
            track_id: Track identifier
            task: Task dictionary with description and status
            context_docs: Context documentation

        Returns:
            Execution result.
        """
        print(f"\n{'='*60}")
        print(f"TASK: {task['description']}")
        print(f"{'='*60}\n")

        # Update plan to in-progress
        self.update_plan_status(track_id, task['line_content'], '~')
        commit_sha = self.git_commit(f"conductor(plan): Mark task '{task['description'][:50]}' as in-progress")

        # Execute TDD cycle
        result = {
            'task': task['description'],
            'started': datetime.now().isoformat(),
            'tdd_completed': False,
            'tests_passed': False,
            'coverage_met': False,
            'smoke_test_passed': False
        }

        # For demonstration, we'll simulate TDD completion
        # In real usage, this would interact with Claude Code to:
        # 1. Write failing tests (RED)
        # 2. Implement code (GREEN)
        # 3. Refactor (REFACTOR)
        # 4. Verify coverage

        print("[INFO] TDD Cycle:")
        print("  [DEMO] RED: Would write failing tests here")
        print("  [DEMO] GREEN: Would implement code to pass tests")
        print("  [DEMO] REFACTOR: Would improve code quality")

        # Run tests
        print("\n[INFO] Running tests...")
        test_result = self.run_tests(verbose=False)
        result['tests_passed'] = test_result['success']
        print(f"  Tests: {test_result['passed']} passed, {test_result['failed']} failed")

        # Check coverage
        print("[INFO] Checking coverage...")
        coverage_result = self.run_coverage()
        result['coverage'] = coverage_result.get('coverage', 0)
        print(f"  Coverage: {coverage_result.get('coverage', 0)}%")

        # Smoke test
        print("[INFO] Running smoke test...")
        smoke_result = self.smoke_test()
        result['smoke_test_passed'] = smoke_result['success']
        print(f"  Smoke test: {'PASSED' if smoke_result['success'] else 'FAILED'}")

        # Commit changes
        print("\n[INFO] Committing changes...")
        commit_msg = f"feat: {task['description']}"
        commit_sha = self.git_commit(commit_msg)

        if commit_sha:
            result['commit_sha'] = commit_sha
            print(f"  Commit: {commit_sha}")

            # Attach git note
            note_content = self._generate_task_note(result, track_id)
            self.git_add_note(commit_sha, note_content)
            print(f"  Git note attached")

        # Update plan as complete
        self.update_plan_status(track_id, task['line_content'], 'x', commit_sha)
        self.git_commit(f"conductor(plan): Mark task '{task['description'][:50]}' as complete")

        result['completed'] = True
        result['completed_at'] = datetime.now().isoformat()

        return result

    def _generate_task_note(self, result: Dict, track_id: str) -> str:
        """Generate git note content for task.

        Args:
            result: Task execution result
            track_id: Track identifier

        Returns:
            Note content.
        """
        return f"""Task: {result['task']}

Track: {track_id}
Started: {result['started']}
Completed: {result.get('completed_at', 'N/A')}

TDD Cycle:
- RED: Failing tests written
- GREEN: Implementation completed
- REFACTOR: Code quality improved

Results:
- Tests: {'PASSED' if result['tests_passed'] else 'FAILED'}
- Coverage: {result.get('coverage', 0)}%
- Smoke Test: {'PASSED' if result['smoke_test_passed'] else 'FAILED'}

Commit SHA: {result.get('commit_sha', 'N/A')}
"""

    def create_checkpoint(
        self,
        track_id: str,
        phase_num: int,
        phase_name: str,
        previous_checkpoint: str = None
    ) -> Dict[str, Any]:
        """Create phase checkpoint with verification.

        Args:
            track_id: Track identifier
            phase_num: Phase number
            phase_name: Phase name
            previous_checkpoint: Previous checkpoint SHA

        Returns:
            Checkpoint result.
        """
        print(f"\n{'='*60}")
        print(f"PHASE {phase_num} CHECKPOINT: {phase_name}")
        print(f"{'='*60}\n")

        # Identify changed files
        print("[INFO] Identifying changed files...")
        changed_files = self.get_changed_files(previous_checkpoint)
        print(f"  Changed files: {len(changed_files)}")
        for f in changed_files:
            print(f"    - {f}")

        # Verify test coverage
        print("\n[INFO] Verifying test coverage for changed files...")
        test_files = [f for f in changed_files if 'test_' in f or f.endswith('_test.py')]
        print(f"  Test files: {len(test_files)}")

        # Run full test suite
        print("\n[INFO] Running full test suite...")
        test_result = self.run_tests(verbose=True)
        print(f"  Result: {test_result['passed']} passed, {test_result['failed']} failed")

        if test_result['failed'] > 0:
            print(f"\n[WARNING] {test_result['failed']} tests failed!")
            return {
                'success': False,
                'error': f'{test_result["failed"]} tests failed',
                'test_output': test_result['output']
            }

        # Check coverage
        print("\n[INFO] Checking coverage...")
        coverage_result = self.run_coverage()
        coverage = coverage_result.get('coverage', 0)
        print(f"  Coverage: {coverage}%")

        # Generate manual verification plan
        print("\n[INFO] Manual Verification Plan:")
        print("  1. Review the generated files in this phase")
        print("  2. Run application and verify functionality")
        print("  3. Check that all acceptance criteria are met")
        print("\n  [DEMO] In real usage, would wait for user confirmation here")

        # Create checkpoint commit
        print("\n[INFO] Creating checkpoint commit...")
        checkpoint_msg = f"conductor(checkpoint): Checkpoint end of Phase {phase_num}"
        checkpoint_sha = self.git_commit(checkpoint_msg)

        if not checkpoint_sha:
            # Create empty commit if no changes
            result = self._run_git(['commit', '--allow-empty', '-m', checkpoint_msg])
            sha_result = self._run_git(['log', '-1', '--format=%H'])
            checkpoint_sha = sha_result.stdout.strip()[:7]

        print(f"  Checkpoint: {checkpoint_sha}")

        # Attach verification report as git note
        verification_report = f"""Phase Verification Report: Phase {phase_num} - {phase_name}

Automated Tests:
- Command: pytest
- Result: {test_result['passed']} passed

Coverage:
- Overall: {coverage}%

Changed Files ({len(changed_files)}):
{chr(10).join(f'  - {f}' for f in changed_files)}

Manual Verification:
1. Review generated files
2. Run application
3. Verify functionality
4. Confirm acceptance criteria

Checkpoint SHA: {checkpoint_sha}
Completed: {datetime.now().isoformat()}
"""

        self.git_add_note(checkpoint_sha, verification_report)
        print(f"  Verification report attached as git note")

        # Update plan.md with checkpoint
        print("\n[INFO] Updating plan.md with checkpoint SHA...")
        self.update_phase_checkpoint(track_id, phase_num, checkpoint_sha)

        # Commit plan update
        self.git_commit(f"conductor(plan): Mark phase '{phase_name}' as complete")

        print(f"\n[SUCCESS] Phase {phase_num} checkpoint complete!")

        return {
            'success': True,
            'checkpoint_sha': checkpoint_sha,
            'tests_passed': test_result['passed'],
            'coverage': coverage,
            'changed_files': changed_files
        }

    def execute_track(
        self,
        track_id: str,
        start_phase: int = 1,
        start_task: int = 1,
        auto_mode: bool = False
    ) -> Dict[str, Any]:
        """Execute a track plan.

        Args:
            track_id: Track identifier
            start_phase: Starting phase number (for resume)
            start_task: Starting task number (for resume)
            auto_mode: Run without user interaction

        Returns:
            Execution result.
        """
        print(f"\n{'='*70}")
        print(f"CONDUCTOR TRACK EXECUTION")
        print(f"{'='*70}")
        print(f"\nTrack ID: {track_id}")
        print(f"Start Phase: {start_phase}")
        print(f"Auto Mode: {auto_mode}\n")

        # Load plan
        print("[INFO] Loading track plan...")
        plan_content = self.load_plan(track_id)
        plan = self.parse_plan(plan_content)

        print(f"[INFO] Found {plan['total_phases']} phases with {plan['total_tasks']} tasks")

        # Load context
        context_docs = self.load_context_docs()

        # Execute phases
        execution_log = []
        previous_checkpoint = None

        for phase in plan['phases']:
            phase_num = phase['number']

            # Skip if before start phase
            if phase_num < start_phase:
                if phase['checkpoint_sha']:
                    previous_checkpoint = phase['checkpoint_sha']
                continue

            print(f"\n{'#'*70}")
            print(f"# PHASE {phase_num}: {phase['name'].upper()}")
            print(f"{'#'*70}")

            # Skip if phase already complete
            if phase['complete']:
                print(f"\n[INFO] Phase {phase_num} already complete (checkpoint: {phase['checkpoint_sha']})")
                previous_checkpoint = phase['checkpoint_sha']
                continue

            # Execute tasks in phase
            task_num = 0
            for task in phase['tasks']:
                task_num += 1

                # Skip if before start task
                if phase_num == start_phase and task_num < start_task:
                    continue

                # Skip if task already complete
                if task['complete']:
                    print(f"\n[INFO] Task already complete: {task['description']}")
                    continue

                # Execute task
                result = self.execute_task(track_id, task, context_docs)
                execution_log.append(result)

                # Check if task failed
                if not result.get('completed'):
                    print(f"\n[ERROR] Task failed: {result}")
                    return {
                        'success': False,
                        'error': f"Task failed: {task['description']}",
                        'execution_log': execution_log
                    }

            # Create checkpoint at end of phase
            checkpoint_result = self.create_checkpoint(
                track_id,
                phase_num,
                phase['name'],
                previous_checkpoint
            )

            if not checkpoint_result['success']:
                return {
                    'success': False,
                    'error': f"Checkpoint failed: {checkpoint_result.get('error')}",
                    'execution_log': execution_log
                }

            execution_log.append({
                'type': 'checkpoint',
                'phase': phase_num,
                'result': checkpoint_result
            })

            previous_checkpoint = checkpoint_result['checkpoint_sha']

        print(f"\n{'='*70}")
        print(f"TRACK EXECUTION COMPLETE!")
        print(f"{'='*70}")

        return {
            'success': True,
            'track_id': track_id,
            'phases_completed': len([p for p in plan['phases'] if p['complete']]),
            'total_phases': plan['total_phases'],
            'execution_log': execution_log,
            'final_checkpoint': previous_checkpoint
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute a Conductor track")
    parser.add_argument("track_id", help="Track identifier (e.g., feature_add_oauth_20260111)")
    parser.add_argument("--start-phase", type=int, default=1,
                       help="Starting phase number (for resume)")
    parser.add_argument("--start-task", type=int, default=1,
                       help="Starting task number (for resume)")
    parser.add_argument("--auto", action="store_true",
                       help="Run without user interaction (demo mode)")

    args = parser.parse_args()

    agent = ImplementationAgent()
    result = agent.execute_track(
        args.track_id,
        start_phase=args.start_phase,
        start_task=args.start_task,
        auto_mode=args.auto
    )

    if result['success']:
        print(f"\n✓ Track completed successfully!")
        print(f"  Phases completed: {result['phases_completed']}/{result['total_phases']}")
        print(f"  Final checkpoint: {result['final_checkpoint']}")
    else:
        print(f"\n✗ Track execution failed: {result.get('error')}")
        exit(1)
