# Project Organization Guidelines

**Universal recommendations for maintaining a clean, professional project structure that scales well and is easy to navigate for both developers and AI assistants.**

---

## 📋 Table of Contents
1. [Root Directory: Keep It Minimal](#root-directory-keep-it-minimal)
2. [Documentation Structure](#documentation-structure-docs)
3. [Development Tools](#development-tools-tools-scripts)
4. [Test Organization](#test-organization-tests)
5. [Universal Principles](#universal-principles)
6. [Examples: Good vs Bad](#examples-good-vs-bad-organization)

---

## 🗂️ Root Directory: Keep It Minimal

### Principle
The root directory should contain **only essential files and directories** that serve as entry points to understand and use the project.

### ✅ Recommended Files in Root

#### Essential Guides (First Contact)
- `README.md` - Project overview, quick start, and basic usage
- `CLAUDE.md` - AI/developer guidance (if using Claude Code)
- `CONTRIBUTING.md` - Contribution guidelines
- `CHANGELOG.md` - Version history and changes
- `LICENSE` - License information

#### Configuration
- `.gitignore` - Git ignore rules
- `.env.example` - Environment variables template
- `config.*` - Application configuration files

#### Build & Dependencies
- `requirements*.txt`, `package.json`, `pom.xml`, etc. - Dependency declarations
- `setup.py`, `pyproject.toml`, `Makefile` - Build automation
- `Dockerfile`, `docker-compose.yml` - Container definitions

#### Core Directories
- `src/` or `app/` or `lib/` - Source code
- `tests/` or `test/` - Test suite
- `docs/` - Documentation
- `tools/` or `scripts/` - Development utilities

### ❌ Avoid in Root Directory

#### Documentation Clutter
- **Implementation plans, analysis reports, design docs** → `docs/architecture/`
- **Meeting notes, brainstorming** → `docs/meetings/` or remove
- **Temporary logs** → `docs/logs/` or remove

#### Code Files
- **Test files** → `tests/`
- **Utility scripts** → `tools/` or `scripts/`
- **One-off experiments** → `sandbox/` or remove

#### Generated/Temporary
- **Build artifacts** → `build/`, `dist/`, `out/`
- **Dependencies** → `.venv/`, `node_modules/`, `vendor/`
- **IDE configs** → `.idea/`, `.vscode/` (in .gitignore)

---

## 📚 Documentation Structure (`docs/`)

### Principle
Organize documentation **by purpose and audience**, not by format.

### Recommended Structure
```
docs/
├── guides/           # How-to guides and tutorials
├── api/              # API documentation
├── architecture/     # System design and architecture
├── development/      # Development workflow and setup
├── deployment/       # Deployment and operations
├── troubleshooting/  # Common issues and solutions
├── meetings/         # Meeting notes and decisions
└── changelog/        # Historical change logs
```

### Quick Reference

| Content Type | Location | Example |
|--------------|----------|---------|
| **Getting started** | `README.md` (root) | Quick start guide |
| **API reference** | `docs/api/` | Endpoint documentation |
| **Architecture** | `docs/architecture/` | System design docs |
| **Tutorials** | `docs/guides/` | Step-by-step guides |
| **Deployment** | `docs/deployment/` | Production setup |
| **Development** | `docs/development/` | Contributing workflow |
| **Analysis/Plans** | `docs/architecture/` | Design docs, ADRs |
| **Meeting notes** | `docs/meetings/` or remove | Decision records |
| **Historical** | `docs/changelog/` or remove | Old implementation plans |

---

## 🛠️ Development Tools (`tools/`, `scripts/`)

### Principle
Separate automation and utility scripts from application code.

### Recommended Structure
```
tools/
├── setup/           # Installation and setup scripts
├── development/     # Development helpers (linting, formatting)
├── testing/         # Test utilities and fixtures
├── deployment/      # Build and deployment scripts
└── maintenance/     # Database migrations, cleanup scripts
```

### Examples of Tool Scripts
- **Generators** (scaffolding, boilerplate)
- **Migration scripts** (data, schema)
- **Build automation** (compilation, packaging)
- **Development helpers** (linters, formatters)
- **Test utilities** (test data generation, fixtures)

---

## 🧪 Test Organization (`tests/`)

### Principle
Mirror source structure with clear separation of test types.

### Recommended Structure
```
tests/
├── unit/            # Fast, isolated tests
├── integration/     # Component interaction tests
├── e2e/             # Full workflow tests
├── performance/     # Load and benchmark tests
└── fixtures/        # Test data and mocks
```

### Test Type Guidelines

| Test Type | Purpose | Speed | Dependencies |
|-----------|---------|-------|--------------|
| **Unit** | Test individual functions/classes | Fast | None (mocked) |
| **Integration** | Test component interactions | Medium | Real dependencies |
| **E2E** | Test complete workflows | Slow | Full system |
| **Performance** | Test load and benchmarks | Variable | None/Full |

---

## 🎯 Universal Principles

### 1. Root = First Impression
- Root directory is the project's "face"
- Should be **scannable in < 10 seconds**
- Only files that help newcomers get started

### 2. Documentation by Purpose
- Group by **WHO** needs it (users, developers, operators)
- Not by format (all .md files together)
- Make navigation intuitive

### 3. Separation of Concerns
- Application code ≠ Tests ≠ Tools ≠ Docs
- Clear boundaries prevent confusion
- Each directory has a **single responsibility**

### 4. Scalability
- Structure should work for **10 files or 10,000**
- Avoid flat organization beyond ~10 items
- Use subdirectories to group related content

### 5. Convention over Invention
- Use standard structures (`src/`, `tests/`, `docs/`)
- Follow framework conventions when applicable
- Make it predictable for newcomers

---

## 📊 Examples: Good vs Bad Organization

### ✅ GOOD - Clean Root
```
project/
├── README.md              ← Quick overview
├── CLAUDE.md              ← Developer/AI guidance
├── CONTRIBUTING.md        ← How to contribute
├── .gitignore
├── package.json
├── src/                   ← Application code
├── tests/                 ← All tests
├── docs/                  ← All documentation
└── tools/                 ← Development utilities
```

**Characteristics:**
- ✅ Scannable in < 10 seconds
- ✅ Clear separation of concerns
- ✅ Entry points clearly visible
- ✅ Professional appearance

### ❌ BAD - Cluttered Root
```
project/
├── README.md
├── IMPLEMENTATION_PLAN.md         ← Should be in docs/
├── ANALYSIS_REPORT.md             ← Should be in docs/
├── test_integration.py            ← Should be in tests/
├── generate_fixtures.py           ← Should be in tools/
├── meeting_notes_2024.md          ← Should be in docs/ or removed
├── legacy_script_v1.py            ← Should be removed or archived
├── temp_debug_log.txt             ← Should be removed
└── [50+ markdown files...]        ← Organization nightmare
```

**Problems:**
- ❌ Not scannable (too many files)
- ❌ Mixed concerns (docs, tests, code all mixed)
- ❌ No clear entry points
- ❌ Temporary files not cleaned up

---

## 🔍 Checklist for New Projects

Use this checklist when starting a new project:

### Root Directory Setup
- [ ] Create `README.md` with project overview
- [ ] Create `.gitignore` appropriate for language/stack
- [ ] Add dependency file (`package.json`, `requirements.txt`, etc.)
- [ ] Create core directories: `src/`, `tests/`, `docs/`, `tools/`
- [ ] Add `CLAUDE.md` if using Claude Code
- [ ] Add `CONTRIBUTING.md` for team projects
- [ ] Add `LICENSE` if open source

### Documentation Structure
- [ ] Create `docs/guides/` for tutorials
- [ ] Create `docs/architecture/` for design docs
- [ ] Create `docs/api/` for API documentation
- [ ] Create `docs/development/` for workflow docs

### Test Structure
- [ ] Create `tests/unit/` for unit tests
- [ ] Create `tests/integration/` for integration tests
- [ ] Create `tests/fixtures/` for test data

### Tools Structure
- [ ] Create `tools/setup/` for setup scripts
- [ ] Create `tools/development/` for dev helpers
- [ ] Create `tools/deployment/` for build/deploy scripts

---

## 📖 Additional Resources

### Related Standards
- [Standard Project Structure (Python)](https://docs.python-guide.org/writing/structure/)
- [Node.js Best Practices](https://github.com/goldbergyoni/nodebestpractices)
- [Java Project Structure (Maven)](https://maven.apache.org/guides/introduction/introduction-to-the-standard-directory-layout.html)

### Documentation Tools
- **Markdown** - Simple, universal format
- **Sphinx** - Python documentation generator
- **Docusaurus** - Modern documentation sites
- **Swagger/OpenAPI** - API documentation

---

## 🎓 Key Takeaways

1. **Less is more** in root directory - only essential files
2. **Organize by purpose**, not by file format
3. **Separate concerns** - code, tests, docs, tools each have their place
4. **Think scalability** - structure should grow gracefully
5. **Follow conventions** - use standard patterns others recognize
6. **Keep it clean** - remove temporary files, archive old work
7. **Document decisions** - use `docs/architecture/` for design docs
8. **Make it scannable** - newcomers should understand structure in < 10 seconds

---

**Last Updated:** 2025-01-08
**Version:** 1.0

*These guidelines are applicable to any programming language, framework, or project size. Adapt as needed for your specific context.*
