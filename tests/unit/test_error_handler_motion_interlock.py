from unittest.mock import Mock

from consumo_lib.utils.error_handler import (
    is_motion_interlock_error,
    show_motion_interlock_dialog,
)


def test_is_motion_interlock_error_identifies_m137_m138_message():
    message = (
        "Movimento absoluto bloqueado pelo CLP: "
        "sensor de presenca (X1.0 -> M137) desacionado(s)."
    )
    assert is_motion_interlock_error(message) is True


def test_show_motion_interlock_dialog_uses_critical_message_box(monkeypatch):
    calls = []

    def fake_critical(parent, title, message):
        calls.append((parent, title, message))

    monkeypatch.setattr(
        "consumo_lib.utils.error_handler.QMessageBox.critical",
        fake_critical,
    )

    parent = Mock()
    message = (
        "Movimento absoluto bloqueado pelo CLP: "
        "sensor de presenca (X1.0 -> M137) desacionado(s)."
    )

    shown = show_motion_interlock_dialog(parent, message, operation="medicao")

    assert shown is True
    assert len(calls) == 1
    assert calls[0][0] is parent
    assert calls[0][1] == "Intertravamento de Movimento"
    assert "X1.0/M137 e X1.1/M138" in calls[0][2]
