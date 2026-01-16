# Implementation Plan: Authentication Configuration Feature

## Phase 1: Setup and Configuration

### Task 1.1: Update AOIConfigManager with Authentication Section
- [ ] Add `authentication` section to `_DEFAULT_CFG` in `aoi_lib/config_manager.py`
    - [ ] Add `require_login_on_startup: true`
    - [ ] Add `default_role: "operator"`
- [ ] Add helper methods to AOIConfigManager:
    - [ ] `get_require_login_on_startup() -> bool`
    - [ ] `get_default_role() -> str`
    - [ ] `set_require_login_on_startup(value: bool)`
    - [ ] `set_default_role(role: str)`
- [ ] Add migration logic for existing configs (backward compatibility)

### Task 1.2: Create AuthConfigManager
- [ ] Create `consumo_lib/managers/auth_config_manager.py`
- [ ] Implement `AuthConfigManager` class:
    - [ ] `__init__(config_manager: AOIConfigManager, role_manager: RoleManager, auth_service: AuthService)`
    - [ ] `can_modify_config() -> bool` - check if user has engineering+ permission
    - [ ] `get_current_config() -> dict` - read current authentication settings
    - [ ] `update_config(require_login: bool, default_role: str, confirming_user: str, password: str) -> bool` - update with password confirmation
    - [ ] `validate_role(role: str) -> bool` - check if role is valid
    - [ ] `_log_config_change(user: str, old_config: dict, new_config: dict)` - audit log
- [ ] Add comprehensive error handling
- [ ] Add logging for all operations

- [ ] Task: Conductor - User Manual Verification 'Phase 1: Setup and Configuration' (Protocol in workflow.md)

## Phase 2: Unit Tests for AuthConfigManager

### Task 2.1: Write Tests for AuthConfigManager
- [ ] Create `tests/unit/test_auth_config_manager.py`
- [ ] Test `can_modify_config()`:
    - [ ] Returns True for engineering role
    - [ ] Returns True for admin role
    - [ ] Returns False for operator role
    - [ ] Returns False for quality role
- [ ] Test `get_current_config()`:
    - [ ] Returns default values when config section missing
    - [ ] Returns existing values when config present
    - [ ] Handles invalid values gracefully
- [ ] Test `validate_role()`:
    - [ ] Accepts valid roles (operator, engineering, quality, admin)
    - [ ] Rejects invalid roles
- [ ] Test `update_config()`:
    - [ ] Successfully updates with valid credentials
    - [ ] Fails with invalid password
    - [ ] Fails for non-engineering users
    - [ ] Logs configuration changes
- [ ] Test backward compatibility:
    - [ ] Works when authentication section missing from config
    - [ ] Creates section with defaults on first update

### Task 2.2: Achieve 80%+ Test Coverage
- [ ] Run coverage analysis on AuthConfigManager
- [ ] Add tests for edge cases:
    - [ ] Concurrent modification attempts
    - [ ] Invalid JSON in config file
    - [ ] File permission errors
- [ ] Verify coverage >80%

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Unit Tests for AuthConfigManager' (Protocol in workflow.md)

## Phase 3: Authentication Settings Dialog

### Task 3.1: Create AuthenticationSettingsDialog UI
- [ ] Create `consumo_lib/dialogs/auth_settings_dialog.py`
- [ ] Implement dialog layout:
    - [ ] Checkbox: "Solicitar login ao iniciar"
    - [ ] ComboBox: "Login padrão" with roles
    - [ ] Button: "Aplicar"
    - [ ] Button: "Cancelar"
    - [ ] Info label explaining permissions
- [ ] Implement `__init__(auth_config_manager: AuthConfigManager, current_role: str, parent=None)`
- [ ] Implement UI initialization from current config
- [ ] Implement validation logic
- [ ] Implement state management (enable/disable Apply button)

### Task 3.2: Implement Dialog Logic
- [ ] Implement `load_current_config()` - populate fields from config
- [ ] Implement `on_checkbox_changed()` - handle state changes
- [ ] Implement `on_apply_clicked()`:
    - [ ] Check if user has permission (can_modify_config)
    - [ ] Show permission denied if not engineering+
    - [ ] If changing to "no login required", show login confirmation dialog
    - [ ] Call `auth_config_manager.update_config()` with confirmation
    - [ ] Show success/error messages
    - [ ] Close dialog on success
- [ ] Implement `on_cancel_clicked()` - close without saving
- [ ] Add tooltips for all fields

### Task 3.3: Add Login Confirmation Dialog
- [ ] Create method `show_confirmation_dialog()` in AuthenticationSettingsDialog
- [ ] Reuse existing LoginDialog for confirmation
- [ ] Implement callback for successful confirmation
- [ ] Handle confirmation failure (wrong password)

- [ ] Task: Conductor - User Manual Verification 'Phase 3: Authentication Settings Dialog' (Protocol in workflow.md)

## Phase 4: Integration Tests for Dialog

### Task 4.1: Write Tests for AuthenticationSettingsDialog
- [ ] Create `tests/unit/test_auth_settings_dialog.py`
- [ ] Test dialog initialization:
    - [ ] Loads current config correctly
    - [ ] Displays correct values in fields
- [ ] Test permission checking:
    - [ ] Engineering user can access
    - [ ] Admin user can access
    - [ ] Operator user receives permission denied
- [ ] Test apply functionality:
    - [ ] Apply enabled only when values change
    - [ ] Successful update closes dialog
    - [ ] Failed update keeps dialog open
- [ ] Test confirmation flow:
    - [ ] Confirmation dialog shown when disabling login
    - [ ] Invalid password prevents update
    - [ ] Valid password allows update

### Task 4.2: Test Dialog Edge Cases
- [ ] Test with invalid config values
- [ ] Test with missing config section
- [ ] Test rapid apply/cancel operations
- [ ] Test dialog state persistence

- [ ] Task: Conductor - User Manual Verification 'Phase 4: Integration Tests for Dialog' (Protocol in workflow.md)

## Phase 5: Menu Integration

### Task 5.1: Add Menu Entry
- [ ] Modify `consumo_lib/handlers/menu_handler.py`:
    - [ ] Add action "Configurações de Autenticação..." to Engineering menu
    - [ ] Connect action to handler method
    - [ ] Add keyboard shortcut (optional)
- [ ] Implement visibility logic:
    - [ ] Show only for engineering+ roles
    - [ ] Update menu when role changes

### Task 5.2: Implement Dialog Launcher
- [ ] Add handler in MainWindow or appropriate coordinator:
    - [ ] `on_auth_settings_triggered()`
    - [ ] Check user permissions
    - [ ] Create and show AuthenticationSettingsDialog
    - [ ] Handle dialog result
- [ ] Add proper error handling
- [ ] Add logging for menu access

- [ ] Task: Conductor - User Manual Verification 'Phase 5: Menu Integration' (Protocol in workflow.md)

## Phase 6: Auto-Login Implementation

### Task 6.1: Modify Startup Logic
- [ ] Modify `consumo_lib/coordinators/setup_coordinator.py`:
    - [ ] Read authentication config on startup
    - [ ] Check if `require_login_on_startup` is False
    - [ ] If False, skip LoginDialog
    - [ ] Set RoleManager to `default_role` directly
    - [ ] Log auto-login event
- [ ] Ensure LoginDialog is shown when `require_login_on_startup` is True

### Task 6.2: Handle Auto-Login Edge Cases
- [ ] Handle missing `default_role` in config (fallback to "operator")
- [ ] Handle invalid `default_role` in config (fallback to "operator")
- [ ] Add startup logging for auto-login
- [ ] Test with various config states

- [ ] Task: Conductor - User Manual Verification 'Phase 6: Auto-Login Implementation' (Protocol in workflow.md)

## Phase 7: End-to-End Testing

### Task 7.1: Manual Testing Scenarios
- [ ] Test scenario 1: Normal login (require_login=true)
    - [ ] Start application
    - [ ] Verify LoginDialog is shown
    - [ ] Login as operator
    - [ ] Verify no auth settings menu option
- [ ] Test scenario 2: Engineering user configures auto-login
    - [ ] Login as engineering
    - [ ] Open auth settings dialog
    - [ ] Disable login requirement
    - [ ] Confirm with password
    - [ ] Set default role to operator
    - [ ] Apply changes
    - [ ] Close application
- [ ] Test scenario 3: Auto-login works
    - [ ] Start application
    - [ ] Verify no LoginDialog
    - [ ] Verify logged in as operator
    - [ ] Verify auth settings not visible
- [ ] Test scenario 4: Revert to normal login
    - [ ] Login as engineering (via menu if available, or manual method)
    - [ ] Open auth settings
    - [ ] Enable login requirement
    - [ ] Confirm with password
    - [ ] Apply changes
- [ ] Test scenario 5: Permission denied
    - [ ] Login as quality
    - [ ] Try to access auth settings (should fail or not be visible)

### Task 7.2: Automated E2E Tests
- [ ] Create `tests/integration/test_auth_config_e2e.py`
- [ ] Test complete configuration flow
- [ ] Test auto-login flow
- [ ] Test permission enforcement
- [ ] Test config persistence across restarts

- [ ] Task: Conductor - User Manual Verification 'Phase 7: End-to-End Testing' (Protocol in workflow.md)

## Phase 8: Documentation and Cleanup

### Task 8.1: Update Documentation
- [ ] Update `CLAUDE.md`:
    - [ ] Add authentication configuration to relevant sections
    - [ ] Document new AuthConfigManager
    - [ ] Document auto-login behavior
- [ ] Update `README.md` if needed
- [ ] Add inline code comments (Portuguese)
- [ ] Ensure all docstrings follow Google style (Portuguese)

### Task 8.2: Code Quality Checks
- [ ] Run pylint on all new files:
    - [ ] `consumo_lib/managers/auth_config_manager.py`
    - [ ] `consumo_lib/dialogs/auth_settings_dialog.py`
- [ ] Run flake8 on all new files
- [ ] Fix any warnings or errors
- [ ] Verify no code duplication

### Task 8.3: Final Testing
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Verify 100% pass rate
- [ ] Run coverage: `coverage run -m pytest tests/ && coverage report`
- [ ] Verify >80% coverage on new code
- [ ] Manual smoke test of all scenarios

- [ ] Task: Conductor - User Manual Verification 'Phase 8: Documentation and Cleanup' (Protocol in workflow.md)

## Phase 9: Release Preparation

### Task 9.1: Git Commit
- [ ] Review all changes
- [ ] Stage all files
- [ ] Create commit with message:
    ```
    feat(auth): Add authentication configuration feature

    - Add AuthConfigManager for managing authentication settings
    - Add AuthenticationSettingsDialog for UI configuration
    - Implement auto-login on startup based on config
    - Require engineering+ permission to modify settings
    - Add password confirmation for security
    - Add audit logging for configuration changes

    Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
    ```

### Task 9.2: Tag Release
- [ ] Create git tag: `auth_config_feature_20260115`
- [ ] Push commit and tag to remote

- [ ] Task: Conductor - User Manual Verification 'Phase 9: Release Preparation' (Protocol in workflow.md)

## Success Criteria

- [ ] All 9 phases completed
- [ ] All acceptance criteria met (see spec.md)
- [ ] Test coverage >80%
- [ ] All tests passing (100% pass rate)
- [ ] Linter clean (no errors)
- [ ] Documentation updated
- [ ] Manual testing successful for all scenarios
- [ ] Zero breaking changes to existing functionality
- [ ] Backward compatibility maintained

## Estimated Effort

- **Total Phases:** 9
- **Total Tasks:** 32
- **Estimated Duration:** 2-3 days
- **Lines of Code:** ~600-800
- **Test Cases:** ~40-50
