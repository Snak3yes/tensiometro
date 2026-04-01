from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QFrame, QSizePolicy, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIntValidator
from aoi_lib.plc_axis_controller import PLCAxisController
import logging

# Design System
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)
class PLCMonitorWidget(QWidget):
    """
    Monitor de registradores e coils do CLP (inspirado na aba de debug da Adesivadora).
    Mostra valores lidos e permite gravar holdings ou pulsar coils.
    """

    def __init__(self, controller, config_manager=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.config_manager = config_manager
        self.rows = self._build_rows()

        layout = QVBoxLayout(self)

        # Barra superior com atualização e status
        header_layout = QHBoxLayout()
        self.refresh_btn = StandardButton("Atualizar valores")
        self.refresh_btn.clicked.connect(self.refresh_values)
        header_layout.addWidget(self.refresh_btn)
        header_layout.addStretch()
        self.status_label = QLabel("Conecte o PLC e clique em Atualizar.")
        header_layout.addWidget(self.status_label)
        layout.addLayout(header_layout)

        # Parâmetro operacional do fluxo de medição
        delay_group = QGroupBox("Parâmetros de Medição")
        delay_layout = QHBoxLayout(delay_group)
        delay_layout.addWidget(QLabel("Delay_Medidor (ms):"))

        self.delay_medidor_spin = QSpinBox()
        self.delay_medidor_spin.setRange(0, 10000)
        self.delay_medidor_spin.setSingleStep(50)
        self.delay_medidor_spin.setValue(self._get_delay_medidor_ms())
        self.delay_medidor_spin.setToolTip(
            "Tempo de estabilização aplicado após o eixo Z atingir a altura de medição."
        )
        delay_layout.addWidget(self.delay_medidor_spin)

        self.save_delay_btn = StandardButton("Salvar Delay")
        self.save_delay_btn.clicked.connect(self.save_delay_medidor)
        delay_layout.addWidget(self.save_delay_btn)
        delay_layout.addStretch()
        layout.addWidget(delay_group)

        # Tabela principal
        self.table = QTableWidget(len(self.rows), 4)
        self.table.setHorizontalHeaderLabels(["Variável", "Endereço", "Tipo", "Valor"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.currentCellChanged.connect(self._on_row_changed)
        self._populate_static_columns()
        layout.addWidget(self.table)

        # Controles de escrita/pulso
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Novo valor:"))
        self.value_input = QLineEdit()
        self.value_input.setValidator(QIntValidator(-2147483648, 2147483647, self))
        self.value_input.setPlaceholderText("Inteiro (holding D...)")
        form_layout.addWidget(self.value_input)

        self.write_btn = StandardButton("Gravar valor")
        self.write_btn.clicked.connect(self.write_selected_value)
        form_layout.addWidget(self.write_btn)

        self.pulse_btn = StandardButton("Pulso coil")
        self.pulse_btn.clicked.connect(self.pulse_selected_coil)
        form_layout.addWidget(self.pulse_btn)

        layout.addLayout(form_layout)

        # Configura estado inicial dos botões
        self._on_row_changed(0, 0, 0, 0)

    def _get_delay_medidor_ms(self) -> int:
        """Lê o delay global do medidor salvo na configuração da aplicação."""
        if self.config_manager is None:
            return 500
        if hasattr(self.config_manager, "get_delay_medidor_ms"):
            return self.config_manager.get_delay_medidor_ms()
        return int(self.config_manager.get("tension", "delay_medidor_ms", default=500))

    def save_delay_medidor(self):
        """Persiste o Delay_Medidor para o fluxo operacional de medição."""
        if self.config_manager is None:
            QMessageBox.warning(self, "Erro", "Configuração da aplicação não disponível.")
            return

        value = int(self.delay_medidor_spin.value())
        try:
            if hasattr(self.config_manager, "set_delay_medidor_ms"):
                self.config_manager.set_delay_medidor_ms(value)
            else:
                self.config_manager.set("tension", "delay_medidor_ms", value=value)
            self.status_label.setText(f"Delay_Medidor salvo: {value} ms.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar Delay_Medidor: {e}")

    def _build_rows(self):
        """Lista os registradores/coils relevantes já mapeados no controlador."""
        rows = []
        for axis, cfg in PLCAxisController.ADDRESSES.items():
            rows.extend([
                {"name": f"{axis} alvo (D{cfg['pos_input']})", "type": "holding", "address": cfg["pos_input"]},
                {"name": f"{axis} posição atual (D{cfg['pos_reg']})", "type": "holding", "address": cfg["pos_reg"]},
                {"name": f"{axis} velocidade (D{cfg['speed']})", "type": "holding", "address": cfg["speed"]},
                {"name": f"{axis} Jog + (M{cfg['jog_plus']})", "type": "coil", "address": cfg["jog_plus"]},
                {"name": f"{axis} Jog - (M{cfg['jog_minus']})", "type": "coil", "address": cfg["jog_minus"]},
                {"name": f"{axis} Move abs (M{cfg['move_abs']})", "type": "coil", "address": cfg["move_abs"]},
                {"name": f"{axis} Home confirmado (M{cfg['zero']})", "type": "coil", "address": cfg["zero"]},
                {"name": f"{axis} Jog stop + (M{cfg['jog_stop_plus']})", "type": "coil", "address": cfg["jog_stop_plus"]},
                {"name": f"{axis} Jog stop - (M{cfg['jog_stop_minus']})", "type": "coil", "address": cfg["jog_stop_minus"]},
            ])
        return rows

    def _populate_static_columns(self):
        for row_idx, row in enumerate(self.rows):
            self.table.setItem(row_idx, 0, QTableWidgetItem(row["name"]))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row["address"])))
            type_label = "Holding 32b" if row["type"] == "holding" else "Coil"
            self.table.setItem(row_idx, 2, QTableWidgetItem(type_label))

    def _get_plc(self) -> PLCAxisController | None:
        plc = getattr(self.controller, "cnc", None)
        if not isinstance(plc, PLCAxisController):
            QMessageBox.warning(self, "Erro", "Backend atual não é PLC (Modbus).")
            return None
        if not plc.is_connected:
            QMessageBox.warning(self, "Erro", "PLC não conectado.")
            return None
        return plc

    def refresh_values(self):
        plc = self._get_plc()
        if not plc:
            return

        for row_idx, row in enumerate(self.rows):
            try:
                if row["type"] == "holding":
                    val = plc.read_register(row["address"])
                else:
                    val = plc.read_coil(row["address"])
                row["last"] = val
            except Exception as e:
                val = f"Erro: {e}"
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(val)))

        self.status_label.setText("Valores atualizados do CLP.")

    def write_selected_value(self):
        plc = self._get_plc()
        if not plc:
            return

        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.information(self, "Seleção", "Selecione uma linha de holding.")
            return

        row = self.rows[row_idx]
        if row["type"] != "holding":
            QMessageBox.warning(self, "Tipo inválido", "Somente holdings (D...) aceitam gravação.")
            return

        try:
            value = int(self.value_input.text())
        except ValueError:
            QMessageBox.warning(self, "Valor inválido", "Informe um inteiro para gravar no registrador.")
            return

        try:
            plc.write_register(row["address"], value)
            self.status_label.setText(f"D{row['address']} gravado com sucesso.")
            self.refresh_values()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao gravar D{row['address']}: {e}")

    def pulse_selected_coil(self):
        plc = self._get_plc()
        if not plc:
            return

        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.information(self, "Seleção", "Selecione uma linha de coil.")
            return

        row = self.rows[row_idx]
        if row["type"] != "coil":
            QMessageBox.warning(self, "Tipo inválido", "Selecione um coil (M...) para pulsar.")
            return

        try:
            plc.pulse_coil(row["address"], duration_ms=50)
            self.status_label.setText(f"Pulso enviado para M{row['address']}.")
            self.refresh_values()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao pulsar M{row['address']}: {e}")

    def _on_row_changed(self, currentRow, currentColumn, previousRow, previousColumn):
        """Habilita/desabilita botões de acordo com o tipo selecionado."""
        row_idx = self.table.currentRow()
        if row_idx < 0:
            self.write_btn.setEnabled(False)
            self.value_input.setEnabled(False)
            self.pulse_btn.setEnabled(False)
            return

        row = self.rows[row_idx]
        is_holding = row["type"] == "holding"
        self.write_btn.setEnabled(is_holding)
        self.value_input.setEnabled(is_holding)
        self.pulse_btn.setEnabled(row["type"] == "coil")
