# Conductor Update Command

You are executing the `/conductor-update` command to update base documentation.

## Purpose
Update Conductor base documentation files (product.md, tech-stack.md, workflow.md) from saved setup responses.

## Execution Steps

1. **Import and validate:**
   ```python
   from claude_conductor.support_commands import ConductorCommands
   cmd = ConductorCommands()
   ```

2. **Load setup responses:**
   - Read `conductor/setup_state.json`
   - Verify responses exist
   - If missing: Warn that setup must be run first

3. **Determine which docs to update:**
   - If `doc=product`: Update only product.md
   - If `doc=tech-stack`: Update only tech-stack.md
   - If `doc=workflow`: Update only workflow.md
   - If `doc=all`: Update all three

4. **For each document to update:**
   - Load template from `claude-conductor/templates/`
   - Fill placeholders with responses
   - Write updated file to `conductor/`
   - Show what was updated

5. **Ask for confirmation (unless confirm=true):**
   - Show which files will be updated
   - Show what changed
   - Ask: "Update these files? (yes/no)"

6. **Perform update:**
   - Backup existing files (add .bak extension)
   - Write new content
   - Show success message

## Document Templates

### product.md
Contains:
- Product vision and goals
- User personas
- Key features
- Success metrics

Placeholders filled from:
- `setup_responses.json` -> "product_vision" section

### tech-stack.md
Contains:
- Programming languages
- Frameworks and libraries
- Database
- Testing tools
- DevOps tools

Placeholders filled from:
- `setup_responses.json` -> "tech_stack" section

### workflow.md
Contains:
- TDD methodology
- Code review process
- Git workflow
- Testing standards
- Coverage requirements

Placeholders filled from:
- `setup_responses.json` -> "workflow_preferences" section

## Output Format

```
📝 Updating Conductor documentation

Files to update:
  ✓ conductor/product.md
  ✓ conductor/tech-stack.md
  ✓ conductor/workflow.md

Changes:
  - product.md: Updated user personas and success metrics
  - tech-stack.md: Added pytest and coverage tools
  - workflow.md: Updated TDD coverage requirement to 85%

❓ Update these files? (yes/no): yes

✅ Documentation updated successfully!

Backups created:
  - conductor/product.md.bak
  - conductor/tech-stack.md.bak
  - conductor/workflow.md.bak
```

## Parameters

### doc (default: "all")
Which document(s) to update:
- `product` - Update only product.md
- `tech-stack` - Update only tech-stack.md
- `workflow` - Update only workflow.md
- `all` - Update all three documents

### confirm (default: false)
Skip confirmation prompt:
- `true` - Update without asking
- `false` - Ask before updating (safer)

## Use Cases

### Use Case 1: Update After Setup Changes
```bash
# User modified setup_responses.json manually
/conductor-update
```

### Use Case 2: Update Specific Document
```bash
# Only update product documentation
/conductor-update doc=product
```

### Use Case 3: Automated Update
```bash
# In a script, skip confirmation
/conductor-update doc=all --confirm
```

## Error Handling

- If `setup_state.json` missing:
  - Error: "Setup not found. Run /conductor-setup first."
  - Suggest running setup

- If template file missing:
  - Error: "Template not found: {template_path}"
  - Suggest re-running setup or checking installation

- If backup fails:
  - Warning: "Could not create backup"
  - Continue with update (files will be overwritten)

- If write fails:
  - Error: "Could not write {file}"
  - Check file permissions
  - Restore from backup if created

## Backup Strategy

Before updating:
1. Copy existing file to `{file}.bak`
2. If .bak exists: `{file}.bak.1`, `.bak.2`, etc.
3. Keep up to 3 backup versions

To restore from backup:
```bash
# Check backups
ls conductor/*.bak*

# Restore specific backup
cp conductor/product.md.bak conductor/product.md
```

## Important Notes

- **Always creates backups** before overwriting
- **Uses setup_responses.json** as source of truth
- **Regenerates from templates** - manual edits will be lost
- **Ask before updating** unless confirm=true
- **Display in Portuguese** if user communicates in Portuguese
- **Use safe_print** for all output
