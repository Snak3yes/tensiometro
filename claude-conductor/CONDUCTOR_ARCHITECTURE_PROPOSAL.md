# Conductor Architecture Proposal for Claude Code
**Data:** 2026-01-11
**Autor:** Claude Sonnet 4.5
**Status:** Proposta de Arquitetura

---

## 📋 Executive Summary

Este documento propõe uma arquitetura completa de **agentes autônomos** para implementar o sistema **Conductor** no Claude Code, baseado no [Conductor extension do Gemini CLI](https://github.com/gemini-cli-extensions/conductor). O objetivo é criar um sistema de desenvolvimento **context-driven** com memória persistente, verificação rigorosa e TDD automático.

**Principais benefícios:**
- ✅ **Memória Persistente:** Contexto gerenciado como artefato versionado
- ✅ **Qualidade Garantida:** TDD obrigatório com >95% de cobertura
- ✅ **Auditabilidade Total:** Git notes detalhados em cada etapa
- ✅ **Verificação Humana:** Checkpoints manuais entre fases
- ✅ **Rastreabilidade:** Cada tarefa linkada ao commit SHA

---

## 🎯 Análise Profunda do Conductor

### 1.1 Conceito Core

O Conductor transforma o desenvolvimento de software de **conversation-driven** para **context-driven**:

| Tradicional (Chat) | Context-Driven (Conductor) |
|-------------------|---------------------------|
| Contexto em histórico de chat volátil | Contexto persistente em arquivos Markdown |
| Sem rastreabilidade estruturada | Specs, plans e metadata versionados |
| Tarefas implícitas | Tarefas explícitas com status rastreável |
| Verificação ad-hoc | Checkpoints formais em cada fase |
| Commits sem contexto | Git notes com sumário detalhado |

### 1.2 Fluxo de Vida Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONDUCTOR LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────┘

Phase 1: SETUP (Once per project)
  ┌─────────────────────────────────────────────────────────┐
  │ /conductor:setup                                        │
  │  ├─ Interview: Product Vision                          │
  │  ├─ Interview: Product Guidelines                      │
  │  ├─ Interview: Tech Stack                              │
  │  ├─ Interview: Workflow Preferences                    │
  │  └─ Generate:                                           │
  │     ├─ conductor/product.md                            │
  │     ├─ conductor/product-guidelines.md                 │
  │     ├─ conductor/tech-stack.md                         │
  │     ├─ conductor/workflow.md                           │
  │     ├─ conductor/code_styleguides/*.md                 │
  │     └─ conductor/tracks.md                             │
  └─────────────────────────────────────────────────────────┘

Phase 2: PLANNING (Per feature/bug)
  ┌─────────────────────────────────────────────────────────┐
  │ /conductor:newTrack "Feature description"              │
  │  ├─ Generate Track ID: <feature_name_YYYYMMDD>        │
  │  ├─ Create conductor/tracks/<track_id>/                │
  │  ├─ Interview: Detailed Requirements                   │
  │  ├─ Generate:                                           │
  │  │  ├─ spec.md (What & Why)                            │
  │  │  ├─ plan.md (Phases → Tasks → Subtasks)            │
  │  │  └─ metadata.json (ID, status, timestamps)          │
  │  ├─ User reviews and approves spec & plan             │
  │  └─ Update conductor/tracks.md registry               │
  └─────────────────────────────────────────────────────────┘

Phase 3: IMPLEMENTATION (Automated with checkpoints)
  ┌─────────────────────────────────────────────────────────┐
  │ /conductor:implement                                    │
  │  ├─ Load plan.md                                        │
  │  ├─ For each Phase:                                     │
  │  │  ├─ For each Task:                                  │
  │  │  │  ├─ Mark [~] in plan.md                          │
  │  │  │  ├─ TDD Cycle:                                    │
  │  │  │  │  ├─ Write failing tests (RED)                │
  │  │  │  │  ├─ Implement code (GREEN)                   │
  │  │  │  │  ├─ Refactor (REFACTOR)                      │
  │  │  │  │  └─ Verify coverage >95%                     │
  │  │  │  ├─ Smoke test application                       │
  │  │  │  ├─ Commit with message                          │
  │  │  │  ├─ Attach git note (summary + files)           │
  │  │  │  ├─ Mark [x] with commit SHA in plan.md         │
  │  │  │  └─ Commit plan update                           │
  │  │  └─ Next task...                                    │
  │  │                                                       │
  │  ├─ PHASE CHECKPOINT:                                   │
  │  │  ├─ Identify all changed files (git diff)          │
  │  │  ├─ Verify test coverage for each file             │
  │  │  ├─ Run full test suite                            │
  │  │  ├─ Generate manual verification plan              │
  │  │  ├─ Wait for user approval                         │
  │  │  ├─ Commit checkpoint                              │
  │  │  ├─ Attach verification report (git note)          │
  │  │  ├─ Update plan.md with checkpoint SHA             │
  │  │  └─ Commit plan update                             │
  │  └─ Next phase...                                       │
  └─────────────────────────────────────────────────────────┘

Phase 4: COMPLETION & ARCHIVE
  ┌─────────────────────────────────────────────────────────┐
  │ Track Completion                                        │
  │  ├─ All phases verified                                 │
  │  ├─ Update tracks.md (mark completed)                   │
  │  ├─ Move track to conductor/archive/                    │
  │  └─ Optional: Generate completion report                │
  └─────────────────────────────────────────────────────────┘

Supporting Commands:
  - /conductor:status      → Show progress across all tracks
  - /conductor:revert      → Revert track/phase/task logically
  - /conductor:update      → Update product/tech-stack docs
```

### 1.3 Estrutura de Arquivos

```
project_root/
├─ conductor/
│  ├─ product.md                    # Visão, usuários, funcionalidades
│  ├─ product-guidelines.md         # Brand voice, UI/UX guidelines
│  ├─ tech-stack.md                 # Tecnologias e rationale
│  ├─ workflow.md                   # Metodologia (TDD, commits, etc)
│  ├─ tracks.md                     # Master registry of all tracks
│  ├─ setup_state.json              # Estado do setup
│  ├─ code_styleguides/
│  │  ├─ python.md
│  │  ├─ javascript.md
│  │  └─ ...
│  ├─ tracks/
│  │  ├─ feature_auth_20260110/
│  │  │  ├─ metadata.json           # Track ID, status, timestamps
│  │  │  ├─ spec.md                 # Detailed requirements
│  │  │  └─ plan.md                 # Phases → Tasks → Subtasks
│  │  ├─ bugfix_login_20260111/
│  │  │  ├─ metadata.json
│  │  │  ├─ spec.md
│  │  │  └─ plan.md
│  │  └─ ...
│  └─ archive/
│     ├─ feature_auth_20260110/
│     └─ ...
```

---

## 🔍 Gap Analysis: Estado Atual vs. Ideal

### ✅ O que já existe

| Componente | Status | Localização |
|-----------|--------|-------------|
| Estrutura de diretórios | ✅ Completo | `conductor/` |
| Documentação base | ✅ Completo | `product.md`, `tech-stack.md`, etc |
| Workflow template | ✅ Completo | `workflow.md` |
| Tracks directory | ✅ Completo | `conductor/tracks/` |
| Archive directory | ✅ Completo | `conductor/archive/` |
| Metadata structure | ✅ Completo | `metadata.json` em cada track |
| Git notes usage | ✅ Parcial | Usado em checkpoints |
| TDD workflow | ✅ Completo | Definido em `workflow.md` |

### ❌ O que falta

| Componente | Status | Prioridade |
|-----------|--------|-----------|
| Comandos automatizados | ❌ Ausente | 🔴 CRÍTICO |
| Agente de setup | ❌ Ausente | 🔴 CRÍTICO |
| Agente de planning | ❌ Ausente | 🔴 CRÍTICO |
| Agente de implementation | ❌ Ausente | 🔴 CRÍTICO |
| Sistema de checkpoints | ❌ Ausente | 🔴 CRÍTICO |
| Entrevistas interativas | ❌ Ausente | 🟡 ALTA |
| Verificação automática | ❌ Ausente | 🟡 ALTA |
| Status reporting | ❌ Ausente | 🟢 MÉDIA |
| Revert capabilities | ❌ Ausente | 🟢 MÉDIA |

---

## 🏗️ Arquitetura Proposta: Sistema de Agentes

### 2.1 Visão Geral da Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                    CONDUCTOR AGENT SYSTEM                        │
└──────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │  Conductor      │
                    │  Orchestrator   │
                    │  (Master Agent) │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐        ┌──────▼──────┐     ┌──────▼──────┐
   │ Setup   │        │  Planning   │     │Implementation│
   │ Agent   │        │   Agent     │     │   Agent     │
   └────┬────┘        └──────┬──────┘     └──────┬──────┘
        │                    │                    │
   ┌────▼────┐        ┌──────▼──────┐     ┌──────▼──────┐
   │Interview│        │Spec         │     │  TDD        │
   │Subagent │        │Generator    │     │ Executor    │
   └─────────┘        │Subagent     │     │ Subagent    │
                      └─────────────┘     └──────┬──────┘
                      ┌─────────────┐            │
                      │Plan         │     ┌──────▼──────┐
                      │Generator    │     │Checkpoint   │
                      │Subagent     │     │Verifier     │
                      └─────────────┘     │Subagent     │
                                          └─────────────┘

         ┌──────────────────────────────────────┐
         │     SHARED SERVICES LAYER            │
         ├──────────────────────────────────────┤
         │ • FileManager (Read/Write MD/JSON)   │
         │ • GitManager (Commits, Notes, Diff)  │
         │ • TestRunner (Pytest execution)      │
         │ • CoverageAnalyzer (Coverage.py)     │
         │ • SmokeTestRunner (Application test) │
         │ • DocumentationValidator             │
         └──────────────────────────────────────┘
```

### 2.2 Agentes Principais

#### 2.2.1 **ConductorOrchestrator** (Master Agent)
**Responsabilidade:** Coordenar todo o fluxo do Conductor

**Skills:**
- `/conductor:setup` → Delega para SetupAgent
- `/conductor:newTrack` → Delega para PlanningAgent
- `/conductor:implement` → Delega para ImplementationAgent
- `/conductor:status` → Gera relatório de progresso
- `/conductor:revert` → Gerencia rollback lógico
- `/conductor:update` → Atualiza documentação base

**Estado mantido:**
- `setup_state.json` (progresso do setup)
- `tracks.md` (registro mestre)

#### 2.2.2 **SetupAgent** (Phase 1)
**Responsabilidade:** Inicialização do projeto com entrevistas

**Subagentes:**
- **InterviewSubagent** → Conduz entrevistas estruturadas

**Workflow:**
```
1. Check if conductor/ exists
   ├─ Yes → Ask user if wants to reconfigure
   └─ No → Proceed with setup

2. Interview: Product Vision
   ├─ Questions: User personas, goals, key features
   └─ Generate: conductor/product.md

3. Interview: Product Guidelines
   ├─ Questions: Brand voice, UI/UX principles
   └─ Generate: conductor/product-guidelines.md

4. Interview: Tech Stack
   ├─ Detect current stack from codebase
   ├─ Ask: Framework preferences, database, libraries
   └─ Generate: conductor/tech-stack.md

5. Interview: Workflow Preferences
   ├─ Questions: TDD approach, commit strategy, coverage target
   └─ Generate: conductor/workflow.md

6. Detect code style
   ├─ Analyze existing code
   └─ Generate: conductor/code_styleguides/*.md

7. Initialize tracking
   └─ Generate: conductor/tracks.md (empty registry)

8. Save state
   └─ Update: conductor/setup_state.json

9. Commit setup
   ├─ git add conductor/
   ├─ git commit -m "conductor(setup): Initialize Conductor context"
   └─ git notes add (detailed setup summary)
```

**Skills necessárias:**
- `AskUserQuestion` (para entrevistas)
- `Glob` + `Read` (para analisar codebase)
- `Write` (para gerar documentação)
- `Bash` (para git operations)

#### 2.2.3 **PlanningAgent** (Phase 2)
**Responsabilidade:** Criar spec e plan para novas tracks

**Subagentes:**
- **SpecGeneratorSubagent** → Cria especificação detalhada
- **PlanGeneratorSubagent** → Cria plano de implementação

**Workflow:**
```
1. Receive track description from user

2. Generate Track ID
   └─ Format: <feature_name>_YYYYMMDD (sanitized)

3. Create track directory
   └─ conductor/tracks/<track_id>/

4. Load context
   ├─ Read: product.md, tech-stack.md, workflow.md
   └─ Analyze: Related code in codebase

5. Interview: Detailed Requirements
   ├─ Questions: Acceptance criteria, edge cases, constraints
   └─ Refine: User requirements

6. Generate Specification (SpecGeneratorSubagent)
   ├─ Sections:
   │  ├─ Objetivo (What and Why)
   │  ├─ Escopo (Boundaries)
   │  ├─ Critérios de Aceite (Success criteria)
   │  └─ Considerações Técnicas (Tech constraints)
   └─ Write: conductor/tracks/<track_id>/spec.md

7. Generate Plan (PlanGeneratorSubagent)
   ├─ Analyze: Code architecture from codebase
   ├─ Break down: Phases → Tasks → Subtasks
   ├─ Estimate: Test requirements per task
   ├─ Structure:
   │  └─ ## Fase N: Name
   │     ├─ [ ] Tarefa: Description
   │     ├─ [ ] Tarefa: Create tests for X
   │     └─ [ ] Tarefa: Conductor - User Manual Verification
   └─ Write: conductor/tracks/<track_id>/plan.md

8. Create metadata
   └─ Write: conductor/tracks/<track_id>/metadata.json
      {
        "track_id": "...",
        "type": "feature|bugfix|refactor",
        "status": "planning",
        "created_at": "ISO timestamp",
        "updated_at": "ISO timestamp",
        "description": "..."
      }

9. Present to user for approval
   ├─ Show: spec.md and plan.md
   ├─ Ask: "Does this plan meet your expectations?"
   └─ If approved → Continue, else → Refine

10. Update tracks registry
    ├─ Read: conductor/tracks.md
    ├─ Add: ## [ ] Track: <Description>
    │       *Link: ./conductor/tracks/<track_id>/*
    └─ Write: conductor/tracks.md

11. Commit track creation
    ├─ git add conductor/tracks/<track_id>/
    ├─ git commit -m "conductor(track): Create track <track_id>"
    └─ git notes add (spec + plan summary)
```

**Skills necessárias:**
- `AskUserQuestion` (requirements clarification)
- `Task` with `Explore` subagent (code analysis)
- `Read` + `Write` (documentation)
- `Bash` (git operations)

#### 2.2.4 **ImplementationAgent** (Phase 3)
**Responsabilidade:** Executar o plan.md com TDD rigoroso

**Subagentes:**
- **TDDExecutorSubagent** → Ciclo Red-Green-Refactor
- **CheckpointVerifierSubagent** → Verificação de fases

**Workflow:**
```
1. Load active track
   ├─ Read: conductor/tracks/<track_id>/plan.md
   ├─ Read: conductor/tracks/<track_id>/spec.md
   └─ Load: product.md, tech-stack.md, workflow.md

2. Parse plan.md
   └─ Extract: Phases, Tasks, Current status

3. For each Phase (sequentially):
   ├─ For each Task:
   │  ├─ Mark task [~] in plan.md
   │  ├─ Commit plan update
   │  │
   │  ├─ DELEGATE TO TDDExecutorSubagent:
   │  │  ├─ RED Phase:
   │  │  │  ├─ Analyze task requirements
   │  │  │  ├─ Write failing unit tests
   │  │  │  ├─ Run tests → Confirm FAIL
   │  │  │  └─ If tests pass → ERROR (tests not strict enough)
   │  │  │
   │  │  ├─ GREEN Phase:
   │  │  │  ├─ Implement minimum code to pass
   │  │  │  ├─ Run tests → Confirm PASS
   │  │  │  └─ Run smoke test (python main.py)
   │  │  │
   │  │  ├─ REFACTOR Phase (optional):
   │  │  │  ├─ Improve code quality
   │  │  │  ├─ Run tests → Confirm PASS
   │  │  │  └─ Run smoke test again
   │  │  │
   │  │  └─ COVERAGE Phase:
   │  │     ├─ Run: pytest --cov=<module> --cov-report=term
   │  │     ├─ Verify: Coverage >95%
   │  │     └─ If <95% → Add more tests
   │  │
   │  ├─ Git commit code changes
   │  │  ├─ Stage all changes
   │  │  ├─ Commit: feat|fix|refactor(<scope>): <description>
   │  │  └─ Get commit SHA
   │  │
   │  ├─ Attach git note
   │  │  ├─ Content:
   │  │  │  Task: <task description>
   │  │  │  Summary: <what was done>
   │  │  │  Files Modified:
   │  │  │    - file1.py
   │  │  │    - file2.py
   │  │  │  Tests Added:
   │  │  │    - test_file1.py
   │  │  │  Coverage: XX%
   │  │  │  Rationale: <why this approach>
   │  │  └─ git notes add -m "<content>" <sha>
   │  │
   │  ├─ Update plan.md
   │  │  └─ Mark [x] with commit SHA (first 7 chars)
   │  │
   │  └─ Commit plan update
   │     └─ conductor(plan): Mark task '<task>' as complete
   │
   └─ PHASE CHECKPOINT (CheckpointVerifierSubagent):
      ├─ Identify changed files
      │  ├─ Find previous checkpoint SHA from plan.md
      │  ├─ Run: git diff --name-only <prev_checkpoint> HEAD
      │  └─ Filter: Only code files (exclude .md, .json)
      │
      ├─ Verify test coverage per file
      │  ├─ For each changed file:
      │  │  ├─ Check corresponding test file exists
      │  │  └─ If missing → CREATE test file
      │  └─ Run: pytest --cov=<changed_modules>
      │
      ├─ Run full test suite
      │  ├─ Announce command: "Running: pytest"
      │  ├─ Execute: pytest
      │  └─ If FAIL:
      │     ├─ Attempt fix (max 2 attempts)
      │     └─ If still fails → STOP, ask user
      │
      ├─ Generate manual verification plan
      │  ├─ Read: product.md, spec.md
      │  ├─ Identify: User-facing changes
      │  └─ Create step-by-step plan:
      │     **Manual Verification Steps:**
      │     1. **Start application:** python main.py
      │     2. **Navigate to:** <specific screen>
      │     3. **Confirm that:** <expected behavior>
      │
      ├─ Present to user
      │  ├─ Show: Manual verification plan
      │  └─ Ask: "Does this meet your expectations? (yes/no)"
      │
      ├─ Wait for user confirmation
      │  └─ If "no" → Ask for feedback, iterate
      │
      ├─ Create checkpoint commit
      │  └─ git commit --allow-empty -m "conductor(checkpoint): Checkpoint end of Phase <N>"
      │
      ├─ Attach verification report (git note)
      │  ├─ Content:
      │  │  Phase Verification Report: Phase <N>
      │  │  Automated Tests: Executed 'pytest'. Result: <X> passed.
      │  │  Coverage: <XX%> for <modules>
      │  │  Key Changes:
      │  │    - <change 1>
      │  │    - <change 2>
      │  │  Manual Verification: <steps>
      │  │  User Confirmation: Provided by user.
      │  └─ git notes add -m "<content>" <checkpoint_sha>
      │
      ├─ Update plan.md with checkpoint SHA
      │  └─ ## Fase N: Name [checkpoint: <7-char-sha>]
      │
      └─ Commit plan update
         └─ conductor(plan): Mark phase '<Phase N>' as complete

4. Track completion
   ├─ Update tracks.md
   │  └─ Mark track as [x]
   ├─ Move to archive
   │  └─ mv conductor/tracks/<track_id> conductor/archive/
   └─ Commit finalization
      ├─ conductor: Mark track as completed
      └─ Attach summary git note
```

**Skills necessárias:**
- `Task` with specialized subagents (TDD, testing)
- `Read` + `Write` + `Edit` (code e docs)
- `Bash` (pytest, git, smoke tests)
- `Grep` + `Glob` (file analysis)

---

## 🚀 Implementação Detalhada

### 3.1 Shared Services Layer

Antes de criar os agentes, precisamos de serviços compartilhados:

#### **FileManager Service**
```python
# conductor/services/file_manager.py
class FileManager:
    """Manages reading/writing Markdown and JSON files."""

    @staticmethod
    def read_md(file_path: str) -> str:
        """Read markdown file."""

    @staticmethod
    def write_md(file_path: str, content: str):
        """Write markdown file."""

    @staticmethod
    def read_json(file_path: str) -> dict:
        """Read JSON file."""

    @staticmethod
    def write_json(file_path: str, data: dict):
        """Write JSON file with proper formatting."""

    @staticmethod
    def parse_plan(plan_content: str) -> dict:
        """Parse plan.md into structured data."""
        # Returns: {phases: [{name, tasks: [{description, status, sha}]}]}

    @staticmethod
    def update_task_status(plan_content: str, task_line: int,
                          new_status: str, sha: str = None) -> str:
        """Update task status in plan.md content."""
```

#### **GitManager Service**
```python
# conductor/services/git_manager.py
class GitManager:
    """Manages Git operations (commits, notes, diff)."""

    @staticmethod
    def commit(message: str, files: list = None):
        """Create git commit with message."""

    @staticmethod
    def add_note(commit_sha: str, note_content: str):
        """Attach git note to commit."""

    @staticmethod
    def get_last_commit_sha(short: bool = True) -> str:
        """Get last commit SHA."""

    @staticmethod
    def diff_files(from_sha: str, to_sha: str = "HEAD") -> list:
        """Get list of changed files between commits."""

    @staticmethod
    def get_note(commit_sha: str) -> str:
        """Retrieve git note for commit."""
```

#### **TestRunner Service**
```python
# conductor/services/test_runner.py
class TestRunner:
    """Manages pytest execution and coverage analysis."""

    @staticmethod
    def run_tests(path: str = None, verbose: bool = True) -> dict:
        """Run pytest and return results."""
        # Returns: {passed: int, failed: int, output: str}

    @staticmethod
    def run_coverage(modules: list) -> dict:
        """Run pytest with coverage for specific modules."""
        # Returns: {coverage: float, report: str, missing_files: list}

    @staticmethod
    def verify_test_exists(code_file: str) -> bool:
        """Check if test file exists for code file."""
```

#### **SmokeTestRunner Service**
```python
# conductor/services/smoke_test_runner.py
class SmokeTestRunner:
    """Runs application smoke tests."""

    @staticmethod
    def run_application(timeout: int = 10) -> dict:
        """Start application and verify it runs without errors."""
        # Returns: {success: bool, error: str|None, output: str}
```

### 3.2 Agent Implementation Strategy

**Opção 1: Skills (Recomendado para integração com Claude Code)**

Criar skills customizadas que podem ser invocadas via `/conductor:*`:

```
.claude/
├─ skills/
   ├─ conductor-setup/
   │  ├─ skill.json
   │  └─ prompt.md
   ├─ conductor-newtrack/
   │  ├─ skill.json
   │  └─ prompt.md
   ├─ conductor-implement/
   │  ├─ skill.json
   │  └─ prompt.md
   └─ conductor-status/
      ├─ skill.json
      └─ prompt.md
```

**Opção 2: Task Tool com Subagentes Especializados**

Usar o Task tool do Claude Code para lançar agentes autônomos:

```python
# Exemplo de invocação
task = Task(
    subagent_type="conductor-implementation",
    description="Implement track feature_auth_20260110",
    prompt="""
    Execute the implementation workflow for track: feature_auth_20260110

    Context files:
    - conductor/tracks/feature_auth_20260110/spec.md
    - conductor/tracks/feature_auth_20260110/plan.md
    - conductor/product.md
    - conductor/workflow.md

    Follow strict TDD protocol from workflow.md.
    Create checkpoints at end of each phase.
    """,
    run_in_background=False
)
```

**Opção 3: Híbrida (RECOMENDADO)**

- **Skills** para comandos de alto nível (`/conductor:setup`, `/conductor:newTrack`)
- **Task Tool** para execução de implementação longa (`/conductor:implement`)
- **Shared Services** em Python para lógica reutilizável

---

## 📝 Exemplo de Fluxo End-to-End

### Cenário: Adicionar autenticação OAuth ao projeto

```bash
# ===== FASE 1: SETUP (Já executado) =====
# $ /conductor:setup
# [Setup completo anteriormente]

# ===== FASE 2: PLANNING =====
$ /conductor:newTrack "Add OAuth authentication with Google and GitHub providers"

> ConductorOrchestrator:
  ├─ Delegating to PlanningAgent...
  └─ PlanningAgent activated

> PlanningAgent:
  ├─ Generating track ID: "add_oauth_auth_20260111"
  ├─ Creating directory: conductor/tracks/add_oauth_auth_20260111/
  ├─ Loading context:
  │  ├─ ✓ product.md
  │  ├─ ✓ product-guidelines.md
  │  ├─ ✓ tech-stack.md
  │  └─ ✓ workflow.md
  └─ Analyzing codebase for authentication patterns...

> InterviewSubagent (via AskUserQuestion):

  **Question 1:** Which OAuth providers should we support?
  Options:
    [x] Google
    [x] GitHub
    [ ] Facebook
    [ ] Microsoft

  **Question 2:** Where should user sessions be stored?
  Options:
    (*) Database (PostgreSQL)
    ( ) In-memory (Redis)
    ( ) JWT tokens only

  **Question 3:** What should happen for unauthenticated users?
  Options:
    (*) Redirect to /login
    ( ) Show 401 error
    ( ) Allow limited access

> SpecGeneratorSubagent:
  ├─ Generating specification...
  └─ Created: conductor/tracks/add_oauth_auth_20260111/spec.md

> PlanGeneratorSubagent:
  ├─ Analyzing current architecture...
  ├─ Identified: No authentication system exists
  ├─ Planning phases:
  │  ├─ Phase 1: Setup OAuth libraries and configuration
  │  ├─ Phase 2: Create authentication service
  │  ├─ Phase 3: Integrate with UI
  │  └─ Phase 4: Testing and validation
  └─ Created: conductor/tracks/add_oauth_auth_20260111/plan.md

> PlanningAgent:
  ├─ Presenting plan to user...
  │
  │  ╔══════════════════════════════════════════════════════╗
  │  ║  SPECIFICATION PREVIEW                               ║
  │  ╚══════════════════════════════════════════════════════╝
  │
  │  ## Objetivo
  │  Implementar sistema de autenticação OAuth2 com suporte
  │  para Google e GitHub, permitindo login seguro e
  │  rastreável de usuários.
  │
  │  ## Escopo
  │  - OAuth2 flow (authorization code)
  │  - User model com provider tracking
  │  - Session management em PostgreSQL
  │  - Protected routes middleware
  │
  │  ## Critérios de Aceite
  │  - Usuários podem fazer login via Google/GitHub
  │  - Sessões persistem entre restarts
  │  - Logout limpa sessão corretamente
  │  - Testes cobrem >95% do código
  │
  │  ╔══════════════════════════════════════════════════════╗
  │  ║  PLAN PREVIEW                                        ║
  │  ╚══════════════════════════════════════════════════════╝
  │
  │  ## Fase 1: Setup OAuth libraries
  │  - [ ] Install authlib and dependencies
  │  - [ ] Create OAuth configuration module
  │  - [ ] Write tests for config validation
  │
  │  ## Fase 2: Authentication Service
  │  - [ ] Create User model
  │  - [ ] Implement OAuth flow handlers
  │  - [ ] Write comprehensive unit tests
  │  - [ ] Conductor - User Manual Verification 'Fase 2'
  │
  │  ...
  │
  └─ **Does this plan meet your expectations? (yes/no)**

> User: yes

> PlanningAgent:
  ├─ Updating conductor/tracks.md...
  ├─ Committing track creation...
  │  └─ git commit -m "conductor(track): Create track add_oauth_auth_20260111"
  └─ ✓ Track created successfully!

# ===== FASE 3: IMPLEMENTATION =====
$ /conductor:implement

> ConductorOrchestrator:
  ├─ Loading active tracks...
  ├─ Found: add_oauth_auth_20260111 (status: planning)
  └─ Delegating to ImplementationAgent...

> ImplementationAgent:
  ├─ Loading plan: conductor/tracks/add_oauth_auth_20260111/plan.md
  ├─ Parsing: 4 phases, 12 tasks identified
  └─ Starting implementation...

  ┌──────────────────────────────────────────────────────────┐
  │ FASE 1: Setup OAuth libraries                            │
  └──────────────────────────────────────────────────────────┘

  > Task 1/3: Install authlib and dependencies
    ├─ Marking [~] in plan.md
    ├─ Committing plan update
    │
    ├─ TDDExecutorSubagent:
    │  ├─ RED: Writing failing test...
    │  │  └─ Created: tests/test_oauth_config.py
    │  │     test_authlib_import() → FAIL ✓
    │  │
    │  ├─ GREEN: Installing dependencies...
    │  │  └─ pip install authlib requests
    │  │     test_authlib_import() → PASS ✓
    │  │
    │  └─ COVERAGE: 100% (new module)
    │
    ├─ Smoke test: python main.py → ✓ PASS
    ├─ Committing: feat(auth): Install authlib for OAuth2
    ├─ Attaching git note with summary
    ├─ Marking [x] abc1234 in plan.md
    └─ Committing plan update

  > Task 2/3: Create OAuth configuration module
    ├─ Marking [~] in plan.md
    │
    ├─ TDDExecutorSubagent:
    │  ├─ RED: Writing tests...
    │  │  └─ Created: tests/unit/test_oauth_config.py
    │  │     - test_load_google_config()
    │  │     - test_load_github_config()
    │  │     - test_invalid_config_raises_error()
    │  │     All tests → FAIL ✓
    │  │
    │  ├─ GREEN: Implementing...
    │  │  └─ Created: aoi_lib/oauth_config.py
    │  │     class OAuthConfig:
    │  │       def load_provider(provider: str) -> dict
    │  │     All tests → PASS ✓
    │  │
    │  ├─ REFACTOR: Improving error messages...
    │  │  └─ Tests still → PASS ✓
    │  │
    │  └─ COVERAGE: pytest --cov=aoi_lib.oauth_config
    │     Coverage: 98% ✓
    │
    ├─ Smoke test: python main.py → ✓ PASS
    ├─ Committing: feat(auth): Add OAuth configuration module
    ├─ Attaching git note
    ├─ Marking [x] def5678 in plan.md
    └─ Committing plan update

  > Task 3/3: Write tests for config validation
    [... similar TDD flow ...]

  ┌──────────────────────────────────────────────────────────┐
  │ PHASE 1 CHECKPOINT                                       │
  └──────────────────────────────────────────────────────────┘

  > CheckpointVerifierSubagent:
    ├─ Identifying changed files (git diff)...
    │  └─ Found: 3 code files, 3 test files
    │
    ├─ Verifying test coverage...
    │  └─ All files have corresponding tests ✓
    │
    ├─ Running full test suite...
    │  ├─ Command: pytest
    │  └─ Result: 45 passed ✓
    │
    ├─ Generating manual verification plan...
    │
    │  **Manual Verification Steps:**
    │  1. **Verify dependencies installed:**
    │     ```bash
    │     pip list | grep authlib
    │     ```
    │     **Expected:** authlib 1.3.0 listed
    │
    │  2. **Test configuration loading:**
    │     ```python
    │     from aoi_lib.oauth_config import OAuthConfig
    │     config = OAuthConfig.load_provider('google')
    │     print(config)
    │     ```
    │     **Expected:** Dictionary with client_id, client_secret, etc.
    │
    └─ **Does this meet your expectations? (yes/no)**

> User: yes

> CheckpointVerifierSubagent:
  ├─ Creating checkpoint commit...
  │  └─ conductor(checkpoint): Checkpoint end of Phase 1
  ├─ Attaching verification report (git note)
  ├─ Updating plan.md: [checkpoint: a1b2c3d]
  └─ Committing plan update

  ✓ Phase 1 complete! Proceeding to Phase 2...

[... Continua com Fases 2, 3, 4 ...]

# ===== APÓS CONCLUSÃO DE TODAS AS FASES =====

> ImplementationAgent:
  ├─ All phases completed successfully!
  ├─ Updating tracks.md (mark [x])
  ├─ Moving track to archive...
  │  └─ mv conductor/tracks/add_oauth_auth_20260111 conductor/archive/
  └─ Committing: conductor: Mark track as completed

✓ Track 'add_oauth_auth_20260111' completed!

# ===== CONSULTAR STATUS =====
$ /conductor:status

> Tracks Overview:
  ✓ add_oauth_auth_20260111 (Completed 2026-01-11)
  ○ refactor_ui_components_20260110 (In Progress - Phase 2/4)
  ○ bugfix_camera_timeout_20260109 (Planning)
```

---

## ⚙️ Configuração e Extensibilidade

### 4.1 Configuration File

```json
// conductor/config.json
{
  "version": "1.0.0",
  "settings": {
    "coverage_threshold": 95,
    "smoke_test_timeout": 10,
    "max_checkpoint_retry": 2,
    "auto_archive": true,
    "git_notes_enabled": true,
    "verification_required": true
  },
  "templates": {
    "workflow": "conductor/templates/workflow.md",
    "spec": "conductor/templates/spec.md",
    "plan": "conductor/templates/plan.md"
  },
  "hooks": {
    "pre_task": null,
    "post_task": null,
    "pre_checkpoint": null,
    "post_checkpoint": null
  }
}
```

### 4.2 Custom Templates

Usuários podem customizar templates em `conductor/templates/`:

```markdown
<!-- conductor/templates/spec.md -->
# Especificação da Track: {{track_name}}

## Contexto
{{context}}

## Objetivo
{{objective}}

## Escopo
{{scope}}

## Critérios de Aceite
{{acceptance_criteria}}

## Considerações Técnicas
{{technical_notes}}

## Riscos e Mitigações
{{risks}}
```

---

## 🎓 Comparação com Gemini CLI Conductor

| Aspecto | Gemini CLI Conductor | Nossa Proposta |
|---------|---------------------|----------------|
| **Setup** | `/conductor:setup` command | ✅ Idêntico com skills |
| **Planning** | `/conductor:newTrack` | ✅ Idêntico + melhor análise de código |
| **Implementation** | `/conductor:implement` | ✅ Idêntico + TDD rigoroso |
| **Checkpoints** | Manual verification | ✅ Idêntico + smoke tests automáticos |
| **Git Integration** | Basic commits | ✅ **SUPERIOR:** Git notes detalhados |
| **Test Coverage** | Optional | ✅ **SUPERIOR:** Obrigatório >95% |
| **Smoke Tests** | Not mentioned | ✅ **SUPERIOR:** Automático em cada task |
| **Architecture Analysis** | Basic | ✅ **SUPERIOR:** Explore agent para análise profunda |
| **Rollback** | `/conductor:revert` | ✅ Idêntico (a implementar) |
| **Status** | `/conductor:status` | ✅ Idêntico (a implementar) |

**Diferenciais da Nossa Solução:**
1. ✨ **Cobertura obrigatória >95%** vs. Gemini (opcional)
2. ✨ **Git notes detalhados** em cada commit e checkpoint
3. ✨ **Smoke tests automáticos** após cada task
4. ✨ **Análise arquitetural profunda** via Explore agent
5. ✨ **Integração nativa com Claude Code** (tools existentes)

---

## 📊 Métricas de Sucesso

### KPIs para Avaliar o Sistema

1. **Setup Efficiency**
   - Tempo para completar setup inicial: < 10 minutos
   - Documentação base completa: 100%

2. **Planning Accuracy**
   - Specs aprovadas na primeira tentativa: >80%
   - Plans sem revisões: >70%

3. **Implementation Quality**
   - Cobertura de testes: >95%
   - Smoke tests passando: 100%
   - Checkpoints com falha: <5%

4. **Developer Experience**
   - Satisfação com clareza das tracks: >4/5
   - Facilidade de retomar trabalho: >4/5
   - Confiança no código gerado: >4/5

5. **Auditability**
   - Commits com git notes: 100%
   - Checkpoints documentados: 100%
   - Rastreabilidade task → commit: 100%

---

## 🚀 Roadmap de Implementação

### Phase 1: Foundation (Week 1)
- [ ] Implementar Shared Services Layer
  - [ ] FileManager
  - [ ] GitManager
  - [ ] TestRunner
  - [ ] SmokeTestRunner
- [ ] Criar estrutura de skills base
- [ ] Testes unitários para services

### Phase 2: Setup Agent (Week 2)
- [ ] Implementar SetupAgent
- [ ] Criar InterviewSubagent
- [ ] Templates para setup docs
- [ ] Skill: `/conductor:setup`
- [ ] Testes end-to-end do setup

### Phase 3: Planning Agent (Week 3)
- [ ] Implementar PlanningAgent
- [ ] Criar SpecGeneratorSubagent
- [ ] Criar PlanGeneratorSubagent
- [ ] Skill: `/conductor:newTrack`
- [ ] Templates para spec e plan
- [ ] Testes end-to-end do planning

### Phase 4: Implementation Agent (Week 4-5)
- [ ] Implementar ImplementationAgent
- [ ] Criar TDDExecutorSubagent
- [ ] Criar CheckpointVerifierSubagent
- [ ] Skill: `/conductor:implement`
- [ ] Testes end-to-end da implementação

### Phase 5: Supporting Features (Week 6)
- [ ] Skill: `/conductor:status`
- [ ] Skill: `/conductor:revert`
- [ ] Skill: `/conductor:update`
- [ ] Dashboard de progresso
- [ ] Documentação completa

### Phase 6: Polish & Optimization (Week 7)
- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] User experience refinements
- [ ] Comprehensive documentation
- [ ] Video tutorials

---

## 🎯 Próximos Passos Imediatos

Para começar a implementação **HOJE**:

### Opção A: Protótipo Rápido (Recomendado)
1. Criar skill básica `/conductor:setup` manualmente
2. Testar fluxo de entrevistas com AskUserQuestion
3. Validar geração de documentação
4. Iterar baseado em feedback

### Opção B: Implementação Completa
1. Começar com Shared Services Layer
2. Criar testes para cada serviço
3. Implementar SetupAgent primeiro
4. Expandir gradualmente

### Opção C: Análise Adicional
1. Estudar mais a fundo o Gemini CLI Conductor
2. Analisar outros sistemas similares
3. Refinar a arquitetura proposta
4. Criar POC em Python puro

**Minha Recomendação:** **Opção A** - Protótipo rápido para validar conceito e obter feedback real antes de investir em implementação completa.

---

## 📚 Referências

- [Conductor: Gemini CLI Extension](https://github.com/gemini-cli-extensions/conductor)
- [Google Developers Blog: Introducing Conductor](https://developers.googleblog.com/conductor-introducing-context-driven-development-for-gemini-cli/)
- [Medium: Trying Out Conductor](https://medium.com/google-cloud/trying-out-the-new-conductor-extension-in-gemini-cli-0801f892e2db)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Test-Driven Development Best Practices](https://martinfowler.com/bliki/TestDrivenDevelopment.html)

---

**Status:** Pronto para revisão e aprovação
**Próxima Ação:** Decisão sobre abordagem de implementação
