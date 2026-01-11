# Conductor Revert Command

You are executing the `/conductor-revert` command to revert a track, phase, or task.

## Purpose
Revert a track to a previous state using git reset, allowing rollback of changes made during implementation.

## Execution Steps

1. **Import and validate:**
   ```python
   from claude_conductor.support_commands import ConductorCommands
   cmd = ConductorCommands()
   ```

2. **Find checkpoint commit:**
   - Read plan.md to find checkpoint commits
   - Each phase ends with a checkpoint commit
   - Find the commit SHA for the target phase

3. **Verify git status:**
   - Check if there are uncommitted changes
   - If yes: Warn user and suggest commit or stash
   - Show what will be reverted

4. **Ask for confirmation (unless confirm=true):**
   - Show track ID
   - Show target phase (if specified)
   - Show commits that will be removed
   - Ask: "Do you want to proceed? (yes/no)"

5. **Perform git reset:**
   - Use `git reset --hard <checkpoint-sha>`
   - This removes commits after the checkpoint
   - Working directory will match checkpoint state

6. **Update plan.md:**
   - Mark tasks as incomplete
   - Remove completion SHAs
   - Update current phase marker

7. **Display results:**
   - Show what was reverted
   - Show current state
   - Suggest next steps

## Revert Scenarios

### Scenario 1: Revert Entire Track
```bash
/conductor-revert track=feature_x
```
- Reverts all commits for this track
- Returns track to "new" state
- All tasks marked as incomplete

### Scenario 2: Revert to Specific Phase
```bash
/conductor-revert track=feature_x phase=2
```
- Keeps phases 1-2
- Removes phases 3+
- Tasks in phases 1-2 remain complete

### Scenario 3: Auto-confirm (Dangerous!)
```bash
/conductor-revert track=feature_x --confirm
```
- Skips confirmation prompt
- Use only in automation/scripts
- **Warning:** Cannot be easily undone

## Output Format

```
⚠️ Reverting track: feature_implement_user_auth_20260111
Target: Phase 2 (checkpoint: a1b2c3d)

Commits that will be removed:
  - d4e5f6g Add login UI
  - h7i8j9k Implement user session
  - l0m1n2o Add password reset

Working directory is clean.

❓ Do you want to proceed? (yes/no): yes

✅ Revert complete!
Track reset to checkpoint: a1b2c3d
Current state: Phase 2 complete
Next: Resume from Phase 3, Task 1
```

## Error Handling

- If uncommitted changes:
  - Warn user
  - Suggest: `git stash` or `git commit`
  - Ask if they want to continue anyway

- If checkpoint not found:
  - Show available checkpoints
  - Ask user to specify different phase

- If git reset fails:
  - Show error message
  - Suggest: `git status` to check state
  - May need manual resolution

## Safety Features

1. **Always show what will be reverted** before executing
2. **Ask for confirmation** by default
3. **Check working directory status** before reset
4. **Display checkpoint SHAs** for verification
5. **Keep git refs** for recovery if needed

## Recovery After Revert

If user needs to undo the revert:

```bash
# Find the reflog entry
git reflog

# Reset to the state before revert
git reset --hard <commit-sha>
```

## Important Notes

- **Git reset --hard is destructive** - commits after checkpoint are lost
- **Checkpoint commits are tagged** in plan.md for easy reference
- **Always verify before proceeding**
- **Consider creating backup branch** before revert
- **Display in Portuguese** if user communicates in Portuguese
- **Use safe_print** for all output
