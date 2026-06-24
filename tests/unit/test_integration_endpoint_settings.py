from types import SimpleNamespace

from PyQt6.QtWidgets import QDialog, QMessageBox

from aoi_lib.config_manager import AOIConfigManager
from consumo_lib.dialogs.integration_endpoint_dialog import (
    IntegrationEndpointDialog,
    StencilLookupEndpointDialog,
)
from consumo_lib.main_window import AOIControllerApp


class _StatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, message, timeout=None):
        self.messages.append((message, timeout))


class _EndpointDialogStub:
    endpoint = "http://10.0.0.5:3075/sfcs-print/stencil/stencil_tensiometro"
    enabled = False

    def __init__(self, endpoint_url, enabled=True, parent=None):
        self.initial_endpoint_url = endpoint_url
        self.initial_enabled = enabled
        self.parent = parent

    def exec(self):
        return QDialog.DialogCode.Accepted

    def endpoint_url(self):
        return self.endpoint

    def integration_enabled(self):
        return self.enabled


class _StencilLookupDialogStub:
    endpoint = "http://10.0.0.5:3075/sfcs-print/stencil/{codigo_barras}"

    def __init__(self, endpoint_url, parent=None):
        self.initial_endpoint_url = endpoint_url
        self.parent = parent

    def exec(self):
        return QDialog.DialogCode.Accepted

    def endpoint_url(self):
        return self.endpoint


def _window(config, role="admin"):
    status_bar = _StatusBar()
    return SimpleNamespace(
        config_manager=config,
        role_manager=SimpleNamespace(get_current_role=lambda: role),
        statusBar=lambda: status_bar,
        _status_bar=status_bar,
    )


def test_endpoint_dialog_accepts_http_and_https_urls():
    assert IntegrationEndpointDialog.is_valid_endpoint_url(
        "http://147.1.0.85:3075/sfcs-print/stencil/stencil_tensiometro"
    )
    assert IntegrationEndpointDialog.is_valid_endpoint_url(
        "https://api.example.com/stencil_tensiometro"
    )


def test_endpoint_dialog_rejects_empty_or_non_http_urls():
    assert not IntegrationEndpointDialog.is_valid_endpoint_url("")
    assert not IntegrationEndpointDialog.is_valid_endpoint_url("ftp://api.example.com/path")
    assert not IntegrationEndpointDialog.is_valid_endpoint_url("http:///missing-host")


def test_stencil_lookup_endpoint_dialog_requires_valid_url(qtbot, monkeypatch):
    warnings = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warnings.append(args),
    )

    dialog = StencilLookupEndpointDialog(endpoint_url="")
    qtbot.addWidget(dialog)

    dialog.accept()

    assert warnings
    assert dialog.result() == QDialog.DialogCode.Rejected


def test_stencil_lookup_endpoint_dialog_accepts_valid_url(qtbot, monkeypatch):
    warnings = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warnings.append(args),
    )

    dialog = StencilLookupEndpointDialog(
        endpoint_url="http://147.1.0.100:3075/sfcs-print/stencil/{codigo_barras}"
    )
    qtbot.addWidget(dialog)

    dialog.accept()

    assert warnings == []
    assert dialog.result() == QDialog.DialogCode.Accepted


def test_endpoint_dialog_allows_empty_url_when_integration_disabled(qtbot, monkeypatch):
    warnings = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warnings.append(args),
    )

    dialog = IntegrationEndpointDialog(endpoint_url="", enabled=False)
    qtbot.addWidget(dialog)

    dialog.accept()

    assert warnings == []
    assert dialog.result() == QDialog.DialogCode.Accepted


def test_admin_endpoint_settings_updates_endpoint_url_and_enabled_flag(tmp_path, monkeypatch):
    config_path = tmp_path / "aoi_config.json"
    config = AOIConfigManager(cfg_path=str(config_path))
    config.set("integration", "endpoint_url", value="http://old-server/api")
    config.set("integration", "enabled", value=True)
    config.set("integration", "timeout_sec", value=10.0)
    config.set("integration", "user_id", value=1)

    monkeypatch.setattr(
        "consumo_lib.dialogs.integration_endpoint_dialog.IntegrationEndpointDialog",
        _EndpointDialogStub,
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    window = _window(config)

    AOIControllerApp.show_integration_endpoint_settings(window)

    assert config.get("integration", "endpoint_url") == _EndpointDialogStub.endpoint
    assert config.get("integration", "enabled") is False
    assert config.get("integration", "timeout_sec") == 10.0
    assert config.get("integration", "user_id") == 1
    assert window._status_bar.messages[-1] == ("Configuracao da API salva", 3000)


def test_admin_endpoint_settings_can_enable_existing_endpoint(tmp_path, monkeypatch):
    config = AOIConfigManager(cfg_path=str(tmp_path / "aoi_config.json"))
    existing_endpoint = "http://old-server/api"
    config.set("integration", "endpoint_url", value=existing_endpoint)
    config.set("integration", "enabled", value=False)

    class EnableDialogStub(_EndpointDialogStub):
        enabled = True
        endpoint = existing_endpoint

    monkeypatch.setattr(
        "consumo_lib.dialogs.integration_endpoint_dialog.IntegrationEndpointDialog",
        EnableDialogStub,
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    window = _window(config)

    AOIControllerApp.show_integration_endpoint_settings(window)

    assert config.get("integration", "endpoint_url") == existing_endpoint
    assert config.get("integration", "enabled") is True


def test_non_admin_endpoint_settings_does_not_update_config(tmp_path, monkeypatch):
    config = AOIConfigManager(cfg_path=str(tmp_path / "aoi_config.json"))
    config.set("integration", "endpoint_url", value="http://old-server/api")
    config.set("integration", "enabled", value=True)

    warnings = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warnings.append(args),
    )

    window = _window(config, role="engineering")

    AOIControllerApp.show_integration_endpoint_settings(window)

    assert config.get("integration", "endpoint_url") == "http://old-server/api"
    assert config.get("integration", "enabled") is True
    assert warnings


def test_admin_stencil_lookup_settings_updates_endpoint_and_keeps_lookup_enabled(tmp_path, monkeypatch):
    config = AOIConfigManager(cfg_path=str(tmp_path / "aoi_config.json"))
    config.set(
        "sfcs_stencil_lookup",
        "endpoint_url",
        value="http://old-server/sfcs-print/stencil/{codigo_barras}",
    )
    config.set("sfcs_stencil_lookup", "enabled", value=False)
    config.set("sfcs_stencil_lookup", "timeout_sec", value=10.0)

    monkeypatch.setattr(
        "consumo_lib.dialogs.integration_endpoint_dialog.StencilLookupEndpointDialog",
        _StencilLookupDialogStub,
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    window = _window(config)

    AOIControllerApp.show_stencil_lookup_endpoint_settings(window)

    assert config.get("sfcs_stencil_lookup", "endpoint_url") == _StencilLookupDialogStub.endpoint
    assert config.get("sfcs_stencil_lookup", "enabled") is True
    assert config.get("sfcs_stencil_lookup", "timeout_sec") == 10.0
    assert window._status_bar.messages[-1] == ("Endpoint de consulta salvo", 3000)


def test_non_admin_stencil_lookup_settings_does_not_update_config(tmp_path, monkeypatch):
    config = AOIConfigManager(cfg_path=str(tmp_path / "aoi_config.json"))
    endpoint = "http://old-server/sfcs-print/stencil/{codigo_barras}"
    config.set("sfcs_stencil_lookup", "endpoint_url", value=endpoint)
    config.set("sfcs_stencil_lookup", "enabled", value=True)

    warnings = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warnings.append(args),
    )

    window = _window(config, role="engineering")

    AOIControllerApp.show_stencil_lookup_endpoint_settings(window)

    assert config.get("sfcs_stencil_lookup", "endpoint_url") == endpoint
    assert config.get("sfcs_stencil_lookup", "enabled") is True
    assert warnings
