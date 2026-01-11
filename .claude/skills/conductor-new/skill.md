# Conductor New Track Command

You are executing the `/conductor-new` command to create a new Conductor track.

## Purpose
Create a new track (feature/bugfix/refactor/experiment) by conducting a structured interview and automatically generating spec.md and plan.md.

## Execution Steps

1. **Import PlanningAgent:**
   ```python
   from claude_conductor.planning_agent import PlanningAgent
   agent = PlanningAgent()
   ```

2. **Conduct structured interview with 13 questions:**

   Use AskUserQuestion tool for each question. Maximum 4 options per question.

   **Question 1: Track Type**
   - What type of track is this?
   - Options: feature, bugfix, refactor, experiment

   **Question 2: Title**
   - Short title for the track (text input)

   **Question 3: Description**
   - Detailed description of what this track will accomplish (text input)

   **Question 4: Priority**
   - What is the priority?
   - Options: Low, Medium, High, Critical

   **Question 5: Complexity**
   - How complex is this track?
   - Options: Low (1-3 days), Medium (4-7 days), High (1-2 weeks), Very High (3+ weeks)

   **Question 6: Dependencies**
   - Does this track depend on other tracks or external factors? (text input)

   **Question 7: Acceptance Criteria**
   - What are the acceptance criteria? (text input - define "done")

   **Question 8: Testing Requirements**
   - What testing is required?
   - Options: Unit tests only, Integration tests, Full test suite, Manual testing

   **Question 9: Documentation Needs**
   - What documentation is needed?
   - Options: None, Code comments, User docs, API docs + User docs

   **Question 10: Performance Impact**
   - Will this affect performance?
   - Options: No impact, Minor, Moderate, Major optimization needed

   **Question 11: Security Considerations**
   - Are there security implications?
   - Options: None, Minor (data validation), Major (auth/encryption), Critical (security fix)

   **Question 12: Migration Requirements**
   - Is data migration or schema changes needed?
   - Options: No, Simple data migration, Schema changes, Complex migration

   **Question 13: Rollback Plan**
   - How can this be rolled back if needed?
   - Options: Easy revert, Manual revert, Difficult, Cannot be rolled back

3. **Generate Track ID:**
   - Use format: {type}_{name}_{date}
   - Example: feature_implement_user_auth_20260111

4. **Generate spec.md:**
   - 8 sections: Overview, Background, Requirements, Architecture, etc.
   - Use template from `claude-conductor/templates/spec_template.md`

5. **Generate plan.md:**
   - Break down into 2-5 phases based on complexity
   - Each phase has 3-10 tasks
   - Use template from `claude-conductor/templates/plan_template.md`

6. **Generate metadata.json:**
   - Store track metadata

7. **Update tracks.md:**
   - Register the new track

8. **Display results:**
   - Track ID
   - Spec path
   - Plan path
   - Next steps to start implementation

## Output Example

```
✅ Track created successfully!

Track ID: feature_implement_user_auth_20260111
Type: Feature
Priority: High

Files created:
  - conductor/tracks/feature_implement_user_auth_20260111/spec.md
  - conductor/tracks/feature_implement_user_auth_20260111/plan.md
  - conductor/tracks/feature_implement_user_auth_20260111/metadata.json

Next steps:
  1. Review the spec: cat conductor/tracks/feature_implement_user_auth_20260111/spec.md
  2. Review the plan: cat conductor/tracks/feature_implement_user_auth_20260111/plan.md
  3. Start implementing: /conductor-implement track=feature_implement_user_auth_20260111
```

## Important Notes
- Always use AskUserQuestion (max 4 options)
- Store all responses in a dictionary
- Validate required fields before generation
- Handle errors gracefully
- Display in Portuguese if user communicates in Portuguese
