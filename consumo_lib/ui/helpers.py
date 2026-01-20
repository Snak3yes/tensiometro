"""
⚠️⚠️⚠️ REGRA CRÍTICA: PROIBIÇÃO DE ESTILOS INLINE/HARDCODED ⚠️⚠️⚠️

Este arquivo FORNECE funções helpers que USEM tokens do Design System.

❌ COMPLETAMENTE PROIBIDO:
   - Criar helpers que usem valores hardcoded
   - Definir espaçamentos, tamanhos ou cores mágicos aqui

✅ ESTE ARQUIVO:
   - FORNECE funções helpers que USEM COLORS.*, TYPO.*, DIM.*, SPACE.*
   - SEMPRE via design_tokens import (Spacing, Dimensions, ColorPalette)

⚠️ ESTA REGRA NÃO PODE SER BURLADA - Code review irá rejeitar violações
⚠️⚠️⚠️ FIM DA REGRA CRÍTICA ⚠️⚠️⚠️

Funções Helper para UI

Funções utilitárias para tarefas comuns de UI.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt
from .design_tokens import Spacing, Dimensions, ColorPalette


def create_h_spacer():
    """
    Cria espaço horizontal expansível

    Usage:
        >>> layout = QHBoxLayout()
        >>> layout.addWidget(label)
        >>> layout.addItem(create_h_spacer())
        >>> layout.addWidget(button)

    Returns:
        QWidget com tamanho horizontal expansível
    """
    spacer = QWidget()
    spacer.setSizePolicy(
        QWidget.SizePolicy.Expanding,
        QWidget.SizePolicy.Minimum
    )
    return spacer


def create_v_spacer():
    """
    Cria espaço vertical expansível

    Usage:
        >>> layout = QVBoxLayout()
        >>> layout.addWidget(widget1)
        >>> layout.addItem(create_v_spacer())
        >>> layout.addWidget(widget2)

    Returns:
        QWidget com tamanho vertical expansível
    """
    spacer = QWidget()
    spacer.setSizePolicy(
        QWidget.SizePolicy.Minimum,
        QWidget.SizePolicy.Expanding
    )
    return spacer


def add_spacing(layout: QHBoxLayout | QVBoxLayout, space: int = Spacing.MD):
    """
    Adiciona espaçamento ao layout

    Args:
        layout: Layout alvo (QHBoxLayout ou QVBoxLayout)
        space: Espaçamento em pixels (padrão: 16px)

    Usage:
        >>> layout = QHBoxLayout()
        >>> add_spacing(layout, Spacing.MD)
    """
    layout.addSpacing(space)


def create_separator(orientation: Qt.Orientation = Qt.Orientation.Horizontal):
    """
    Cria linha separadora visual

    Args:
        orientation: Horizontal ou Vertical

    Usage:
        >>> separator = create_separator(Qt.Orientation.Horizontal)
        >>> layout.addWidget(separator)

    Returns:
        QFrame com linha separadora
    """
    frame = QFrame()
    if orientation == Qt.Orientation.Horizontal:
        frame.setFixedHeight(1)
        frame.setStyleSheet(f"background-color: {ColorPalette.BORDER};")
    else:
        frame.setFixedWidth(1)
        frame.setStyleSheet(f"background-color: {ColorPalette.BORDER};")
    return frame


def apply_standard_spacing(layout: QHBoxLayout | QVBoxLayout):
    """
    Aplica espaçamento padrão ao layout

    Args:
        layout: Layout alvo

    Aplica:
        - Spacing: 16px (MD)
        - Margins: 16px (MD)

    Usage:
        >>> layout = QVBoxLayout()
        >>> apply_standard_spacing(layout)
    """
    layout.setSpacing(Spacing.MD)
    layout.setContentsMargins(
        Spacing.MD, Spacing.MD,
        Spacing.MD, Spacing.MD
    )


__all__ = [
    "create_h_spacer",
    "create_v_spacer",
    "add_spacing",
    "create_separator",
    "apply_standard_spacing",
]
