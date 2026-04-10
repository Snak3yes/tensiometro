"""
Helpers para configurar o icone visual da aplicacao Qt.

No Windows, o icone do executavel nao garante automaticamente o icone
mostrado na barra de tarefas e nas janelas Qt. Este modulo centraliza a
configuracao do AppUserModelID e do QIcon usado em runtime.
"""

from __future__ import annotations

import ctypes
import logging
import sys
from functools import lru_cache
from pathlib import Path

from aoi_lib.runtime_paths import get_runtime_path

logger = logging.getLogger(__name__)

APP_USER_MODEL_ID = "Digiboard.Tenciometro"


def _get_icon_candidates() -> tuple[Path, ...]:
    return (
        get_runtime_path("resources", "app_icon.ico"),
        get_runtime_path("resources", "app_icon.png"),
    )


@lru_cache(maxsize=1)
def get_app_icon():
    """Carrega o QIcon principal da aplicacao."""
    from PyQt6.QtGui import QIcon

    for icon_path in _get_icon_candidates():
        if not icon_path.exists():
            continue

        icon = QIcon(str(icon_path))
        if not icon.isNull():
            return icon

    return QIcon()


def configure_windows_app_user_model_id():
    """Define um AppUserModelID explicito para fixar o icone na taskbar."""
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception as exc:
        logger.warning("Falha ao configurar AppUserModelID do Windows: %s", exc)


def apply_application_icon(app) -> bool:
    """Aplica o icone global ao QApplication."""
    icon = get_app_icon()
    if icon.isNull():
        logger.warning("Icone da aplicacao nao encontrado em resources/")
        return False

    app.setWindowIcon(icon)
    return True


def apply_window_icon(widget) -> bool:
    """Aplica explicitamente o icone a uma janela ou dialogo."""
    icon = get_app_icon()
    if icon.isNull():
        return False

    widget.setWindowIcon(icon)
    return True
