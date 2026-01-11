# Conductor Commit - Commit Changes with Git Notes

**Triggered by:** `/conductor-commit` or `/conductor-commit [message]`

## Purpose

Commit modified files after completing a task or phase, with automatic git notes attachment for detailed audit trail.

## Workflow

### Step 1: Detect Modified Files

```bash
git status --short
```

Parse output to identify:
- **Modified files** (M)
- **Added files** (A)
- **Deleted files** (D)
- **Renamed files** (R)

### Step 2: Generate Commit Message (if auto_detect=true)

**Format:** `<type>(<scope>): <description>`

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `refactor` - Code change that neither fixes a bug nor adds a feature
- `test` - Adding or updating tests
- `docs` - Documentation only
- `chore` - Maintenance tasks

**Scope:**
- Name of the module/component being worked on
- Example: `recipe_manager`, `plc_controller`, `ui`

**Description:**
- Succinct summary of changes (max 72 chars)
- Use imperative mood ("add" not "added" or "adds")
- Example: "Add validation for empty recipe names"

### Step 3: Stage Modified Files

```bash
git add <files>
```

Stage all relevant files based on git status output.

### Step 4: Create Commit

```bash
git commit -m "<commit_message>"
```

### Step 5: Get Commit SHA

```bash
git log -1 --format="%H"
```

Get the full commit SHA for git notes attachment.

### Step 6: Generate Git Note Content

**Read author info from:** `conductor/setup_state.json`

```json
{
  "commit_author_name": "Ronald Buzaglo",
  "commit_author_email": "",
  "co_author_text": "Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
}
```

**Structure:**

```
Task Completion Summary
=======================

Author: Ronald Buzaglo
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

Type: <task_type>
Scope: <module_name>

Changes Made:
- <change_1>
- <change_2>
- <change_3>

Files Modified:
- <file_1>
- <file_2>
- <file_3>

Test Results:
- [ ] Tests pass
- [ ] Coverage meets requirements
- [ ] Smoke test passed

Documentation:
- [ ] Code documented
- [ ] plan.md updated (if applicable)

Notes:
<additional_context>
```

### Step 7: Attach Git Note

```bash
git notes add -m "<note_content>" <commit_sha>
```

## Examples

### Example 1: Auto-detect mode

```bash
/conductor-commit
```

**What it does:**
1. Runs `git status` to detect changes
2. Generates commit message from modified files
3. Prompts user for confirmation
4. Creates commit
5. Generates detailed git note
6. Attaches note to commit

**Example output:**

```
Detected changes:
M aoi_lib/recipe_manager.py
M tests/unit/test_recipe_manager_enhanced.py

Generated commit message:
test(recipe_manager): Add validation for empty recipe names

Add detailed note? (Y/n): Y

Created commit: abc1234
Attached git note: abc1234
```

### Example 2: Custom message

```bash
/conductor-commit "fix(plc): Handle connection timeout gracefully"
```

Skips auto-detection, uses provided message.

### Example 3: With custom note

```bash
/conductor-commit message="refactor(ui): Clean up dialog validation" note="Removed validation logic from RecipeDialog and delegated to RecipeManager. All 18 tests passing."
```

## Best Practices

### Commit Message Format

✅ **Good:**
```
feat(recipe_manager): Add recipe duplication feature
fix(plc): Handle connection timeout gracefully
test(tension): Add functional integration tests
```

❌ **Bad:**
```
updated stuff
fix bug
changes
```

### Git Note Content

✅ **Good notes include:**
- What was changed (succinct bullet points)
- Why it was changed (context)
- Test results
- Any important decisions made

❌ **Bad notes:**
- Too verbose (entire conversation transcript)
- Too vague ("did some work")
- Missing test results

### When to Use

**Use `/conductor-commit` after:**
- Completing a task from plan.md
- Finishing a phase checkpoint
- Significant code changes
- Test additions/updates

**Don't use after:**
- Every small edit (use for meaningful units of work)
- Typos or trivial formatting
- Experimental code (not ready to commit)

## Integration with Workflow

This command integrates with `conductor/workflow.md`:

**Standard Task Workflow** (steps 6-8):
```
6. Commit Code Changes (git add + git commit)
7. Attach Task Summary with Git Notes (git notes add)
8. Get and Record Task Commit SHA (update plan.md)
```

This command automates steps 6-7 in one operation.

## Error Handling

**If no changes detected:**
```
No modified files detected. Nothing to commit.
```

**If commit fails:**
```
Commit failed: <error_message>
Please resolve issues and try again.
```

**If git notes fails:**
```
Warning: Could not attach git note
Commit created successfully: <sha>
You can manually add note later with: git notes add -m "<content>" <sha>
```

## Related Commands

- `/conductor-status` - Check overall track progress
- `/conductor-implement` - Execute next task from plan.md
- `/conductor-revert` - Revert last commit if needed
