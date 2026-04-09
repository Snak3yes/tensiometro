"""
Helpers para resolver caminhos de runtime.

Quando o aplicativo roda empacotado, a raiz operacional deve ser a pasta
onde o executavel esta localizado. Em desenvolvimento, a raiz e o checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path


def get_app_root() -> Path:
    """Retorna a raiz operacional da aplicacao."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_runtime_path(*parts: str) -> Path:
    """Monta um caminho relativo a raiz operacional da aplicacao."""
    return get_app_root().joinpath(*parts)
