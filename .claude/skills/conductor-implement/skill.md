# Conductor Implement Command

You are executing the `/conductor-implement` command to execute a track plan with TDD workflow.

## Purpose
Execute a track plan automatically using Test-Driven Development (Red-Green-Refactor cycle) with checkpoints and git integration.

## Execution Steps

1. **Import ImplementationAgent:**
   ```python
   from claude_conductor.implementation_agent import ImplementationAgent
   agent = ImplementationAgent()
   ```

2. **Parse plan.md:**
   - Extract all phases
   - Extract all tasks with their status
   - Identify first incomplete task

3. **For each incomplete task, execute TDD cycle:**

   **Phase A: RED (Write Failing Test)**
   - Create test file if doesn't exist
   - Write test that captures the requirement
   - Run test and confirm it fails
   - Output: "❌ RED: Test failing (expected)"

   **Phase B: GREEN (Make Test Pass)**
   - Write minimal code to make test pass
   - Run test and confirm it passes
   - Output: "✅ GREEN: Test passing"

   **Phase C: REFACTOR (Improve Code)**
   - Review code quality
   - Refactor while keeping tests green
   - Run tests again to confirm
   - Output: "🔧 REFACTOR: Code improved"

   **Phase D: Verify Coverage**
   - Run coverage check
   - If coverage <80%: Add more tests
   - Output: "📊 Coverage: XX%"

   **Phase E: Git Commit**
   - Stage changes
   - Create conventional commit message:
     ```
     feat(scope): description

     Detailed explanation.

     Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
     ```
   - Commit with SHA
   - Output: "💾 Committed: abc1234"

   **Phase F: Attach Git Note**
   - Add detailed note with rationale
   - Note format:
     ```
     Task: [task description]
     Approach: [what was done]
     Tests: [test coverage details]
     Changes: [files modified]
     Rationale: [why this approach]
     ```
   - Output: "📝 Note added"

   **Phase G: Update plan.md**
   - Mark task as complete: `[x] task description abc1234`
   - Commit plan update

4. **At Phase End: Create Checkpoint**
   - Identify all changed files in phase
   - Verify test coverage for all files
   - Run full test suite
   - Generate manual verification plan
   - Wait for user approval (unless auto_mode)
   - Create checkpoint commit
   - Attach verification report as git note
   - Update plan.md with checkpoint SHA

5. **Display Progress:**
   - Show current task
   - Show phase progress
   - Show overall track progress

## TDD Workflow Detail

### Red Phase
```python
# 1. Identify what needs to be tested
# 2. Create/modify test file
# 3. Write test case
# 4. Run: pytest
# 5. Confirm test fails
```

### Green Phase
```python
# 1. Write minimal implementation
# 2. Run: pytest
# 3. Confirm test passes
# 4. No refactoring yet!
```

### Refactor Phase
```python
# 1. Review code for improvements
# 2. Refactor while tests pass
# 3. Run: pytest
# 4. Confirm still passing
```

### Coverage Check
```python
# 1. Run: pytest --cov=module --cov-report=term-missing
# 2. Check if coverage >= 80%
# 3. If not, identify untested code
# 4. Add more tests
# 5. Repeat until 80%+
```

## Output Format

```
🚀 Implementing track: feature_implement_user_auth_20260111

Phase 1: Authentication Module
  Task 1/5: Create user model
    ❌ RED: Writing test... test_user_model_creation
    ✅ GREEN: Implementation passing
    🔧 REFACTOR: Code optimized
    📊 Coverage: 85%
    💾 Committed: a1b2c3d
    📝 Note added

  ✅ Phase 1 Complete!
  Checkpoint: e5f6g7h

Overall Progress: 20% (1/5 tasks in phase 1 complete)
```

## Parameters

### track (required)
- Track identifier to execute
- Example: `feature_implement_operator_workflow_20260111`

### start_phase (optional)
- Phase number to resume from
- Default: 1 (start from beginning)
- Example: `2` (resume from phase 2)

### auto_mode (optional)
- Run without user interaction
- Default: false
- When true: skip confirmations at checkpoints

## Error Handling

- If test fails unexpectedly: Stop and ask user
- If coverage can't reach 80%: Ask if user wants to continue
- If git conflict: Stop and ask for resolution
- If file missing: Create or ask user

## Important Notes

- Always maintain >80% test coverage
- All commits must follow conventional commit format
- Git notes are mandatory for every commit
- Checkpoints require user approval (unless auto_mode)
- Display in Portuguese if user communicates in Portuguese
- Use safe_print for all output
