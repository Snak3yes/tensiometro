# Implementation Plan: Engineering Wizard Free Navigation Mode

**Track ID:** engineering_free_navigation_20260116
**Status:** Pending
**Est. Duration:** 1-2 days
**Phases:** 5
**Tasks:** 23

---

## Phase 1: Setup and Configuration (Foundation)

**Objective:** Establish configuration infrastructure for free navigation mode

**Duration:** 2-3 hours

### Tasks

#### 1.1 Configuration Schema
- [ ] Add `engineering_wizard` section to `aoi_config.json` template
- [ ] Define `free_navigation_enabled` boolean field (default: false)
- [ ] Define `last_used_mode` string field for tracking
- [ ] Document configuration schema in CLAUDE.md

#### 1.2 AOIConfigManager Extension
- [ ] Implement `get_free_navigation_enabled() -> bool`
- [ ] Implement `set_free_navigation_enabled(enabled: bool) -> None`
- [ ] Add default value handling (false if key missing)
- [ ] Add configuration validation
- [ ] Write unit tests (4 tests)
  - Test get when enabled
  - Test get when disabled
  - Test get when key missing (default)
  - Test set and persistence

#### 1.3 AuthConfigManager Integration
- [ ] Add `get_free_navigation_enabled()` wrapper method
- [ ] Add `set_free_navigation_enabled()` wrapper method
- [ ] Add password confirmation requirement
- [ ] Add audit logging for setting changes
- [ ] Write unit tests (3 tests)
  - Test get wrapper
  - Test set wrapper with password
  - Test audit logging

**Success Criteria:**
- Configuration can be loaded and saved correctly
- Default value is false when key missing
- Unit tests pass (7 tests)
- Configuration persists across application restarts

---

## Phase 2: Settings UI Integration

**Objective:** Add free navigation toggle to Authentication Settings dialog

**Duration:** 3-4 hours

### Tasks

#### 2.1 AuthenticationSettingsDialog UI
- [ ] Add "Engineering Settings" group box (below authentication settings)
- [ ] Add checkbox: "Habilitar Navegação Livre (Testing/Debug)"
- [ ] Add description label explaining the feature
- [ ] Add warning label: "⚠️ Modo de desenvolvimento - permite ignorar validações"
- [ ] Apply styling (warning color, bold text)
- [ ] Position UI elements in layout
- [ ] Add tooltips for help

#### 2.2 Settings Dialog Logic
- [ ] Load `free_navigation_enabled` setting on dialog open
- [ ] Connect checkbox state change to handler
- [ ] Implement save handler with password confirmation
- [ ] Validate user role (engineering+ only)
- [ ] Disable checkbox for operator/quality roles
- [ ] Show/hide checkbox based on current user role
- [ ] Add error handling for save failures

#### 2.3 Access Control
- [ ] Integrate with existing RoleManager
- [ ] Check user role before showing checkbox
- [ ] Require password confirmation to save
- [ ] Add audit log entry on setting change
- [ ] Log: "Free navigation enabled by {user} at {timestamp}"

#### 2.4 Testing Settings Dialog
- [ ] Write unit tests (5 tests)
  - Test checkbox shows for engineering role
  - Test checkbox hidden for operator role
  - Test save with correct password
  - Test save fails with wrong password
  - Test audit logging
- [ ] Write integration tests (3 tests)
  - Test complete workflow (load → change → save)
  - Test configuration persistence
  - Test role-based visibility

**Success Criteria:**
- Checkbox appears for engineering+ users only
- Setting persists to `aoi_config.json`
- Password confirmation required
- Audit log entry created
- Unit tests pass (8 tests)
- Integration tests pass (3 tests)

---

## Phase 3: EngineeringWizardDialog Navigation Logic

**Objective:** Modify wizard navigation to respect free navigation mode

**Duration:** 4-5 hours

### Tasks

#### 3.1 Dialog Initialization
- [ ] Add `free_navigation_mode` property to EngineeringWizardDialog
- [ ] Load configuration in `__init__()` via AOIConfigManager
- [ ] Store mode setting as instance variable
- [ ] Pass mode to tab widgets if needed

#### 3.2 Tab Creation Logic
- [ ] Modify `_create_tabs()` to check navigation mode
- [ ] When free navigation enabled: skip `setTabEnabled(i, False)` for tabs 1-6
- [ ] When free navigation disabled: use current logic (sequential enable)
- [ ] Add comment explaining both code paths
- [ ] Test both modes manually

#### 3.3 Next Button Handler
- [ ] Modify `_on_next()` to check navigation mode
- [ ] When free navigation enabled: skip validation checks
- [ ] When free navigation disabled: use current validation logic
- [ ] Preserve all existing validation behavior in normal mode
- [ ] Add logging for mode-specific behavior

#### 3.4 Tab Changed Handler
- [ ] Modify `_on_tab_changed()` to check navigation mode
- [ ] When free navigation enabled: allow any tab change
- [ ] When free navigation disabled: use current logic
- [ ] Update progress bar based on actual tab (not validation state)

#### 3.5 Visual Indicators
- [ ] Add "🔓 Navegação Livre" badge to dialog title when mode active
- [ ] Add status indicator in progress bar area
- [ ] Update title when mode changes (if dialog is open)
- [ ] Add tooltip to tab widget showing current mode
- [ ] Optional: Change tab color slightly when mode active

#### 3.6 Validation State Tracking
- [ ] Ensure validation state continues to be tracked
- [ ] Tab completion indicators (✓) still reflect actual state
- [ ] Validation signals still connect and emit
- [ ] State management unchanged (only navigation changes)

#### 3.7 Testing Navigation Logic
- [ ] Write unit tests (6 tests)
  - Test tab creation with free navigation enabled
  - Test tab creation with free navigation disabled
  - Test next button with free navigation enabled
  - Test next button with free navigation disabled
  - Test tab changed with free navigation enabled
  - Test tab changed with free navigation disabled
- [ ] Write integration tests (4 tests)
  - Test complete workflow in free navigation mode
  - Test complete workflow in normal mode
  - Test mode switching during wizard session
  - Test validation state tracking in both modes

**Success Criteria:**
- Free navigation mode enables all 7 tabs immediately
- Normal navigation mode preserves current behavior
- Visual indicators clearly show active mode
- Validation state tracking unchanged
- Unit tests pass (6 tests)
- Integration tests pass (4 tests)

---

## Phase 4: Finish Button Validation

**Objective:** Ensure finish button validates all data regardless of mode

**Duration:** 1-2 hours

### Tasks

#### 4.1 Finish Button Handler
- [ ] Verify `_on_finish()` validates all tabs
- [ ] Ensure validation runs in both navigation modes
- [ ] Confirm validation summary shows all errors
- [ ] Test with incomplete data in free navigation mode
- [ ] Test with incomplete data in normal mode
- [ ] Verify both modes prevent saving incomplete programs

#### 4.2 Validation Summary
- [ ] Ensure validation message lists all invalid tabs
- [ ] Test with multiple invalid tabs
- [ ] Test with single invalid tab
- [ ] Verify user-friendly error messages

#### 4.3 Testing Finish Validation
- [ ] Write unit tests (4 tests)
  - Test finish with all valid (both modes)
  - Test finish with some invalid (free navigation mode)
  - Test finish with some invalid (normal mode)
  - Test validation summary content

**Success Criteria:**
- Finish button validates all tabs in both modes
- Cannot save incomplete programs in either mode
- Validation summary is clear and helpful
- Unit tests pass (4 tests)

---

## Phase 5: MainWindow Integration and E2E Testing

**Objective:** Integrate feature with main window and test complete workflows

**Duration:** 2-3 hours

### Tasks

#### 5.1 MainWindow Integration
- [ ] Update `open_wizard()` in MainWindowEngineeringWorkflow
- [ ] Load free navigation configuration before opening dialog
- [ ] Pass configuration to EngineeringWizardDialog if needed
- [ ] Ensure configuration is fresh (not cached from startup)

#### 5.2 Configuration Loading on Startup
- [ ] Verify AOIConfigManager loads configuration on app startup
- [ ] Test configuration persists across app restarts
- [ ] Test default value handling with old config files
- [ ] Test migration from config without the key

#### 5.3 End-to-End Testing
- [ ] Write E2E test for free navigation workflow
  - Enable free navigation mode
  - Open Engineering Wizard
  - Navigate directly to Tab 5 (Alignment)
  - Verify no validation warnings
  - Complete all tabs
  - Verify finish validation works
  - Save program
- [ ] Write E2E test for normal navigation workflow
  - Disable free navigation mode
  - Open Engineering Wizard
  - Verify tabs are locked
  - Complete Tab 1, verify Tab 2 unlocks
  - Try to skip to Tab 5, verify warning
  - Complete all tabs sequentially
  - Save program
- [ ] Write E2E test for mode switching
  - Open wizard in normal mode
  - Close wizard
  - Enable free navigation
  - Reopen wizard, verify mode changed
- [ ] Write E2E test for access control
  - Login as operator, verify checkbox hidden
  - Login as engineering, verify checkbox visible
  - Try to enable as operator, verify fails

#### 5.4 Documentation
- [ ] Update CLAUDE.md with free navigation configuration
- [ ] Add user guide for enabling/disabling mode
- [ ] Document developer testing workflow
- [ ] Add screenshots of settings dialog
- [ ] Add troubleshooting section

#### 5.5 Code Review
- [ ] Self-review all changes for SOLID principles
- [ ] Verify backward compatibility
- [ ] Check for security issues (access control)
- [ ] Verify error handling
- [ ] Check logging and debugging support

**Success Criteria:**
- MainWindow integrates correctly with new feature
- Configuration loads and persists properly
- E2E tests pass (4 tests)
- Documentation is complete
- Code review passes

---

## Summary

**Total Tasks:** 23
**Estimated Duration:** 1-2 days (12-17 hours)

**Task Breakdown by Phase:**
- Phase 1 (Setup): 4 tasks, 2-3 hours
- Phase 2 (Settings UI): 4 tasks, 3-4 hours
- Phase 3 (Navigation Logic): 7 tasks, 4-5 hours
- Phase 4 (Finish Validation): 3 tasks, 1-2 hours
- Phase 5 (Integration): 5 tasks, 2-3 hours

**Test Coverage:**
- Unit tests: 25 tests
- Integration tests: 7 tests
- E2E tests: 4 tests
- **Total: 36 tests**

**Quality Gates:**
- [ ] All 36 tests passing
- [ ] Test coverage ≥80% for new code
- [ ] Zero breaking changes to existing workflows
- [ ] Documentation complete
- [ ] Code review approved

---

## Risk Mitigation

### Risk 1: Breaking Existing Navigation
**Mitigation:**
- Extensive testing of normal mode
- Default is disabled (current behavior)
- Backward compatibility verified

### Risk 2: Access Control Bypass
**Mitigation:**
- Role checks in settings dialog
- Password confirmation required
- Audit logging for all changes

### Risk 3: Configuration Corruption
**Mitigation:**
- Default value handling
- Validation in AOIConfigManager
- Migration support for old configs

---

## Definition of Done

A phase is complete when:
- [ ] All tasks in phase are completed
- [ ] All tests for phase pass
- [ ] Code is committed with proper message
- [ ] Documentation updated (if applicable)

The track is complete when:
- [ ] All 5 phases are complete
- [ ] All 36 tests pass
- [ ] Test coverage ≥80%
- [ ] Zero breaking changes
- [ ] E2E tests validate both navigation modes
- [ ] Documentation complete
- [ ] Code review approved
- [ ] Feature working in production environment

---

## Checkpoints

### Checkpoint 1: Configuration Infrastructure (After Phase 1)
**Verification:**
- Configuration loads and saves correctly
- Unit tests pass (7 tests)
- Default value handling works

**Commit:** `feat(engineering): Add free navigation configuration infrastructure`

### Checkpoint 2: Settings UI (After Phase 2)
**Verification:**
- Settings dialog shows checkbox for engineering+
- Setting persists to config file
- Access control works
- Tests pass (11 tests total)

**Commit:** `feat(engineering): Add free navigation settings UI`

### Checkpoint 3: Navigation Logic (After Phase 3)
**Verification:**
- Free navigation mode enables all tabs
- Normal mode preserves current behavior
- Visual indicators work
- Tests pass (21 tests total)

**Commit:** `feat(engineering): Implement free navigation logic in wizard`

### Checkpoint 4: Finish Validation (After Phase 4)
**Verification:**
- Finish button validates in both modes
- Cannot save incomplete programs
- Tests pass (25 tests total)

**Commit:** `feat(engineering): Ensure finish validation in both modes`

### Checkpoint 5: Complete Feature (After Phase 5)
**Verification:**
- E2E tests pass (36 tests total)
- Documentation complete
- Zero breaking changes
- Feature working in production

**Commit:** `feat(engineering): Complete free navigation feature with E2E tests`

---

**Document Version:** 1.0
**Last Updated:** 2026-01-16
**Author:** Claude Code (Sonnet 4.5)
