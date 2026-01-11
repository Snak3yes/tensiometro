# Conductor System for Claude Code

You are the Conductor system interface for project management. When the user invokes `/conductor`, execute the requested command by running the appropriate Python script from the `claude-conductor/` directory.

## Available Commands

### `/conductor setup` - Initialize Conductor System
**Purpose:** Initialize the Conductor system for the current project with structured interviews.

**Script:** `claude-conductor/setup_agent.py`

**Execution:**
```python
from claude_conductor.setup_agent import SetupAgent
agent = SetupAgent()
agent.run_setup()
```

**Parameters:**
- `reconfigure` (bool): If true, reconfigure even if setup already exists

**Output:** Display the generated documents location and status

---

### `/conductor status` - Show Track Status
**Purpose:** Display status of all tracks with progress percentages.

**Script:** `claude-conductor/support_commands.py`

**Execution:**
```python
from claude_conductor.support_commands import SupportCommands
cmd = SupportCommands()
result = cmd.status(verbose=True)
# Display formatted result
```

**Output:** Formatted table showing:
- Track ID and type
- Status (pending, in-progress, complete, archived)
- Progress percentage
- Current phase/task

---

### `/conductor new` - Create New Track
**Purpose:** Create a new track (feature/bugfix/refactor) with automatic spec and plan generation.

**Script:** `claude-conductor/planning_agent.py`

**Execution:**
```python
from claude_conductor.planning_agent import PlanningAgent
agent = PlanningAgent()
# Conduct interview using AskUserQuestion
result = agent.create_track()
# Display generated spec.md and plan.md location
```

**Interview Questions:** Ask the user 13 structured questions about the track:
1. Track type (feature/bugfix/refactor/experiment)
2. Title and description
3. Priority and complexity
4. Dependencies
5. Acceptance criteria
6. Testing requirements
7. Documentation needs
8. Performance impact
9. Security considerations
10. Migration requirements
11. Rollback plan
12. Success metrics
13. Target completion date

**Output:** Track ID and generated document locations

---

### `/conductor implement` - Execute Track Plan
**Purpose:** Execute a track plan with automatic TDD workflow (Red-Green-Refactor).

**Script:** `claude-conductor/implementation_agent.py`

**Execution:**
```python
from claude_conductor.implementation_agent import ImplementationAgent
agent = ImplementationAgent()
agent.execute_track(track_id="{track_id}")
```

**Workflow:**
1. Parse plan.md to extract phases and tasks
2. For each incomplete task:
   a. **RED phase:** Write failing test
   b. **GREEN phase:** Implement minimal code to pass
   c. **REFACTOR phase:** Improve code quality
   d. Run coverage check (>80% required)
   e. Git commit with conventional commit message
   f. Add detailed git note with rationale
3. At phase end: Create checkpoint with smoke tests

**Parameters:**
- `track` (required): Track identifier (e.g., feature_implement_operator_workflow_20260111)
- `start_phase` (optional): Phase number to resume from

**Output:** Progress updates showing each task completion

---

### `/conductor revert` - Revert Track/Phase/Task
**Purpose:** Revert a track, phase, or task using git reset.

**Script:** `claude-conductor/support_commands.py`

**Execution:**
```python
from claude_conductor.support_commands import SupportCommands
cmd = SupportCommands()
result = cmd.revert_track(track_id="{track_id}", phase={phase})
```

**Parameters:**
- `track` (required): Track identifier
- `phase` (optional): Phase number to revert to

**Confirmation:** Always ask user for confirmation before reverting

---

### `/conductor update` - Update Base Documentation
**Purpose:** Update Conductor base documentation from setup responses.

**Script:** `claude-conductor/support_commands.py`

**Execution:**
```python
from claude_conductor.support_commands import SupportCommands
cmd = SupportCommands()
result = cmd.update_documentation(doc_type="{doc}")
```

**Parameters:**
- `doc` (enum): "product", "tech-stack", "workflow", or "all"

**Confirmation:** Ask user for confirmation unless explicitly confirmed

---

### `/conductor archive` - Archive Completed Track
**Purpose:** Archive a completed track to prevent cluttering active track list.

**Script:** `claude-conductor/support_commands.py`

**Execution:**
```python
from claude_conductor.support_commands import SupportCommands
cmd = SupportCommands()
result = cmd.archive_track("{track_id}")
```

**Confirmation:** Always ask user for confirmation

---

## Important Notes

1. **Always run Python scripts from the project root directory**
2. **Use safe_print for all output** to handle Windows encoding issues
3. **Display results in Portuguese** when the user communicates in Portuguese
4. **Handle errors gracefully** and show user-friendly error messages
5. **Verify git status** before any revert or archive operations
6. **Show progress indicators** for long-running operations (like implement)

## File Structure Reference

```
claude-conductor/
├── setup_agent.py          # Setup command
├── planning_agent.py       # New track command
├── implementation_agent.py # Implement command
├── support_commands.py     # Status, revert, update, archive
├── interview_templates/    # JSON interview templates
└── templates/              # Markdown document templates

conductor/
├── product.md              # Product vision
├── tech-stack.md           # Technology stack
├── workflow.md             # Workflow preferences
├── tracks.md               # Track registry
└── tracks/                 # Individual track directories
    └── {track_id}/
        ├── spec.md         # Track specification
        ├── plan.md         # Implementation plan
        └── metadata.json   # Track metadata
```

## Error Handling

If a script fails:
1. Display the error message clearly
2. Show the stack trace if in debug mode
3. Suggest next steps to resolve the issue
4. Never crash - always provide helpful feedback
