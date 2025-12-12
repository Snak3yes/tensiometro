"""
inspection_result_viewer.py
----------------------------
Widget para visualização dos resultados de inspeção visual.

Exibe:
- Overlay Gerber sobre imagem real com marcação de defeitos
- Lista de aberturas inspecionadas
- Resumo estatístico
- Navegação entre defeitos
"""

from __future__ import annotations

import logging
from typing import Optional, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QCheckBox, QFrame, QScrollArea,
    QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QImage, QColor

import numpy as np
import cv2

from .stencil_inspector import InspectionResult, ApertureInspection, DefectType

log = logging.getLogger(__name__)


class InspectionImageView(QLabel):
    """Label para exibir imagem com zoom e pan."""
    
    apertureClicked = pyqtSignal(int)  # object_id da abertura clicada
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #1a1a2e; border: 1px solid #444;")
        
        self._image: Optional[np.ndarray] = None
        self._scale = 1.0
        self._apertures: List[ApertureInspection] = []
    
    def set_image(self, image: np.ndarray):
        """Define imagem a exibir."""
        self._image = image
        self._update_display()
    
    def set_apertures(self, apertures: List[ApertureInspection]):
        """Define lista de aberturas para detecção de clique."""
        self._apertures = apertures
    
    def _update_display(self):
        """Atualiza exibição."""
        if self._image is None:
            self.setText("Nenhuma imagem")
            return
        
        # Converter BGR para RGB
        if len(self._image.shape) == 3:
            rgb = cv2.cvtColor(self._image, cv2.COLOR_BGR2RGB)
        else:
            rgb = cv2.cvtColor(self._image, cv2.COLOR_GRAY2RGB)
        
        h, w = rgb.shape[:2]
        
        # Criar QImage
        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        # Escalar para caber no widget mantendo proporção
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.setPixmap(scaled)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()


class InspectionResultWidget(QWidget):
    """
    Widget principal para visualização de resultados de inspeção.
    
    Signals:
        defectSelected(int): Emitido quando um defeito é selecionado
        exportRequested(): Emitido quando exportação é solicitada
    """
    
    defectSelected = pyqtSignal(int)
    exportRequested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._result: Optional[InspectionResult] = None
        self._overlay_image: Optional[np.ndarray] = None
        
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # =====================================================
        # Painel Esquerdo: Imagem
        # =====================================================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Visualizador de imagem
        self.image_view = InspectionImageView()
        left_layout.addWidget(self.image_view)
        
        # Controles de visualização
        view_controls = QHBoxLayout()
        
        self.chk_show_all = QCheckBox("Mostrar todas as aberturas")
        self.chk_show_all.setChecked(False)
        self.chk_show_all.toggled.connect(self._update_overlay)
        view_controls.addWidget(self.chk_show_all)
        
        view_controls.addStretch()
        
        btn_save_img = QPushButton("💾 Salvar Imagem")
        btn_save_img.clicked.connect(self._save_image)
        view_controls.addWidget(btn_save_img)
        
        left_layout.addLayout(view_controls)
        
        splitter.addWidget(left_panel)
        
        # =====================================================
        # Painel Direito: Resumo e Lista
        # =====================================================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Resumo
        summary_group = QGroupBox("📊 Resumo")
        summary_layout = QVBoxLayout(summary_group)
        
        self.lbl_status = QLabel("Status: -")
        self.lbl_status.setStyleSheet("font-size: 16px; font-weight: bold;")
        summary_layout.addWidget(self.lbl_status)
        
        self.lbl_total = QLabel("Total de aberturas: -")
        summary_layout.addWidget(self.lbl_total)
        
        self.lbl_ok = QLabel("✅ OK: -")
        self.lbl_ok.setStyleSheet("color: #2ecc71;")
        summary_layout.addWidget(self.lbl_ok)
        
        self.lbl_partial = QLabel("⚠️ PARTIAL: -")
        self.lbl_partial.setStyleSheet("color: #f1c40f;")
        summary_layout.addWidget(self.lbl_partial)
        
        self.lbl_blocked = QLabel("❌ BLOCKED: -")
        self.lbl_blocked.setStyleSheet("color: #e74c3c;")
        summary_layout.addWidget(self.lbl_blocked)
        
        self.lbl_approval = QLabel("Taxa de Aprovação: -")
        self.lbl_approval.setStyleSheet("font-weight: bold;")
        summary_layout.addWidget(self.lbl_approval)
        
        right_layout.addWidget(summary_group)
        
        # Lista de defeitos
        defects_group = QGroupBox("🚨 Defeitos Detectados")
        defects_layout = QVBoxLayout(defects_group)
        
        self.table_defects = QTableWidget()
        self.table_defects.setColumnCount(4)
        self.table_defects.setHorizontalHeaderLabels(["ID", "Tipo", "Área %", "Status"])
        self.table_defects.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_defects.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_defects.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_defects.cellClicked.connect(self._on_defect_clicked)
        defects_layout.addWidget(self.table_defects)
        
        # Botões de navegação
        nav_layout = QHBoxLayout()
        
        btn_prev = QPushButton("◀ Anterior")
        btn_prev.clicked.connect(self._prev_defect)
        nav_layout.addWidget(btn_prev)
        
        btn_next = QPushButton("Próximo ▶")
        btn_next.clicked.connect(self._next_defect)
        nav_layout.addWidget(btn_next)
        
        defects_layout.addLayout(nav_layout)
        
        right_layout.addWidget(defects_group)
        
        splitter.addWidget(right_panel)
        
        # Proporção do splitter
        splitter.setSizes([600, 300])
        
        layout.addWidget(splitter)
        
        # =====================================================
        # Barra de ações
        # =====================================================
        action_bar = QHBoxLayout()
        
        btn_export = QPushButton("📄 Gerar Relatório PDF")
        btn_export.clicked.connect(self.exportRequested.emit)
        action_bar.addWidget(btn_export)
        
        action_bar.addStretch()
        
        layout.addLayout(action_bar)
    
    def set_result(
        self, 
        result: InspectionResult, 
        overlay_image: Optional[np.ndarray] = None
    ):
        """
        Define o resultado da inspeção para exibição.
        
        Args:
            result: Resultado da inspeção
            overlay_image: Imagem com overlay (se None, mostra placeholder)
        """
        self._result = result
        self._overlay_image = overlay_image
        
        self._update_summary()
        self._update_defects_table()
        self._update_overlay()
    
    def _update_summary(self):
        """Atualiza painel de resumo."""
        if self._result is None:
            return
        
        r = self._result
        
        # Status com cor
        status_colors = {
            "OK": "#2ecc71",
            "WARNING": "#f1c40f",
            "NOK": "#e74c3c"
        }
        status_color = status_colors.get(r.overall_status, "white")
        self.lbl_status.setText(f"Status: {r.overall_status}")
        self.lbl_status.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {status_color};")
        
        self.lbl_total.setText(f"Total de aberturas: {r.total_apertures}")
        self.lbl_ok.setText(f"✅ OK: {r.ok_count} ({r.ok_count/r.total_apertures*100:.0f}%)" if r.total_apertures else "✅ OK: 0")
        self.lbl_partial.setText(f"⚠️ PARTIAL: {r.partial_count}")
        self.lbl_blocked.setText(f"❌ BLOCKED: {r.blocked_count}")
        self.lbl_approval.setText(f"Taxa de Aprovação: {r.approval_rate:.1f}%")
    
    def _update_defects_table(self):
        """Atualiza tabela de defeitos."""
        self.table_defects.setRowCount(0)
        
        if self._result is None:
            return
        
        defects = self._result.defects
        self.table_defects.setRowCount(len(defects))
        
        for i, d in enumerate(defects):
            self.table_defects.setItem(i, 0, QTableWidgetItem(str(d.object_id)))
            self.table_defects.setItem(i, 1, QTableWidgetItem(d.kind))
            self.table_defects.setItem(i, 2, QTableWidgetItem(f"{d.fill_percentage:.0f}%"))
            
            status_item = QTableWidgetItem(d.status.value)
            if d.status == DefectType.PARTIAL:
                status_item.setForeground(QColor("#f1c40f"))
            else:
                status_item.setForeground(QColor("#e74c3c"))
            self.table_defects.setItem(i, 3, status_item)
    
    def _update_overlay(self):
        """Atualiza imagem de overlay."""
        if self._overlay_image is not None:
            self.image_view.set_image(self._overlay_image)
    
    def _on_defect_clicked(self, row: int, col: int):
        """Callback quando um defeito é clicado na tabela."""
        if self._result and row < len(self._result.defects):
            defect = self._result.defects[row]
            self.defectSelected.emit(defect.object_id)
            # TODO: Zoom no defeito na imagem
    
    def _prev_defect(self):
        """Navega para defeito anterior."""
        current = self.table_defects.currentRow()
        if current > 0:
            self.table_defects.selectRow(current - 1)
            self._on_defect_clicked(current - 1, 0)
    
    def _next_defect(self):
        """Navega para próximo defeito."""
        current = self.table_defects.currentRow()
        if current < self.table_defects.rowCount() - 1:
            self.table_defects.selectRow(current + 1)
            self._on_defect_clicked(current + 1, 0)
    
    def _save_image(self):
        """Salva imagem do resultado."""
        if self._overlay_image is None:
            QMessageBox.warning(self, "Sem Imagem", "Nenhuma imagem para salvar.")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Imagem",
            "inspection_result.png",
            "PNG (*.png);;JPEG (*.jpg)"
        )
        
        if filepath:
            cv2.imwrite(filepath, self._overlay_image)
            QMessageBox.information(
                self, "Imagem Salva",
                f"Imagem salva em:\n{filepath}"
            )


# ============================================================================
#  EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Criar resultado de teste
    result = InspectionResult(
        total_apertures=100,
        ok_count=85,
        partial_count=10,
        blocked_count=5,
        overall_status="WARNING",
        approval_rate=85.0
    )
    
    # Adicionar alguns defeitos de teste
    result.defects = [
        ApertureInspection(
            object_id=42, x_mm=10.5, y_mm=20.3, kind="circle",
            expected_area_px=500, observed_area_px=300,
            fill_ratio=0.6, status=DefectType.PARTIAL,
            bbox=(100, 200, 50, 50)
        ),
        ApertureInspection(
            object_id=87, x_mm=50.2, y_mm=30.1, kind="rect",
            expected_area_px=800, observed_area_px=200,
            fill_ratio=0.25, status=DefectType.BLOCKED,
            bbox=(400, 300, 60, 40)
        ),
    ]
    
    # Criar imagem de teste
    test_image = np.ones((600, 800, 3), dtype=np.uint8) * 50
    cv2.putText(test_image, "Imagem de Teste", (200, 300), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    widget = InspectionResultWidget()
    widget.set_result(result, test_image)
    widget.resize(1000, 600)
    widget.show()
    
    sys.exit(app.exec())
