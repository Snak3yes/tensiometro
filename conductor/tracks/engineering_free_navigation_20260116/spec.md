# Track Specification: Engineering Wizard Free Navigation Mode

**Track ID:** engineering_free_navigation_20260116
**Type:** Feature
**Priority:** Medium
**Created:** 2026-01-16
**Status:** Pending

---

## 1. Overview

### 1.1 Feature Description

Add a configuration option to disable navigation restrictions in the Engineering Wizard (fluxo de engenharia). This feature allows developers and testers to freely navigate between all 7 tabs without completing prerequisites, facilitating testing, debugging, and demonstration of the system.

### 1.2 Problem Statement

**Current Behavior:**
- Engineering Wizard enforces strict tab navigation validation
- Each tab must be validated before advancing to the next tab
- Tabs 2-7 are disabled until previous tabs are completed
- Validation messages prevent navigation until all dependencies are satisfied

**Problems:**
1. Testing individual tabs requires completing all previous tabs
2. Debugging tab-specific issues is time-consuming
3. Demonstrating specific features to stakeholders requires full workflow completion
4. Development workflow is slowed by validation checks during active development

**Example Scenario:**
A developer wants to test the Alignment Widget (Tab 5):
- Currently must complete: Tab 1 (program data), Tab 2 (Gerber upload), Tab 3 (fiducial capture), Tab 4 (mosaic capture)
- Each tab requires valid inputs and hardware operations
- This makes iterative development and testing very slow

### 1.3 Proposed Solution

Add a **"Free Navigation Mode"** configuration that:
1. Disables tab validation when enabled
2. Enables all 7 tabs for free navigation
3. Can be toggled via the same Authentication Settings dialog
4. Persists configuration in `aoi_config.json`
5. Respects role-based access (Engineering+ only)

---

## 2. Functional Requirements

### 2.1 Configuration Management

**REQ-CONF-1:** Configuration Storage
- Store `free_navigation_mode` setting in `config/aoi_config.json`
- Path: `engineering_wizard.free_navigation_enabled` (boolean, default: false)
- Persist across application restarts

**REQ-CONF-2:** Configuration Loading
- AOIConfigManager loads configuration on application startup
- EngineeringWizardDialog reads configuration on initialization
- Configuration changes apply immediately (no restart required)

### 2.2 Access Control

**REQ-AUTH-1:** Role-Based Access
- Only users with `engineering` role or higher can modify free navigation setting
- Operator and Quality roles CANNOT modify this setting
- Configuration changes require password confirmation (re-authentication)

**REQ-AUTH-2:** Settings Dialog Integration
- Add checkbox to existing Authentication Settings Dialog
- Location: `consumo_lib/dialogs/auth_settings_dialog.py`
- Group with "Engineering Settings" section

### 2.3 Navigation Behavior

**REQ-NAV-1:** Free Navigation Mode (ENABLED)
- All 7 tabs are enabled regardless of validation state
- "Next" button advances without validation checks
- Tabs can be clicked directly in any order
- No validation warnings when changing tabs
- "Finish" button still validates all tabs before completion

**REQ-NAV-2:** Normal Navigation Mode (DISABLED - default)
- Current behavior is preserved
- Tabs are enabled sequentially as validation passes
- "Next" button validates current tab before advancing
- Direct tab clicking respects validation state
- Validation warnings prevent incomplete workflows

**REQ-NAV-3:** Visual Indicators
- When free navigation is enabled: Show "🔓 Navegação Livre" badge in dialog title
- When free navigation is disabled: Normal title without badge
- Add tooltip to tabs showing mode status
- Optional: Change tab color to indicate mode (e.g., blue tint for free nav)

### 2.4 Validation Behavior

**REQ-VAL-1:** Finish Button Validation
- "Finish" button ALWAYS validates all tabs, regardless of navigation mode
- Prevents saving incomplete programs
- Shows validation summary with all missing/invalid fields

**REQ-VAL-2:** Validation State Tracking
- Validation state continues to be tracked in free navigation mode
- Tab completion indicators (✓) still reflect actual validation state
- Users can see which tabs are incomplete vs. complete

### 2.5 User Interface

**REQ-UI-1:** Settings Dialog
- Add checkbox: "Habilitar Navegação Livre (Testing/Debug)"
- Add description label explaining the mode
- Add warning: "⚠️ Modo de desenvolvimento - permite ignorar validações"
- Position below authentication settings in same dialog

**REQ-UI-2:** Engineering Wizard Dialog
- Update title bar when mode is active
- Add status indicator in progress bar area
- Maintain all existing UI elements

---

## 3. Non-Functional Requirements

### 3.1 Backward Compatibility
- **REQ-BF-1:** Default behavior unchanged (free_navigation_enabled: false)
- **REQ-BF-2:** Existing configuration files without the setting default to false
- **REQ-BF-3:** No changes to validation logic or state management

### 3.2 Security
- **REQ-SEC-1:** Setting changes require password confirmation
- **REQ-SEC-2:** Audit log entry when mode is toggled
- **REQ-SEC-3:** Operator role cannot enable mode (security prevention)

### 3.3 Performance
- **REQ-PERF-1:** Configuration loading adds <10ms to startup time
- **REQ-PERF-2:** No performance impact on wizard navigation

### 3.4 Testing
- **REQ-TEST-1:** Unit tests for configuration manager (get/set free_navigation)
- **REQ-TEST-2:** Unit tests for navigation logic with both modes
- **REQ-TEST-3:** Integration tests for settings dialog
- **REQ-TEST-4:** E2E test for complete workflow with both modes

---

## 4. Technical Design

### 4.1 Configuration Schema

**File:** `config/aoi_config.json`

```json
{
  "engineering_wizard": {
    "free_navigation_enabled": false,
    "last_used_mode": "normal"
  },
  "authentication": {
    "require_login_on_startup": false,
    "default_role": "engineering"
  }
}
```

### 4.2 Component Changes

**4.2.1 AOIConfigManager** (`aoi_lib/config_manager.py`)
```python
def get_free_navigation_enabled(self) -> bool
def set_free_navigation_enabled(self, enabled: bool) -> None
```

**4.2.2 AuthenticationSettingsDialog** (`consumo_lib/dialogs/auth_settings_dialog.py`)
- Add checkbox widget for free navigation
- Add save/load logic for the setting
- Integrate with existing password confirmation

**4.2.3 EngineeringWizardDialog** (`consumo_lib/dialogs/engineering_wizard_dialog.py`)
- Add `free_navigation_mode` property
- Modify `_create_tabs()` to skip `setTabEnabled()` when mode is active
- Modify `_on_next()` to skip validation when mode is active
- Update `_update_ui_state()` to show mode indicator

**4.2.4 MainWindow** (`consumo_lib/main_window.py`)
- Pass free navigation setting to EngineeringWizardDialog
- Load configuration on startup

### 4.3 Data Flow

```
User opens Authentication Settings Dialog
    ↓
User checks "Habilitar Navegação Livre"
    ↓
User clicks Save → Password confirmation
    ↓
AuthConfigManager.save_config()
    ↓
AOIConfigManager.set_free_navigation_enabled(True)
    ↓
config/aoi_config.json updated
    ↓
Log entry: "Free navigation enabled by user X"
    ↓
Next EngineeringWizardDialog launch reads config
    ↓
Dialog initializes with all tabs enabled
```

---

## 5. Acceptance Criteria

### 5.1 Configuration Management
- [ ] Configuration persists in `aoi_config.json`
- [ ] Configuration loads on application startup
- [ ] Default value is `false` (disabled)
- [ ] Missing configuration key defaults to `false`

### 5.2 Access Control
- [ ] Only Engineering+ users can see and modify the checkbox
- [ ] Operator and Quality users cannot modify setting
- [ ] Password confirmation required to save changes
- [ ] Audit log entry created on setting change

### 5.3 Navigation Behavior
- [ ] **Free Navigation Mode (enabled):**
  - [ ] All 7 tabs are clickable from the start
  - [ ] "Next" button advances without validation
  - [ ] No validation warnings when changing tabs
  - [ ] Visual indicator shows "🔓 Navegação Livre"

- [ ] **Normal Navigation Mode (disabled):**
  - [ ] Tabs are enabled sequentially as before
  - [ ] "Next" button validates before advancing
  - [ ] Validation warnings prevent incomplete workflows
  - [ ] No visual indicator for free navigation

### 5.4 Validation
- [ ] "Finish" button validates all tabs in both modes
- [ ] Validation state tracking continues in free navigation mode
- [ ] Tab completion indicators (✓) work in both modes
- [ ] Cannot save incomplete programs in either mode

### 5.5 Testing
- [ ] Unit tests for AOIConfigManager getters/setters
- [ ] Unit tests for navigation logic (both modes)
- [ ] Integration tests for settings dialog
- [ ] E2E test for complete workflow (both modes)
- [ ] Test coverage ≥80% for new code

---

## 6. User Stories

### 6.1 Developer Story
**As a** developer
**I want to** enable free navigation mode in Engineering Wizard
**So that** I can quickly test individual tabs without completing the entire workflow

**Acceptance:**
- Can toggle mode via settings dialog
- All tabs become immediately accessible
- No validation warnings during navigation
- Can disable mode to resume normal operation

### 6.2 QA Engineer Story
**As a** QA engineer
**I want to** demonstrate specific Engineering Wizard features to stakeholders
**So that** I don't need to complete all 7 tabs to show Tab 5 (Alignment)

**Acceptance:**
- Can jump directly to any tab
- Can show feature without data entry
- Can disable mode before saving

### 6.3 System Administrator Story
**As a** system administrator
**I want to** control who can enable free navigation mode
**So that** production operators don't bypass validation checks

**Acceptance:**
- Only Engineering+ users can enable mode
- Password confirmation required
- Audit log tracks mode changes

---

## 7. Risks and Mitigations

### 7.1 Risk: Production Data Corruption
**Risk:** Operator enables free navigation mode and creates incomplete programs

**Mitigation:**
- Access control restricted to Engineering+ only
- "Finish" button still validates all data
- Cannot save incomplete programs regardless of mode

### 7.2 Risk: Configuration Complexity
**Risk:** Too many configuration options confuse users

**Mitigation:**
- Group engineering settings together
- Clear description and warning labels
- Default is disabled (normal behavior)

### 7.3 Risk: Backward Compatibility
**Risk:** Existing configuration files break

**Mitigation:**
- Default to `false` if key missing
- No changes to validation logic
- Existing workflows unchanged

---

## 8. Success Metrics

- [ ] Configuration persists and loads correctly
- [ ] Access control prevents unauthorized changes
- [ ] Free navigation mode enables all tabs
- [ ] Normal navigation mode preserves current behavior
- [ ] Test coverage ≥80% for new code
- [ ] Zero breaking changes to existing workflows
- [ ] Developer can test Tab 5 directly without completing Tabs 1-4
- [ ] E2E test completes successfully in both modes

---

## 9. Dependencies

### 9.1 Code Dependencies
- `aoi_lib/config_manager.py` - Configuration management
- `consumo_lib/dialogs/auth_settings_dialog.py` - Settings UI
- `consumo_lib/dialogs/engineering_wizard_dialog.py` - Wizard navigation
- `consumo_lib/main_window.py` - Main window initialization

### 9.2 Track Dependencies
- None (standalone feature)

### 9.3 External Dependencies
- PyQt6 (UI framework)
- Existing authentication system

---

## 10. Out of Scope

- Modifying validation logic (validation behavior unchanged)
- Changing the 7-tab workflow structure
- Adding new tabs or removing existing tabs
- Modifying role-based access control system
- Creating separate testing/demonstration modes
- Automatic data generation for testing

---

**Document Version:** 1.0
**Last Updated:** 2026-01-16
**Author:** Claude Code (Sonnet 4.5)
