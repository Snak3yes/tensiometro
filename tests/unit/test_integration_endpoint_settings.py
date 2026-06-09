from types import SimpleNamespace

from PyQt6.QtWidgets import QDialog, QMessageBox

from aoi_lib.config_manager import AOIConfigManager
from consumo_lib.dialogs.integration_endpoint_dialog import IntegrationEndpointDialog
from consumo_lib.main_window import AOIControllerApp


class _StatusBar:
    def __init__(self):
        self.messages = []

    def showMessage(self, message, timeout=None):
        self.messages.append((message, timeout))


class _EndpointDialogStub:
    endpoint = "http://10.0.0.5:3075/sfcs-print/stencil/stencil_tensiometro"

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
        "http://147.1.0.100:3075/sfcs-print/stencil/stencil_tensiometro"
    )
    assert IntegrationEndpointDialog.is_valid_endpoint_url(
        "https://api.example.com/stencil_tensiometro"
    )


def test_endpoint_dialog_rejects_empty_or_non_http_urls():
    assert not IntegrationEndpointDialog.is_valid_endpoint_url("")
    assert not IntegrationEndpointDialog.is_valid_endpoint_url("ftp://api.example.com/path")
    assert not IntegrationEndpointDialog.is_valid_endpoint_url("http:///missing-host")


def test_admin_endpoint_settings_updates_only_endpoint_url(tmp_path, monkeypatch):
    config_path = tmp_path / "aoi_config.json"
    config = AOIConfigManager(cfg_path=str(config_path))
    config.set("integration", "endpoint_url", value="http://old-server/api")
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
    assert config.get("integration", "timeout_sec") == 10.0
    assert config.get("integration", "user_id") == 1
    assert window._status_bar.messages[-1] == ("Endpoint da API salvo", 3000)


def test_non_admin_endpoint_settings_does_not_update_config(tmp_path, monkeypatch):
    config = AOIConfigManager(cfg_path=str(tmp_path / "aoi_config.json"))
    config.set("integration", "endpoint_url", value="http://old-server/api")

    warnings = []
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: warnings.append(args),
    )

    window = _window(config, role="engineering")

    AOIControllerApp.show_integration_endpoint_settings(window)

    assert config.get("integration", "endpoint_url") == "http://old-server/api"
    assert warnings
