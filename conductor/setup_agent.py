#!/usr/bin/env python3
"""
Conductor Setup Agent

This script orchestrates the initial setup of Conductor for a project.
It conducts structured interviews to gather project context and generates
the core documentation files.

Usage:
    python conductor/setup_agent.py

The agent will:
1. Check if setup was already completed
2. Conduct 4 structured interviews (Product, Guidelines, Tech Stack, Workflow)
3. Generate documentation files in conductor/
4. Save setup state
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class SetupAgent:
    """Orchestrates the Conductor setup process."""

    def __init__(self, project_root: str = None):
        """Initialize the setup agent.

        Args:
            project_root: Path to project root. If None, auto-detect.
        """
        if project_root is None:
            # Auto-detect project root (directory containing conductor/)
            current = Path(__file__).resolve().parent.parent
            self.project_root = current
        else:
            self.project_root = Path(project_root)

        self.conductor_dir = self.project_root / "conductor"
        self.templates_dir = self.conductor_dir / "interview_templates"
        self.doc_templates_dir = self.conductor_dir / "templates"
        self.state_file = self.conductor_dir / "setup_state.json"

        self.responses: Dict[str, Any] = {}

    def check_existing_setup(self) -> bool:
        """Check if setup was already completed.

        Returns:
            True if setup exists and is complete.
        """
        if not self.state_file.exists():
            return False

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                return state.get("last_successful_step") == "setup_complete"
        except Exception:
            return False

    def load_interview_template(self, phase: str) -> Dict:
        """Load interview template JSON.

        Args:
            phase: Phase name (e.g., 'product_vision')

        Returns:
            Interview template dictionary.
        """
        template_file = self.templates_dir / f"{phase}.json"
        with open(template_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_doc_template(self, template_name: str) -> str:
        """Load document template.

        Args:
            template_name: Template filename (e.g., 'product_template.md')

        Returns:
            Template content as string.
        """
        template_file = self.doc_templates_dir / template_name
        with open(template_file, 'r', encoding='utf-8') as f:
            return f.read()

    def format_answers_for_claude(self, template: Dict) -> List[Dict]:
        """Format interview questions for Claude's AskUserQuestion tool.

        Args:
            template: Interview template dictionary.

        Returns:
            List of question dictionaries formatted for AskUserQuestion.
        """
        questions = []

        for q in template["questions"]:
            question_dict = {
                "question": q["question"],
                "header": q.get("header", q["id"]),
                "multiSelect": q.get("type") == "multi_choice",
                "options": []
            }

            # Add options if present
            if "options" in q:
                for opt in q["options"]:
                    question_dict["options"].append({
                        "label": opt["label"],
                        "description": opt.get("description", "")
                    })

            # For text questions, we'll handle them separately
            if q.get("type") == "text":
                question_dict["options"] = [
                    {"label": "Provide answer", "description": "Enter your response"}
                ]

            questions.append(question_dict)

        return questions

    def conduct_interview(self, phase: str) -> Dict[str, Any]:
        """Conduct a single interview phase.

        This method prepares the questions but returns a dictionary
        that should be used with Claude's AskUserQuestion tool.

        Args:
            phase: Interview phase name.

        Returns:
            Dictionary with interview metadata and questions.
        """
        template = self.load_interview_template(phase)

        return {
            "phase": phase,
            "title": template["title"],
            "description": template["description"],
            "template": template,
            "formatted_questions": self.format_answers_for_claude(template)
        }

    def save_responses(self, phase: str, responses: Dict[str, Any]):
        """Save responses from an interview phase.

        Args:
            phase: Interview phase name.
            responses: User responses dictionary.
        """
        self.responses[phase] = responses

    def generate_product_md(self) -> str:
        """Generate product.md from responses.

        Returns:
            Generated markdown content.
        """
        template = self.load_doc_template("product_template.md")

        pv = self.responses.get("product_vision", {})

        # Format user personas
        personas = pv.get("user_personas", [])
        if isinstance(personas, list):
            personas_text = "\n".join([f"- **{p}**" for p in personas])
        else:
            personas_text = str(personas)

        # Fill template
        content = template.format(
            product_description=pv.get("product_description", "Not provided"),
            product_type=pv.get("product_type", "Not specified"),
            user_personas=personas_text,
            primary_goals=pv.get("primary_goals", "Not provided"),
            key_features=pv.get("key_features", "Not provided"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        return content

    def generate_product_guidelines_md(self) -> str:
        """Generate product-guidelines.md from responses.

        Returns:
            Generated markdown content.
        """
        template = self.load_doc_template("product_guidelines_template.md")

        pg = self.responses.get("product_guidelines", {})

        content = template.format(
            ui_style=pg.get("ui_style", "Not specified"),
            ui_style_description=pg.get("ui_style_description", ""),
            theme=pg.get("theme", "Not specified"),
            theme_description=pg.get("theme_description", ""),
            tone_of_voice=pg.get("tone_of_voice", "Not specified"),
            tone_description=pg.get("tone_description", ""),
            error_handling=pg.get("error_handling", "Not specified"),
            error_handling_description=pg.get("error_handling_description", ""),
            design_principles=pg.get("design_principles", "Not provided"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        return content

    def generate_tech_stack_md(self) -> str:
        """Generate tech-stack.md from responses.

        Returns:
            Generated markdown content.
        """
        template = self.load_doc_template("tech_stack_template.md")

        ts = self.responses.get("tech_stack", {})

        content = template.format(
            primary_language=ts.get("primary_language", "Not specified"),
            frameworks=ts.get("frameworks", "Not provided"),
            database=ts.get("database", "Not specified"),
            database_description=ts.get("database_description", ""),
            testing_framework=ts.get("testing_framework", "Not specified"),
            package_manager=ts.get("package_manager", "Not specified"),
            additional_tools=ts.get("additional_tools", "Not provided"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        return content

    def generate_workflow_md(self) -> str:
        """Generate workflow.md from responses.

        Returns:
            Generated markdown content.
        """
        template = self.load_doc_template("workflow_template.md")

        wf = self.responses.get("workflow_preferences", {})

        # Build conditional sections based on responses
        dev_method = wf.get("development_methodology", "Test-Driven Development (TDD)")

        if "TDD" in dev_method:
            tdd_phase_name = "Write Failing Tests (Red Phase)"
            tdd_workflow_description = """   - Create a new test file for the feature or bug fix.
   - Write one or more unit tests that clearly define the expected behavior and acceptance criteria for the task.
   - **CRITICAL:** Run the tests and confirm that they fail as expected. This is the "Red" phase of TDD. Do not proceed until you have failing tests."""
            methodology_description = "Follow strict TDD protocol: Red-Green-Refactor cycle"
        else:
            tdd_phase_name = "Write Tests"
            tdd_workflow_description = "   - Write comprehensive unit tests for the implementation."
            methodology_description = "Tests are required but order is flexible"

        # Smoke test sections
        smoke_policy = wf.get("smoke_tests", "Yes (Recommended)")
        if "Yes" in smoke_policy:
            smoke_test_step = "   - **Smoke Test:** Run the application (e.g., `python main.py`) to verify it starts and runs without immediate crashes. If it fails, fix the error and repeat."
            smoke_test_refactor_step = "   - **Smoke Test:** Run the application again to ensure refactoring didn't break startup."
            smoke_test_policy_text = "Smoke Test After Each Task"
            smoke_test_description = "Run application to ensure it starts without errors"
            smoke_test_done = "Application executes without errors (Smoke Test pass)"
            smoke_test_command = "python main.py  # Or your app's entry point"
        elif "phase" in smoke_policy.lower():
            smoke_test_step = ""
            smoke_test_refactor_step = ""
            smoke_test_policy_text = "Smoke Test After Phases"
            smoke_test_description = "Run application at phase boundaries"
            smoke_test_done = "Phase smoke test passed"
            smoke_test_command = "python main.py  # Run at phase checkpoints"
        else:
            smoke_test_step = ""
            smoke_test_refactor_step = ""
            smoke_test_policy_text = "No Smoke Tests"
            smoke_test_description = "Rely on unit/integration tests"
            smoke_test_done = "Tests passing"
            smoke_test_command = "# Smoke tests not configured"

        # Git notes sections
        git_notes_policy = wf.get("git_notes", "Yes (Recommended)")
        if "Yes" in git_notes_policy:
            git_notes_section = """9. **Attach Task Summary with Git Notes:**
   - **Step 9.1: Get Commit Hash:** Obtain the hash of the *just-completed commit* (`git log -1 --format="%H"`).
   - **Step 9.2: Draft Note Content:** Create a detailed summary for the completed task. This should include the task name, a summary of changes, a list of all created/modified files, and the core "why" for the change.
   - **Step 9.3: Attach Note:** Use the `git notes` command to attach the summary to the commit.
     ```bash
     # The note content from the previous step is passed via the -m flag.
     git notes add -m "<note content>" <commit_hash>
     ```"""
            git_notes_done = "10. Git note with task summary attached to the commit"
        elif "checkpoint" in git_notes_policy.lower():
            git_notes_section = """9. **Git Notes for Checkpoints:**
   - Git notes will be attached only at phase checkpoint commits.
   - Regular task commits use commit messages only."""
            git_notes_done = "10. Git note attached to checkpoint commit"
        else:
            git_notes_section = """9. **No Git Notes:**
   - Project relies on commit messages only.
   - Ensure commit messages are descriptive."""
            git_notes_done = ""

        # Checkpoint protocol
        checkpoint_required = wf.get("verification_checkpoints", "Yes (Recommended)")
        if "Yes" in checkpoint_required:
            checkpoint_protocol = """**Trigger:** This protocol is executed immediately after a task is completed that also concludes a phase in `plan.md`.

1.  **Announce Protocol Start:** Inform the user that the phase is complete and the verification and checkpointing protocol has begun.

2.  **Ensure Test Coverage for Phase Changes:**
    -   **Step 2.1: Determine Phase Scope:** To identify the files changed in this phase, you must first find the starting point. Read `plan.md` to find the Git commit SHA of the *previous* phase's checkpoint. If no previous checkpoint exists, the scope is all changes since the first commit.
    -   **Step 2.2: List Changed Files:** Execute `git diff --name-only <previous_checkpoint_sha> HEAD` to get a precise list of all files modified during this phase.
    -   **Step 2.3: Verify and Create Tests:** For each file in the list:
        -   **CRITICAL:** First, check its extension. Exclude non-code files (e.g., `.json`, `.md`, `.yaml`).
        -   For each remaining code file, verify a corresponding test file exists.
        -   If a test file is missing, you **must** create one. Before writing the test, **first, analyze other test files in the repository to determine the correct naming convention and testing style.** The new tests **must** validate the functionality described in this phase's tasks (`plan.md`).

3.  **Execute Automated Tests with Proactive Debugging:**
    -   Before execution, you **must** announce the exact shell command you will use to run the tests.
    -   Execute the announced command.
    -   If tests fail, you **must** inform the user and begin debugging. You may attempt to propose a fix a **maximum of two times**. If the tests still fail after your second proposed fix, you **must stop**, report the persistent failure, and ask the user for guidance.

4.  **Propose a Detailed, Actionable Manual Verification Plan:**
    -   **CRITICAL:** To generate the plan, first analyze `product.md`, `product-guidelines.md`, and `plan.md` to determine the user-facing goals of the completed phase.
    -   You **must** generate a step-by-step plan that walks the user through the verification process, including any necessary commands and specific, expected outcomes.

5.  **Await Explicit User Feedback:**
    -   After presenting the detailed plan, ask the user for confirmation: "**Does this meet your expectations? Please confirm with yes or provide feedback on what needs to be changed.**"
    -   **PAUSE** and await the user's response. Do not proceed without an explicit yes or confirmation.

6.  **Create Checkpoint Commit:**
    -   Stage all changes. If no changes occurred in this step, proceed with an empty commit.
    -   Perform the commit with a clear and concise message (e.g., `conductor(checkpoint): Checkpoint end of Phase X`).

7.  **Attach Auditable Verification Report using Git Notes:**
    -   **Step 7.1: Draft Note Content:** Create a detailed verification report including the automated test command, the manual verification steps, and the user's confirmation.
    -   **Step 7.2: Attach Note:** Use the `git notes` command and the full commit hash from the previous step to attach the full report to the checkpoint commit.

8.  **Get and Record Phase Checkpoint SHA:**
    -   **Step 8.1: Get Commit Hash:** Obtain the hash of the *just-created checkpoint commit* (`git log -1 --format="%H"`).
    -   **Step 8.2: Update Plan:** Read `plan.md`, find the heading for the completed phase, and append the first 7 characters of the commit hash in the format `[checkpoint: <sha>]`.
    -   **Step 8.3: Write Plan:** Write the updated content back to `plan.md`.

9. **Commit Plan Update:**
    - **Action:** Stage the modified `plan.md` file.
    - **Action:** Commit this change with a descriptive message following the format `conductor(plan): Mark phase '<PHASE NAME>' as complete`.

10.  **Announce Completion:** Inform the user that the phase is complete and the checkpoint has been created, with the detailed verification report attached as a git note."""
        elif "Optional" in checkpoint_required:
            checkpoint_protocol = """**Trigger:** User can choose whether to use checkpoints for each track.

Manual verification steps are simplified but still recommended at phase boundaries."""
        else:
            checkpoint_protocol = """**Note:** Manual verification checkpoints are not enforced.

Phases complete automatically after all tasks finish. Consider enabling checkpoints for critical projects."""

        # Commit convention
        commit_conv = wf.get("commit_strategy", "Conventional Commits")
        if "Conventional" in commit_conv:
            commit_convention = "type(scope): description"
            commit_format_example = "feat(auth): Add OAuth2 support\nfix(api): Handle null responses\nrefactor(ui): Simplify form logic"
        else:
            commit_convention = "Clear descriptive message"
            commit_format_example = "Add OAuth2 authentication support\nFix API null response handling"

        # Commands (detect from tech stack)
        ts = self.responses.get("tech_stack", {})
        test_framework = ts.get("testing_framework", "pytest")

        if "pytest" in test_framework.lower():
            test_command = "pytest"
            coverage_command = "pytest --cov=aoi_lib --cov=consumo_lib --cov-report=html --cov-report=term"
        elif "unittest" in test_framework.lower():
            test_command = "python -m unittest discover"
            coverage_command = "coverage run -m unittest discover && coverage report"
        elif "jest" in test_framework.lower():
            test_command = "npm test"
            coverage_command = "npm test -- --coverage"
        else:
            test_command = "# Configure test command"
            coverage_command = "# Configure coverage command"

        content = template.format(
            development_methodology=dev_method,
            methodology_description=methodology_description,
            coverage_target=wf.get("coverage_target", "95% or higher"),
            smoke_test_policy=smoke_test_policy_text,
            smoke_test_description=smoke_test_description,
            tdd_phase_name=tdd_phase_name,
            tdd_workflow_description=tdd_workflow_description,
            smoke_test_step=smoke_test_step,
            smoke_test_refactor_step=smoke_test_refactor_step,
            commit_convention=commit_convention,
            git_notes_section=git_notes_section,
            checkpoint_protocol=checkpoint_protocol,
            test_command=test_command,
            coverage_command=coverage_command,
            smoke_test_command=smoke_test_command,
            commit_format_example=commit_format_example,
            smoke_test_done=smoke_test_done,
            git_notes_done=git_notes_done,
            additional_preferences=wf.get("additional_preferences", "None specified"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        return content

    def generate_tracks_md(self) -> str:
        """Generate initial tracks.md file.

        Returns:
            Generated markdown content.
        """
        content = """# Project Tracks

This file tracks all major tracks for the project. Each track has its own detailed plan in its respective folder.

---

*No tracks created yet. Use `/conductor:newTrack` to create your first track.*

---
*This document is managed by Conductor. Last updated: {timestamp}*
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        return content

    def save_state(self, step: str):
        """Save setup state to JSON file.

        Args:
            step: Current step identifier.
        """
        state = {
            "last_successful_step": step,
            "timestamp": datetime.now().isoformat(),
            "responses": self.responses
        }

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def write_documentation(self):
        """Write all generated documentation files."""
        docs = {
            "product.md": self.generate_product_md(),
            "product-guidelines.md": self.generate_product_guidelines_md(),
            "tech-stack.md": self.generate_tech_stack_md(),
            "workflow.md": self.generate_workflow_md(),
            "tracks.md": self.generate_tracks_md()
        }

        for filename, content in docs.items():
            filepath = self.conductor_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Generated: {filename}")

    def run_setup(self, responses_dict: Dict[str, Dict[str, Any]] = None):
        """Run the complete setup process.

        Args:
            responses_dict: Pre-collected responses (for automated testing).
                          If None, returns interview metadata for manual execution.

        Returns:
            If responses_dict is None, returns list of interview phases.
            Otherwise, completes setup and returns success status.
        """
        # Check existing setup
        if self.check_existing_setup():
            print("[WARNING] Conductor setup already completed.")
            response = input("Do you want to reconfigure? (yes/no): ")
            if response.lower() != "yes":
                print("Setup cancelled.")
                return {"status": "cancelled"}

        # If responses provided (automated mode), use them
        if responses_dict:
            self.responses = responses_dict
            self.write_documentation()
            self.save_state("setup_complete")
            print("\n[SUCCESS] Conductor setup complete!")
            print("\nNext steps:")
            print("1. Review generated documentation in conductor/")
            print("2. Create your first track with: /conductor:newTrack")
            return {"status": "complete"}

        # Manual mode - return interview phases for Claude to execute
        phases = [
            "product_vision",
            "product_guidelines",
            "tech_stack",
            "workflow_preferences"
        ]

        interviews = []
        for phase in phases:
            interview_data = self.conduct_interview(phase)
            interviews.append(interview_data)

        return {
            "status": "ready_for_interviews",
            "interviews": interviews
        }


if __name__ == "__main__":
    # When run directly, start setup in manual mode
    agent = SetupAgent()
    result = agent.run_setup()

    if result.get("status") == "ready_for_interviews":
        print("\n" + "="*60)
        print("CONDUCTOR SETUP - MANUAL MODE")
        print("="*60)
        print("\nThis script requires Claude Code to conduct interviews.")
        print("Please invoke this through Claude Code instead.")
        print("\nPhases to interview:")
        for interview in result["interviews"]:
            print(f"  - {interview['title']}")
