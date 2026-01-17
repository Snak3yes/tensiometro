"""
GerberEditDialogs - Diálogos para edição de propriedades de objetos Gerber.

Este módulo contém diálogos para editar dimensões de objetos Gerber
(largura, altura, escala percentual, movimento).

Baseado em: poc_gerber/gerber_viewer/gui/mainwindow.py
"""

import logging
from typing import Callable, Optional

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QDoubleSpinBox, QCheckBox,
    QPushButton, QWidget, QHBoxLayout, QDialogButtonBox
)
from PyQt6.QtCore import QObject

logger = logging.getLogger(__name__)


class WidthHeightDialog(QDialog):
    """
    Diálogo para edição simultânea de largura e altura, em mm e em %.

    Padrão inspirado em Corel/Illustrator:
      - campos absolutos (mm),
      - campos de escala (% da dimensão original),
      - opção "Manter proporção".

    Usado para:
      - flash_rect / flash_oval
      - regiões (kind == "region")
    """

    def __init__(
        self,
        title: str,
        label_width: str,
        label_height: str,
        cur_w: float,
        cur_h: float,
        parent: Optional[QObject] = None,
        move_callback: Optional[Callable[[float, float], None]] = None,
        *,
        percent_only: bool = False,
    ):
        """
        Inicializa diálogo de edição de largura/altura.

        Args:
            title: Título do diálogo
            label_width: Label para campo de largura
            label_height: Label para campo de altura
            cur_w: Largura atual em mm
            cur_h: Altura atual em mm
            parent: Widget pai
            move_callback: Callback para movimento (dx, dy) -> None
            percent_only: Se True, desabilita edição direta em mm
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self._move_cb = move_callback
        self._percent_only = percent_only

        layout = QFormLayout(self)

        # Guarda dimensões originais (para cálculo de % e manter proporção)
        self._orig_w = cur_w
        self._orig_h = cur_h
        self._updating = False  # evita loops de sinal

        # --------------------- Campos absolutos (mm) ---------------------
        self._w_mm_spin = QDoubleSpinBox(self)
        self._w_mm_spin.setRange(0.001, 1000.0)
        self._w_mm_spin.setDecimals(3)
        self._w_mm_spin.setValue(cur_w)

        self._h_mm_spin = QDoubleSpinBox(self)
        self._h_mm_spin.setRange(0.001, 1000.0)
        self._h_mm_spin.setDecimals(3)
        self._h_mm_spin.setValue(cur_h)

        layout.addRow(label_width, self._w_mm_spin)
        layout.addRow(label_height, self._h_mm_spin)

        # ------------------------ Campos em % ----------------------------
        self._w_pct_spin = QDoubleSpinBox(self)
        self._w_pct_spin.setRange(0.01, 10000.0)  # 0,01% a 100x
        self._w_pct_spin.setDecimals(2)
        self._w_pct_spin.setSuffix(" %")
        self._w_pct_spin.setValue(100.0)

        self._h_pct_spin = QDoubleSpinBox(self)
        self._h_pct_spin.setRange(0.01, 10000.0)
        self._h_pct_spin.setDecimals(2)
        self._h_pct_spin.setSuffix(" %")
        self._h_pct_spin.setValue(100.0)

        layout.addRow("Largura (%):", self._w_pct_spin)
        layout.addRow("Altura (%):", self._h_pct_spin)

        # -------------------- Manter proporção ---------------------------
        self._lock_aspect_chk = QCheckBox("Manter proporção", self)
        self._lock_aspect_chk.setChecked(True)
        layout.addRow("", self._lock_aspect_chk)

        # Se estiver em modo "apenas percentual", desabilita edição direta em mm
        if self._percent_only:
            self._w_mm_spin.setEnabled(False)
            self._h_mm_spin.setEnabled(False)

        # --------------------- Movimento (X/Y) ---------------------------
        # Passo de movimento
        self._move_step_spin = QDoubleSpinBox(self)
        self._move_step_spin.setRange(0.001, 1000.0)
        self._move_step_spin.setDecimals(3)
        self._move_step_spin.setValue(0.050)  # passo padrão: 0,05 mm
        layout.addRow("Passo mov. (mm):", self._move_step_spin)

        # Botões de seta (← ↑ ↓ →)
        move_widget = QWidget(self)
        move_layout = QHBoxLayout(move_widget)
        move_layout.setContentsMargins(0, 0, 0, 0)

        self._btn_left = QPushButton("←", self)
        self._btn_up = QPushButton("↑", self)
        self._btn_down = QPushButton("↓", self)
        self._btn_right = QPushButton("→", self)

        for b in (self._btn_left, self._btn_up, self._btn_down, self._btn_right):
            b.setFixedWidth(32)

        move_layout.addWidget(self._btn_left)
        move_layout.addWidget(self._btn_up)
        move_layout.addWidget(self._btn_down)
        move_layout.addWidget(self._btn_right)

        layout.addRow("Mover:", move_widget)

        # Conexão de sinais (mm <-> %)
        self._w_mm_spin.valueChanged.connect(self._on_mm_changed)
        self._h_mm_spin.valueChanged.connect(self._on_mm_changed)
        self._w_pct_spin.valueChanged.connect(self._on_pct_changed)
        self._h_pct_spin.valueChanged.connect(self._on_pct_changed)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

        # Conexão das setas de movimento
        self._btn_left.clicked.connect(lambda: self._on_move_clicked(-1, 0))
        self._btn_right.clicked.connect(lambda: self._on_move_clicked(1, 0))
        self._btn_up.clicked.connect(lambda: self._on_move_clicked(0, 1))
        self._btn_down.clicked.connect(lambda: self._on_move_clicked(0, -1))

        logger.debug(f"WidthHeightDialog criado: {title}, cur_w={cur_w:.3f}, cur_h={cur_h:.3f}")

    # ---------------------------- Lógica ----------------------------
    def _on_mm_changed(self, _value: float):
        """Atualiza % a partir dos campos em mm, e aplica 'manter proporção'."""
        if self._updating:
            return
        self._updating = True
        try:
            sender = self.sender()
            # Manter proporção: altera a outra dimensão com base na escala
            if self._lock_aspect_chk.isChecked():
                if sender is self._w_mm_spin and self._orig_w > 0:
                    scale = self._w_mm_spin.value() / self._orig_w
                    new_h = self._orig_h * scale
                    self._h_mm_spin.setValue(new_h)
                elif sender is self._h_mm_spin and self._orig_h > 0:
                    scale = self._h_mm_spin.value() / self._orig_h
                    new_w = self._orig_w * scale
                    self._w_mm_spin.setValue(new_w)

            # Atualiza % com base nos valores atuais em mm
            if self._orig_w > 0:
                self._w_pct_spin.setValue(
                    self._w_mm_spin.value() / self._orig_w * 100.0
                )
            if self._orig_h > 0:
                self._h_pct_spin.setValue(
                    self._h_mm_spin.value() / self._orig_h * 100.0
                )
        finally:
            self._updating = False

    def _on_pct_changed(self, _value: float):
        """Atualiza mm a partir dos campos em %, e aplica 'manter proporção'."""
        if self._updating:
            return
        self._updating = True
        try:
            sender = self.sender()
            if sender is self._w_pct_spin and self._orig_w > 0:
                scale = self._w_pct_spin.value() / 100.0
                new_w = self._orig_w * scale
                self._w_mm_spin.setValue(new_w)
                if self._lock_aspect_chk.isChecked():
                    # mesma % na outra dimensão
                    self._h_pct_spin.setValue(self._w_pct_spin.value())
                    # e mesmo fator de escala aplicado em mm
                    if self._orig_h > 0:
                        new_h = self._orig_h * scale
                        self._h_mm_spin.setValue(new_h)
            elif sender is self._h_pct_spin and self._orig_h > 0:
                scale = self._h_pct_spin.value() / 100.0
                new_h = self._orig_h * scale
                self._h_mm_spin.setValue(new_h)
                if self._lock_aspect_chk.isChecked():
                    self._w_pct_spin.setValue(self._h_pct_spin.value())
                    if self._orig_w > 0:
                        new_w = self._orig_w * scale
                        self._w_mm_spin.setValue(new_w)
        finally:
            self._updating = False

    def _on_move_clicked(self, dx_sign: int, dy_sign: int):
        """
        Move o objeto imediatamente, usando o passo configurado e
        chamando o callback fornecido pela janela principal.
        """
        if self._move_cb is None:
            return
        step = self._move_step_spin.value()
        dx = dx_sign * step
        dy = dy_sign * step
        self._move_cb(dx, dy)
        logger.debug(f"Movimento: dx={dx:.3f}, dy={dy:.3f}")

    def values(self) -> tuple[float, float]:
        """
        Retorna as dimensões finais em mm.
        (Os campos em % já atualizam automaticamente os campos em mm.)
        """
        return self._w_mm_spin.value(), self._h_mm_spin.value()

    def scales(self) -> tuple[float, float]:
        """
        Retorna os fatores de escala (sx, sy), onde 1.0 = 100%.
        Útil para edição em grupo (percentual apenas), quando os objetos
        têm dimensões diferentes.
        """
        sx = self._w_pct_spin.value() / 100.0
        sy = self._h_pct_spin.value() / 100.0
        # Garante que não sejam zero (defesa)
        if sx <= 0:
            sx = 1.0
        if sy <= 0:
            sy = 1.0
        return sx, sy
