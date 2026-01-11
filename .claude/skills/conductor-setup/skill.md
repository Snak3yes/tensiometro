# Conductor Setup Command

You are executing the `/conductor-setup` command to initialize the Conductor system for the project.

## Purpose
Initialize the Conductor system by conducting 4 structured interviews and generating base documentation.

## Execution Steps

1. **Check if setup already exists:**
   ```python
   from claude_conductor.setup_agent import SetupAgent
   agent = SetupAgent()
   exists = agent.check_existing_setup()
   ```

2. **If exists and not reconfigure:**
   - Ask user if they want to reconfigure
   - If no, exit with message showing existing setup location

3. **Run setup interviews:**
   - Use AskUserQuestion tool for each interview
   - Load questions from `claude-conductor/interview_templates/`

4. **Generate documentation:**
   - product.md
   - product-guidelines.md
   - tech-stack.md
   - workflow.md
   - tracks.md

5. **Display results:**
   - Show generated files location
   - Confirm success

## Interview Templates

### Phase 1: Product Vision (`product_vision.json`)
4 questions about product type, users, goals, and features.

### Phase 2: Product Guidelines (`product_guidelines.json`)
4 questions about UI/UX, theme, tone, and error handling.

### Phase 3: Technology Stack (`tech_stack.json`)
4 questions about languages, frameworks, database, and testing.

### Phase 4: Workflow Preferences (`workflow_preferences.json`)
7 questions about TDD, coverage, commits, and checkpoints.

## Output Location
Generated files go to `conductor/` directory (not `claude-conductor/`).

## Error Handling
- If interviews fail: Show error and suggest retry
- If file write fails: Check permissions and suggest alternative location
- Always provide helpful error messages in Portuguese if user communicates in Portuguese
