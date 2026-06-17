from unittest.mock import Mock

from aoi_lib.auth.user import User, UserRole
from consumo_lib.dialogs import tensiometer_calibration_dialog as calibration_dialog
from consumo_lib.dialogs.tensiometer_calibration_dialog import (
    CALIBRATION_X_PULSES,
    CALIBRATION_Y_PULSES,
    CALIBRATION_Z_PULSES,
    HOME_ALL_COIL,
    HOME_COMPLETE_COIL,
    MOVE_TIMEOUT_SEC,
    TENSIOMETER_CALIBRATE_COIL,
    TENSIOMETER_POWER_COIL,
    TENSIOMETER_POWER_ON_PULSE_MS,
    TENSIOMETER_ZERO_COIL,
    TensiometerAutoCalibrationWorker,
)
from consumo_lib.facades.authentication_manager import (
    PUBLIC_TOOL_ACTIONS,
    AuthenticationManager,
)
from consumo_lib.managers.role_manager import RoleManager


class _FakeCNC:
    is_connected = True

    def __init__(self):
        self.events = []

    def pulse_coil(self, coil, duration_ms):
        self.events.append(("pulse", coil, duration_ms))
        return True

    def read_coil(self, coil):
        self.events.append(("read", coil))
        return coil == HOME_COMPLETE_COIL

    def _apply_motion_pulses(self, targets_pulses):
        self.events.append(("move", dict(targets_pulses)))
        return True

    def wait_for_idle(self, timeout=None):
        self.events.append(("wait_idle", timeout))
        return True


def test_auto_calibration_powers_and_zeros_after_initial_home_then_returns_home(monkeypatch):
    cnc = _FakeCNC()
    worker = TensiometerAutoCalibrationWorker(cnc)
    finished = []
    failed = []

    worker.calibration_finished.connect(lambda: finished.append(True))
    worker.calibration_failed.connect(lambda error: failed.append(error))
    monkeypatch.setattr(
        calibration_dialog.time,
        "sleep",
        lambda seconds: cnc.events.append(("sleep", seconds)),
    )

    worker.run()

    assert failed == []
    assert finished == [True]
    assert cnc.events == [
        ("pulse", HOME_ALL_COIL, 100),
        ("read", HOME_COMPLETE_COIL),
        ("pulse", TENSIOMETER_POWER_COIL, TENSIOMETER_POWER_ON_PULSE_MS),
        ("pulse", TENSIOMETER_ZERO_COIL, 100),
        ("move", {"X": CALIBRATION_X_PULSES, "Y": CALIBRATION_Y_PULSES}),
        ("wait_idle", MOVE_TIMEOUT_SEC),
        ("move", {"Z": CALIBRATION_Z_PULSES}),
        ("wait_idle", MOVE_TIMEOUT_SEC),
        ("sleep", calibration_dialog.CALIBRATION_SETTLE_DELAY_SEC),
        ("pulse", TENSIOMETER_CALIBRATE_COIL, 100),
        ("pulse", HOME_ALL_COIL, 100),
        ("read", HOME_COMPLETE_COIL),
    ]


def test_operator_keeps_tensiometer_calibration_tool_public():
    role_manager = RoleManager()
    role_manager.set_role("operator")

    auth_service = Mock()
    auth_service.is_authenticated.return_value = True
    auth_service.get_current_user.return_value = User(
        username="operator",
        role=UserRole.OPERATOR,
        full_name="Operator",
    )

    main_window = Mock()
    main_window.role_manager = role_manager
    main_window.menu_handler = Mock()

    auth_manager = AuthenticationManager(auth_service, Mock(), main_window)

    auth_manager.apply_role_permissions()

    main_window.menu_handler.apply_tools_permissions.assert_called_once_with(
        False,
        public_action_keys=PUBLIC_TOOL_ACTIONS,
    )
