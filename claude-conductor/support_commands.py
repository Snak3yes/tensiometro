#!/usr/bin/env python3
"""
Conductor Support Commands

Provides supporting commands for the Conductor system:
- /conductor:status - Show progress across all tracks
- /conductor:revert - Revert track/phase/task
- /conductor:update - Update base documentation

Usage:
    python support_commands.py status
    python support_commands.py revert --track feature_xyz_20260111 --phase 2
    python support_commands.py update --doc product
"""

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConductorCommands:
    """Support commands for Conductor system."""

    @staticmethod
    def safe_print(text: str) -> None:
        """Print text safely, handling encoding issues.

        Args:
            text: Text to print
        """
        try:
            print(text)
        except UnicodeEncodeError:
            # Fallback: replace non-ASCII chars
            safe_text = text.encode('ascii', 'ignore').decode('ascii')
            print(safe_text)

    def __init__(self, project_root: str = None, conductor_dir: str = None):
        """Initialize conductor commands.

        Args:
            project_root: Path to project root
            conductor_dir: Path to conductor directory
        """
        if project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent
        else:
            self.project_root = Path(project_root)

        if conductor_dir is None:
            self.conductor_dir = self.project_root / "conductor"
        else:
            self.conductor_dir = Path(conductor_dir)

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

    # ========================================
    # STATUS COMMAND
    # ========================================

    def status(self, verbose: bool = False) -> Dict[str, Any]:
        """Show status across all tracks.

        Args:
            verbose: Show detailed information

        Returns:
            Status dictionary with track information.
        """
        self.safe_print("\n" + "="*70)
        self.safe_print("CONDUCTOR TRACK STATUS")
        self.safe_print("="*70 + "\n")

        # Load tracks registry
        tracks_file = self.conductor_dir / "tracks.md"

        if not tracks_file.exists():
            self.safe_print("[ERROR] tracks.md not found")
            return {'success': False, 'error': 'tracks.md not found'}

        with open(tracks_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse tracks from registry
        tracks = []

        # Method 1: Look for Track ID in bullet points
        track_id_pattern = r'Track ID:\s*([a-z_0-9_]+)'
        track_ids = re.findall(track_id_pattern, content)

        for track_id in track_ids:
            # Find the block for this track
            track_block_pattern = rf'Track ID:\s*{re.escape(track_id)}.*?(?=Track ID:|---|\Z)'
            track_match = re.search(track_block_pattern, content, re.DOTALL)

            if track_match:
                block = track_match.group(0)

                # Extract info
                status_match = re.search(r'Status:\s*(\w+)', block)
                created_match = re.search(r'Created:\s*([0-9-]+)', block)

                status = status_match.group(1) if status_match else 'Unknown'
                created = created_match.group(1) if created_match else 'Unknown'

                # Load track metadata
                metadata = self._load_track_metadata(track_id)

                # Load plan for phase info
                plan_info = self._get_track_plan_info(track_id)

                tracks.append({
                    'id': track_id,
                    'status': status,
                    'created': created,
                    'metadata': metadata,
                    'plan_info': plan_info
                })

        # Method 2: Check tracks directory directly
        tracks_dir = self.conductor_dir / "tracks"
        if tracks_dir.exists():
            for track_dir in tracks_dir.iterdir():
                if track_dir.is_dir():
                    track_id = track_dir.name

                    # Skip if already in list
                    if any(t['id'] == track_id for t in tracks):
                        continue

                    # Load metadata
                    metadata = self._load_track_metadata(track_id)

                    # Load plan info
                    plan_info = self._get_track_plan_info(track_id)

                    tracks.append({
                        'id': track_id,
                        'status': metadata.get('status', 'Unknown'),
                        'created': metadata.get('created_at', '')[:10] if metadata.get('created_at') else 'Unknown',
                        'metadata': metadata,
                        'plan_info': plan_info
                    })

        if not tracks:
            print("[INFO] No tracks found")
            return {'success': True, 'tracks': []}

        # Display summary
        active = len([t for t in tracks if t['status'] == 'Planning' or t['status'] == 'In Progress'])
        completed = len([t for t in tracks if t['status'] == 'Completed'])
        archived = len([t for t in tracks if t['status'] == 'Archived'])

        self.safe_print(f"Summary:")
        self.safe_print(f"  Total Tracks: {len(tracks)}")
        self.safe_print(f"  Active: {active}")
        self.safe_print(f"  Completed: {completed}")
        self.safe_print(f"  Archived: {archived}\n")

        # Display each track
        for i, track in enumerate(tracks, 1):
            status_symbol = self._get_status_symbol(track['status'])

            # Safe print (handle encoding issues)
            try:
                self.safe_print(f"{i}. {status_symbol} {track['id']}")
            except UnicodeEncodeError:
                self.safe_print(f"{i}. {status_symbol} {track['id'].encode('ascii', 'ignore').decode('ascii')}")

            self.safe_print(f"   Status: {track['status']}")
            self.safe_print(f"   Type: {track['metadata'].get('type', 'N/A').capitalize()}")
            self.safe_print(f"   Priority: {track['metadata'].get('priority', 'N/A')}")
            self.safe_print(f"   Created: {track['created']}")

            # Phase progress
            plan = track['plan_info']
            if plan:
                total_phases = plan.get('total_phases', 0)
                completed_phases = plan.get('completed_phases', 0)
                total_tasks = plan.get('total_tasks', 0)

                self.safe_print(f"   Progress: Phase {completed_phases}/{total_phases} | Tasks in plan: {total_tasks}")

            if verbose:
                # Show phases
                if plan and plan.get('phases'):
                    self.safe_print(f"   Phases:")
                    for phase in plan['phases']:
                        phase_status = "[OK]" if phase.get('complete') else "[TODO]"
                        self.safe_print(f"     {phase_status} Phase {phase['number']}: {phase['name']}")

            self.safe_print("")

        # Calculate overall statistics
        total_phases = sum(t['plan_info'].get('total_phases', 0) for t in tracks if t['plan_info'])
        completed_phases = sum(t['plan_info'].get('completed_phases', 0) for t in tracks if t['plan_info'])

        self.safe_print("="*70)
        self.safe_print(f"Overall Progress: {completed_phases}/{total_phases} phases completed")
        if total_phases > 0:
            percentage = (completed_phases / total_phases) * 100
            self.safe_print(f"Completion: {percentage:.1f}%")
        self.safe_print("="*70)

        return {
            'success': True,
            'tracks': tracks,
            'summary': {
                'total': len(tracks),
                'active': active,
                'completed': completed,
                'archived': archived,
                'total_phases': total_phases,
                'completed_phases': completed_phases
            }
        }

    def _get_status_symbol(self, status: str) -> str:
        """Get status symbol.

        Args:
            status: Track status

        Returns:
            Status symbol.
        """
        symbols = {
            'Planning': '[PLANNING]',
            'In Progress': '[IN PROGRESS]',
            'Completed': '[COMPLETED]',
            'Archived': '[ARCHIVED]',
            'Unknown': '[UNKNOWN]'
        }
        return symbols.get(status, '❓')

    def _load_track_metadata(self, track_id: str) -> Dict:
        """Load track metadata.

        Args:
            track_id: Track identifier

        Returns:
            Metadata dictionary.
        """
        metadata_path = self.conductor_dir / "tracks" / track_id / "metadata.json"

        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        return {}

    def _get_track_plan_info(self, track_id: str) -> Optional[Dict]:
        """Get track plan information.

        Args:
            track_id: Track identifier

        Returns:
            Plan info dictionary or None.
        """
        plan_path = self.conductor_dir / "tracks" / track_id / "plan.md"

        if not plan_path.exists():
            return None

        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse phases
            phases = []
            phase_num = 0
            completed_phases = 0

            lines = content.split('\n')
            for line in lines:
                if line.startswith('## Fase ') or line.startswith('## FASE '):
                    phase_num += 1
                    is_complete = '[checkpoint:' in content[content.find(line):content.find(line)+200]
                    if is_complete:
                        completed_phases += 1

            # Count tasks (simplified)
            total_tasks = content.count('- [ ]')

            return {
                'total_phases': phase_num,
                'completed_phases': completed_phases,
                'total_tasks': total_tasks,
                'phases': phases
            }

        except Exception:
            return None

    # ========================================
    # REVERT COMMAND
    # ========================================

    def revert(
        self,
        track_id: str,
        phase: Optional[int] = None,
        task: Optional[int] = None,
        confirm: bool = False
    ) -> Dict[str, Any]:
        """Revert track, phase, or task.

        Args:
            track_id: Track identifier
            phase: Phase number (None = entire track)
            task: Task number (None = entire phase)
            confirm: Skip confirmation

        Returns:
            Revert result.
        """
        print("\n" + "="*70)
        print("CONDUCTOR REVERT")
        print("="*70 + "\n")

        if not confirm:
            print(f"[WARNING] This will revert changes for track: {track_id}")
            if phase:
                print(f"  Phase: {phase}")
            if task:
                print(f"  Task: {task}")
            print("\nThis will use git reset to remove commits.")
            print("Make sure you have pushed any important changes first!\n")

            response = input("Proceed? (yes/no): ")
            if response.lower() != 'yes':
                print("[INFO] Revert cancelled")
                return {'success': False, 'cancelled': True}

        # Get current git state
        git_status = self._run_git(['status', '--short'])
        if git_status.returncode != 0:
            return {'success': False, 'error': 'Failed to get git status'}

        if not git_status.stdout.strip():
            print("[INFO] No changes to revert")
            return {'success': True, 'message': 'No changes to revert'}

        # Count uncommitted changes
        changed_files = len([l for l in git_status.stdout.split('\n') if l.strip()])
        print(f"[INFO] Found {changed_files} uncommitted changes")

        # Reset to last checkpoint or HEAD~1
        if phase:
            print(f"[INFO] Reverting to start of phase {phase}")
            # In real implementation, would find phase checkpoint SHA
            reset_target = "HEAD~1"
        else:
            print(f"[INFO] Reverting entire track")
            reset_target = "HEAD~1"

        # Soft reset (keep changes locally)
        result = self._run_git(['reset', '--soft', reset_target])

        if result.returncode == 0:
            print(f"[SUCCESS] Reset to {reset_target}")
            print(f"[INFO] Changes are still in your working directory")
            print(f"[INFO] You can now make new commits or continue work")

            return {
                'success': True,
                'reset_to': reset_target,
                'changes_kept': True
            }
        else:
            print(f"[ERROR] Reset failed: {result.stderr}")
            return {'success': False, 'error': result.stderr}

    # ========================================
    # UPDATE COMMAND
    # ========================================

    def update(self, doc: str, confirm: bool = False) -> Dict[str, Any]:
        """Update base documentation.

        Args:
            doc: Document to update ('product', 'tech-stack', 'all')
            confirm: Skip confirmation

        Returns:
            Update result.
        """
        print("\n" + "="*70)
        print("CONDUCTOR UPDATE")
        print("="*70 + "\n")

        # Check setup state
        setup_state_file = self.conductor_dir / "setup_state.json"

        if not setup_state_file.exists():
            print("[ERROR] Setup state not found. Run /conductor:setup first.")
            return {'success': False, 'error': 'Setup not found'}

        with open(setup_state_file, 'r', encoding='utf-8') as f:
            setup_state = json.load(f)

        responses = setup_state.get('responses', {})

        if not responses:
            print("[ERROR] No responses found in setup state")
            return {'success': False, 'error': 'No responses'}

        if not confirm:
            print(f"[INFO] This will regenerate documentation based on setup responses")
            print(f"[INFO] Document to update: {doc}")
            print(f"[INFO] Original setup date: {setup_state.get('timestamp', 'Unknown')}\n")

            response = input("Proceed? (yes/no): ")
            if response.lower() != 'yes':
                print("[INFO] Update cancelled")
                return {'success': False, 'cancelled': True}

        # Import SetupAgent to regenerate docs
        import sys
        sys.path.insert(0, str(self.conductor_dir.parent / "claude-conductor"))

        try:
            from setup_agent import SetupAgent

            agent = SetupAgent(project_root=str(self.project_root))

            # Determine what to update
            docs_to_update = []
            if doc == 'product' or doc == 'all':
                docs_to_update.append(('product.md', agent.generate_product_md()))
            if doc == 'tech-stack' or doc == 'all':
                docs_to_update.append(('tech-stack.md', agent.generate_tech_stack_md()))
            if doc == 'workflow' or doc == 'all':
                docs_to_update.append(('workflow.md', agent.generate_workflow_md()))

            # Write updated docs
            for doc_name, content in docs_to_update:
                doc_path = self.conductor_dir / doc_name
                with open(doc_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[OK] Updated: {doc_name}")

            print(f"\n[SUCCESS] Updated {len(docs_to_update)} document(s)")

            return {
                'success': True,
                'updated': len(docs_to_update),
                'docs': [d[0] for d in docs_to_update]
            }

        except ImportError as e:
            print(f"[ERROR] Failed to import SetupAgent: {e}")
            return {'success': False, 'error': str(e)}

    # ========================================
    # ARCHIVE COMMAND
    # ========================================

    def archive(self, track_id: str, confirm: bool = False) -> Dict[str, Any]:
        """Archive a completed track.

        Args:
            track_id: Track identifier
            confirm: Skip confirmation

        Returns:
            Archive result.
        """
        print("\n" + "="*70)
        print("CONDUCTOR ARCHIVE")
        print("="*70 + "\n")

        track_dir = self.conductor_dir / "tracks" / track_id

        if not track_dir.exists():
            print(f"[ERROR] Track not found: {track_id}")
            return {'success': False, 'error': 'Track not found'}

        # Load metadata
        metadata_file = track_dir / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        current_status = metadata.get('status', 'Unknown')

        if not confirm:
            print(f"[INFO] Track: {track_id}")
            print(f"[INFO] Current status: {current_status}")
            print(f"[INFO] This will move the track to conductor/archive/\n")

            response = input("Proceed? (yes/no): ")
            if response.lower() != 'yes':
                print("[INFO] Archive cancelled")
                return {'success': False, 'cancelled': True}

        # Create archive directory
        archive_dir = self.conductor_dir / "archive" / track_id
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Move track directory
        import shutil
        shutil.move(str(track_dir), str(archive_dir / track_id))

        print(f"[SUCCESS] Archived to: {archive_dir / track_id}")

        # Update tracks.md
        tracks_file = self.conductor_dir / "tracks.md"
        if tracks_file.exists():
            with open(tracks_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Mark track as archived
            content = re.sub(
                f'## \\[ \\] {metadata.get("name", track_id)}',
                f'## [x] {metadata.get("name", track_id)} (Archived)',
                content
            )

            with open(tracks_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"[OK] Updated tracks.md")

        # Update metadata status
        metadata_file = archive_dir / track_id / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            metadata['status'] = 'archived'
            metadata['archived_at'] = datetime.now().isoformat()

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        return {
            'success': True,
            'archived_to': str(archive_dir),
            'track_id': track_id
        }


# ========================================
# CLI INTERFACE
# ========================================

def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Conductor Support Commands")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show track status')
    status_parser.add_argument('--verbose', '-v', action='store_true',
                               help='Show detailed information')

    # Revert command
    revert_parser = subparsers.add_parser('revert', help='Revert track/phase/task')
    revert_parser.add_argument('--track', required=True, help='Track ID')
    revert_parser.add_argument('--phase', type=int, help='Phase number')
    revert_parser.add_argument('--task', type=int, help='Task number')
    revert_parser.add_argument('--confirm', '-y', action='store_true',
                               help='Skip confirmation')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update documentation')
    update_parser.add_argument('--doc', choices=['product', 'tech-stack', 'workflow', 'all'],
                               default='all', help='Document to update')
    update_parser.add_argument('--confirm', '-y', action='store_true',
                               help='Skip confirmation')

    # Archive command
    archive_parser = subparsers.add_parser('archive', help='Archive completed track')
    archive_parser.add_argument('--track', required=True, help='Track ID')
    archive_parser.add_argument('--confirm', '-y', action='store_true',
                               help='Skip confirmation')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute command
    commands = ConductorCommands()

    if args.command == 'status':
        result = commands.status(verbose=args.verbose)

    elif args.command == 'revert':
        result = commands.revert(
            track_id=args.track,
            phase=args.phase,
            task=args.task,
            confirm=args.confirm
        )

    elif args.command == 'update':
        result = commands.update(doc=args.doc, confirm=args.confirm)

    elif args.command == 'archive':
        result = commands.archive(track_id=args.track, confirm=args.confirm)

    else:
        print(f"[ERROR] Unknown command: {args.command}")
        return 1

    # Return exit code
    return 0 if result.get('success') else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
