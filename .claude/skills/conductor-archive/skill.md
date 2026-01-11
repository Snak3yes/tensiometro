# Conductor Archive Command

You are executing the `/conductor-archive` command to archive a completed track.

## Purpose
Archive a completed track to prevent cluttering the active track list while preserving all history and documentation.

## Execution Steps

1. **Import and validate:**
   ```python
   from claude_conductor.support_commands import ConductorCommands
   cmd = ConductorCommands()
   ```

2. **Verify track exists:**
   - Read `conductor/tracks.md`
   - Find track by ID
   - If not found: Error with message

3. **Check track status:**
   - Read track's `plan.md`
   - Verify all phases are complete
   - If not complete: Warn user that track is still active
   - Ask if they still want to archive

4. **Ask for confirmation (unless confirm=true):**
   - Show track ID
   - Show track status
   - Show where it will be moved
   - Ask: "Archive this track? (yes/no)"

5. **Perform archive:**
   - Create `conductor/archive/` directory if doesn't exist
   - Move track directory: `conductor/tracks/{track_id}/` → `conductor/archive/{track_id}/`
   - Update `conductor/tracks.md`:
     - Change status from "complete" to "archived"
     - Move entry to "Archived Tracks" section
   - Create archive summary in track directory

6. **Display results:**
   - Show what was archived
   - Show new location
   - Show updated status

## Archive Location

**Before:**
```
conductor/
└── tracks/
    └── {track_id}/
        ├── spec.md
        ├── plan.md
        └── metadata.json
```

**After:**
```
conductor/
├── tracks/
│   (track removed from here)
└── archive/
    └── {track_id}/
        ├── spec.md
        ├── plan.md
        ├── metadata.json
        └── archive_summary.md
```

## Archive Summary

Create `archive_summary.md` in archived track:

```markdown
# Archive Summary

**Track ID:** {track_id}
**Type:** {feature|bugfix|refactor|experiment}
**Archived:** {date}

## Completion Details
- **Status:** Complete
- **Phases:** {num} phases completed
- **Tasks:** {completed}/{total} tasks completed
- **Duration:** {start_date} to {end_date}

## Key Commits
- Initial: {commit_sha}
- Checkpoint 1: {commit_sha}
- Checkpoint 2: {commit_sha}
- Final: {commit_sha}

## Deliverables
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Documentation complete
- [x] Code reviewed

## Notes
{additional_notes}
```

## Output Format

```
📦 Archiving track: feature_implement_user_auth_20260111

Status: Complete
Duration: 2026-01-11 to 2026-01-15
Phases: 3/3 complete
Tasks: 30/30 complete

Archive location:
  conductor/archive/feature_implement_user_auth_20260111/

❓ Archive this track? (yes/no): yes

✅ Track archived successfully!

Moved:
  conductor/tracks/feature_implement_user_auth_20260111/
  → conductor/archive/feature_implement_user_auth_20260111/

Updated:
  conductor/tracks.md (status: complete → archived)
```

## Parameters

### track (required)
Track identifier to archive:
- Example: `feature_implement_operator_workflow_20260111`

### confirm (default: false)
Skip confirmation prompt:
- `true` - Archive without asking
- `false` - Ask before archiving (safer)

## Unarchiving

To unarchive a track (restore to active):

```bash
# Move back to tracks/
mv conductor/archive/{track_id} conductor/tracks/{track_id}

# Update tracks.md
# Change status from "archived" to "complete"
```

Or use a future `/conductor-unarchive` command (if implemented).

## Use Cases

### Use Case 1: Archive Completed Feature
```bash
# Feature is done and deployed
/conductor-archive track=feature_implement_user_auth_20260111
```

### Use Case 2: Archive Abandoned Experiment
```bash
# Experiment didn't work out
/conductor-archive track=experiment_new_approach_20260110
```

### Use Case 3: Batch Archive (Script)
```bash
# Archive all complete tracks
for track in $(conductor list --status=complete); do
  /conductor-archive track=$track --confirm
done
```

## Error Handling

- If track not found:
  - Error: "Track not found: {track_id}"
  - Suggest: Use `/conductor-status` to list tracks

- If track still active:
  - Warning: "Track is not complete yet"
  - Show: Current progress (phase X/Y)
  - Ask: "Archive anyway? (yes/no)"

- If archive directory creation fails:
  - Error: "Cannot create archive directory"
  - Check: Permissions

- If move fails:
  - Error: "Cannot move track directory"
  - Check: File locks, permissions

- If tracks.md update fails:
  - Error: "Cannot update tracks.md"
  - Track is moved but registry not updated
  - Manual update required

## Archiving Best Practices

1. **Only archive complete tracks**
   - All phases done
   - All acceptance criteria met
   - Tests passing

2. **Verify before archiving**
   - Review final commit
   - Check documentation
   - Confirm deliverables

3. **Keep archive organized**
   - Use consistent naming
   - Maintain directory structure
   - Include archive summary

4. **Don't delete active work**
   - If still working: Don't archive yet
   - If on hold: Keep in active, mark as "on-hold"

## Important Notes

- **Archived tracks are read-only** - No further implementation
- **All history preserved** - Commits, notes, documents
- **Can be unarchived** if needed (manual process)
- **Ask before archiving** unless confirm=true
- **Display in Portuguese** if user communicates in Portuguese
- **Use safe_print** for all output
