# Documentation

This directory contains all project documentation, organized by purpose and audience.

## Structure

### guides/
**Audience:** Developers and operators
**Content:** How-to guides, tutorials, and procedural documentation
**Examples:**
- `testing_guide.md` - Testing best practices
- `test_implementation_plan.md` - Test implementation roadmap
- `fluxo_usuario_questionario.md` - User workflow documentation

### architecture/
**Audience:** Developers and architects
**Content:** System design, technical specifications, integration analysis
**Examples:**
- `ANALISE_INTEGRACAO_MOVEMENT_CONTROLS.md` - Movement controls architecture
- `TENSION_COORDINATOR.md` - Tension measurement system design

### meetings/
**Audience:** Project stakeholders
**Content:** Meeting notes, client reports, decision records
**Examples:**
- `RELATORIO_CLIENTE_3_SEMANAS.md` - 3-week client status report

### reports/
**Audience:** Technical team and management
**Content:** Technical reports, implementation summaries
**Examples:**
- `RELATORIO_IMPLEMENTACAO_3_SEMANAS.md` - 3-week implementation report

### history/
**Audience:** Developers and maintainers
**Content:** Development history, changelogs, refactoring records
**Examples:**
- `BACKLOG.md` - Task backlog
- `CHANGELOG_2025-12-12.md` - Version changelog
- `REFACTORING_*.md` - Refactoring session logs (30+ files)

### External articles and manuals
**Audience:** Operators, maintenance staff, and project stakeholders
**Content:** Articles, technical manuals, hardware specifications, and operator procedures
**Location:** `Documentos e Builds/Arquivos fora do repositorio/Tensiometro/`, outside this repository

## Quick Navigation

**For new developers:**
1. Start with `../README.md` (project root)
2. Read `guides/testing_guide.md` for testing practices
3. Check `architecture/` for system design

**For operators:**
1. Start with the operator manual in the external `Tensiometro/Manuais/` directory
2. See that same directory for hardware documentation
3. Check `guides/` for procedural guides

**For project status:**
1. Review `history/BACKLOG.md` for pending tasks
2. Check latest `CHANGELOG_*.md` for recent changes
3. See `reports/` for implementation progress

## Adding Documentation

When adding new documentation:

1. **Choose the right subdirectory:**
   - Tutorial/How-to → `guides/`
   - Design/Architecture → `architecture/`
   - Meeting notes → `meetings/`
   - Technical reports → `reports/`
   - Historical records → `history/`

2. **Use descriptive filenames:**
   - Prefer `descriptive_name.md` over `doc1.md`
   - Use kebab-case or snake_case consistently
   - Include date for time-sensitive documents (YYYY-MM-DD)

3. **Add to this README:**
   - Update relevant section above
   - Include brief description of content

4. **Cross-reference:**
   - Add links from `../CLAUDE.md` if significant
   - Update `See Also` sections in related docs

## Naming Conventions

- **Guides:** `topic_guide.md` (e.g., `testing_guide.md`)
- **Architecture:** `UPPERCASE_ANALYSIS.md` or `Component_Design.md`
- **Meetings:** `YYYY-MM-DD_topic.md` or `REPORT_TYPE_DURATION.md`
- **Reports:** `REPORT_TYPE_YYYY-MM-DD.md`
- **History:** Preserve existing naming, use descriptive names for new files

## Maintenance

- **Archive old files:** Move outdated docs to `history/`
- **Update dates:** Keep timestamps current in time-sensitive docs
- **Remove duplicates:** Consolidate redundant documentation
- **Link, don't duplicate:** Use links instead of copying content

---

**Last Updated:** 2026-01-08
**Standard:** Follow [PROJECT_ORGANIZATION_GUIDELINES.md](../PROJECT_ORGANIZATION_GUIDELINES.md)
