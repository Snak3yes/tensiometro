# Conductor Status Command

You are executing the `/conductor-status` command to show the status of all Conductor tracks.

## Purpose
Display a formatted table showing all tracks with their progress, status, and current phase/task.

## Execution Steps

1. **Import and run status command:**
   ```python
   from claude_conductor.support_commands import ConductorCommands
   cmd = ConductorCommands()
   result = cmd.status(verbose=True)
   ```

2. **Display formatted output:**
   - Summary (total tracks, active, completed, archived)
   - Each track with:
     - Track ID
     - Status (pending, in-progress, complete, archived)
     - Type (feature, bugfix, refactor, experiment)
     - Priority
     - Creation date
     - Progress (phase X/Y, tasks in plan)
   - Overall progress percentage

3. **Use safe_print for output** to handle Windows encoding issues

## Output Format

```
======================================================================
CONDUCTOR TRACK STATUS
======================================================================

Summary:
  Total Tracks: 2
  Active: 1
  Completed: 0
  Archived: 0

1.  feature_example_20260111
   Status: in-progress
   Type: Feature
   Priority: High
   Created: 2026-01-11
   Progress: Phase 1/3 | Tasks: 5/30 complete

======================================================================
Overall Progress: 33.3%
======================================================================
```

## Error Handling
- If no tracks found: Show message "No tracks found. Use /conductor-new to create one."
- If tracks.md missing: Show error and suggest running /conductor-setup
- Always use safe_print for Unicode characters
