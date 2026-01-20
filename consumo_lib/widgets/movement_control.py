from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QPushButton, QLabel, QDoubleSpinBox, QSpinBox, QMessageBox, QSizePolicy,
    QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QDoubleValidator, QIntValidator
from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.plc_axis_controller import PLCAxisController
from aoi_lib.movement_orchestrator import MovementOrchestrator
import logging

# Design System imports
from consumo_lib.ui import TYPO, DIM, COLORS, SPACE
from consumo_lib.ui.widget_standards import StandardButton

logger = logging.getLogger(__name__)

# Import para registro de atualização de posição
try:
    from consumo_lib.utils.main_window.app_state import register_movement_widget, unregister_movement_widget
    _REGISTRY_AVAILABLE = True
except ImportError:
    # Fallback para compatibilidade
    _REGISTRY_AVAILABLE = False
    logger.warning("Registro de MovementControlWidgets não disponível")

class MovementControlWidget(QWidget):
    """
    Widget for controlling CNC movement (jog).
    
    Delega toda a lógica de controle para o MovementOrchestrator.
    """

    def __init__(self, controller, cfg: AOIConfigManager, orchestrator: MovementOrchestrator = None, parent=None):
        """
        Inicializa o widget.

        Args:
            controller: CNCAOIController (Legacy support)
            cfg: AOIConfigManager
            orchestrator: MovementOrchestrator - Obrigatório para nova arquitetura
            parent: Widget pai
        """
        super().__init__(parent)
        self.controller = controller
        self.cfg = cfg
        self.orchestrator = orchestrator

        # Fallback para compatibilidade se orchestrator não for passado
        if self.orchestrator is None:
            # Tenta usar o antigo movement_service se passado como kwarg ou cria um novo orchestrator
            # Aqui vamos assumir que se não passou, criamos um novo baseado no controller
            logger.warning("MovementOrchestrator não fornecido, criando instância local.")
            self.orchestrator = MovementOrchestrator(controller, cfg)

        # Registrar este widget para receber atualizações de posição
        if _REGISTRY_AVAILABLE:
            register_movement_widget(self)
            logger.debug("MovementControlWidget registrado para atualizações de posição")

        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Group box for movement controls
        movement_group = QGroupBox("Movement Controls")
        movement_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        movement_layout = QGridLayout()
        
        # Directional control buttons
        self.up_button = QPushButton("↑")
        self.down_button = QPushButton("↓")
        self.left_button = QPushButton("←")
        self.right_button = QPushButton("→")

        for btn in [self.up_button, self.down_button, self.left_button, self.right_button]:
            btn.setMinimumSize(50, 50)
            font = TYPO.get_font(16, bold=True)
            btn.setFont(font)
        
        self.up_button.pressed.connect(lambda: self._on_direction_press("Y",  -1))
        self.up_button.released.connect(self._on_direction_release)
        self.down_button.pressed.connect(lambda: self._on_direction_press("Y", 1))
        self.down_button.released.connect(self._on_direction_release)
        self.left_button.pressed.connect(lambda: self._on_direction_press("X", -1))
        self.left_button.released.connect(self._on_direction_release)
        self.right_button.pressed.connect(lambda: self._on_direction_press("X", 1))
        self.right_button.released.connect(self._on_direction_release)

        self.z_up_button   = QPushButton("Z+")
        self.z_down_button = QPushButton("Z-")
        for zbtn in (self.z_up_button, self.z_down_button):
            zbtn.setMinimumSize(50, 30)
        self.z_up_button.pressed.connect(  lambda: self._on_direction_press("Z",  -1))
        self.z_up_button.released.connect(self._on_direction_release)
        self.z_down_button.pressed.connect(lambda: self._on_direction_press("Z", 1))
        self.z_down_button.released.connect(self._on_direction_release)
        
        movement_layout.addWidget(self.up_button, 0, 1)
        movement_layout.addWidget(self.left_button, 1, 0)
        movement_layout.addWidget(self.right_button, 1, 2)
        movement_layout.addWidget(self.down_button, 2, 1)
        movement_layout.addWidget(self.z_up_button,   0, 3, 1, 2)
        movement_layout.addWidget(self.z_down_button, 2, 3, 1, 2)

        # Botão de Emergency Stop / Reset
        self.emergency_stop_button = StandardButton("STOP", variant="danger")
        self.emergency_stop_button.setCheckable(True)
        self.emergency_stop_button.setMinimumSize(100, DIM.BUTTON_HEIGHT_MD)
        self.emergency_stop_button.toggled.connect(self.on_emergency_stop_toggle)
        movement_layout.addWidget(self.emergency_stop_button, 1, 1, Qt.AlignmentFlag.AlignCenter)
        
        # Step size
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Step Size:"))
        default_step = self.cfg.get("movement", "step_size", default=10.0)
        self.step_size = QLineEdit(f"{default_step:.2f}")
        step_validator = QDoubleValidator(0.01, 100000.0, 2, self)
        step_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        from PyQt6.QtCore import QLocale
        step_validator.setLocale(QLocale(QLocale.Language.C))
        self.step_size.setValidator(step_validator)
        step_layout.addWidget(self.step_size)
        step_layout.addWidget(QLabel("mm"))
        
        # Feed rate
        feed_layout = QHBoxLayout()
        feed_layout.addWidget(QLabel("Feed Rate:"))
        default_feed = self.cfg.get("movement", "feed_rate", default=1000.0)
        self.feed_rate = QLineEdit(f"{default_feed}")
        self.feed_rate.setValidator(QDoubleValidator(1.0, 30000.0, 0, self))
        feed_layout.addWidget(self.feed_rate)
        feed_layout.addWidget(QLabel("mm/min"))
        
        movement_layout.addLayout(step_layout, 3, 0, 1, 3)
        movement_layout.addLayout(feed_layout, 4, 0, 1, 3)

        self.step_size.editingFinished.connect(self._save_step_feed)
        self.feed_rate.editingFinished.connect(self._save_step_feed)

        # Go to Zero
        self.go_to_zero_btn = StandardButton("Go to Zero", variant="primary")
        self.go_to_zero_btn.clicked.connect(self.go_to_zero)
        movement_layout.addWidget(self.go_to_zero_btn, 6, 0, 1, 3)

        # Go to Position
        self.go_to_position_btn = StandardButton("Go to Position", variant="primary")
        self.go_to_position_btn.setToolTip("Ir para posição de trabalho específica (WPos)")
        self.go_to_position_btn.clicked.connect(self.show_go_to_dialog)
        movement_layout.addWidget(self.go_to_position_btn, 7, 0, 1, 3)

        # Keyboard Control
        self.keyboard_control_checkbox = QCheckBox("Enable Keyboard Control")
        self.keyboard_control_checkbox.setChecked(False)
        movement_layout.addWidget(self.keyboard_control_checkbox, 8, 0, 1, 3)
        
        # Backlight
        self.backlight_button = QPushButton("💡 Backlight OFF")
        self.backlight_button.setCheckable(True)
        self.backlight_button.setMinimumHeight(DIM.BUTTON_HEIGHT_SM)
        self.backlight_button.setStyleSheet(f"""
            QPushButton {{ background-color: {COLORS.TEXT_HINT}; color: {COLORS.BACKGROUND}; border-radius: {DIM.RADIUS_SM}px; }}
            QPushButton:checked {{ background-color: {COLORS.WARNING}; color: {COLORS.ON_PRIMARY}; font-weight: bold; }}
        """)
        self.backlight_button.toggled.connect(self._on_backlight_toggle)
        movement_layout.addWidget(self.backlight_button, 9, 0, 1, 5)
        
        # Movement mode (G90/G91)
        mode_layout = QHBoxLayout()
        self.mode_absolute = StandardButton("Passo", variant="secondary")
        self.mode_absolute.setCheckable(True)
        self.mode_absolute.clicked.connect(lambda: self.set_motion_mode("G90"))

        self.mode_relative = StandardButton("Contínuo", variant="secondary")
        self.mode_relative.setCheckable(True)
        self.mode_relative.setChecked(True)
        self.mode_relative.clicked.connect(lambda: self.set_motion_mode("G91"))

        mode_layout.addWidget(self.mode_absolute)
        mode_layout.addWidget(self.mode_relative)
        movement_layout.addLayout(mode_layout, 5, 0, 1, 3)

        self._init_position_display(movement_layout)

        movement_group.setLayout(movement_layout)
        layout.addWidget(movement_group)
        layout.setAlignment(movement_group, Qt.AlignmentFlag.AlignTop)

    def _init_position_display(self, parent_layout):
        position_group = QGroupBox("Posição Atual (mm)")
        position_group.setMaximumHeight(180)
        position_layout = QGridLayout()
        position_layout.setContentsMargins(5, 5, 5, 5)
        position_layout.setSpacing(3)

        self.pos_x_label = QLabel("0.000 mm")
        self.pos_y_label = QLabel("0.000 mm")
        self.pos_z_label = QLabel("0.000 mm")

        for label in (self.pos_x_label, self.pos_y_label, self.pos_z_label):
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: #333;
                    color: #0f0;
                    padding: 4px 8px;
                    font-size: 13px;
                    font-weight: bold;
                    border-radius: 3px;
                }
            """)
            label.setMinimumWidth(100)

        self.pos_status_label = QLabel("Desconectado")
        self.pos_status_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.pos_status_label.setStyleSheet("""
            QLabel {
                background-color: #333;
                color: #fc0;
                padding: 4px 8px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 3px;
            }
        """)
        self.pos_status_label.setMinimumWidth(100)

        position_layout.addWidget(QLabel("X:"), 0, 0)
        position_layout.addWidget(self.pos_x_label, 0, 1)
        position_layout.addWidget(QLabel("Y:"), 1, 0)
        position_layout.addWidget(self.pos_y_label, 1, 1)
        position_layout.addWidget(QLabel("Z:"), 2, 0)
        position_layout.addWidget(self.pos_z_label, 2, 1)
        position_layout.addWidget(QLabel("Status:"), 3, 0)
        position_layout.addWidget(self.pos_status_label, 3, 1)

        position_group.setLayout(position_layout)
        parent_layout.addWidget(position_group, 3, 3, 6, 2)

    def update_position(self, x: float, y: float, z: float, status: str = None):
        self.pos_x_label.setText(f"{x:8.3f} mm")
        self.pos_y_label.setText(f"{y:8.3f} mm")
        self.pos_z_label.setText(f"{z:8.3f} mm")
        if status is not None:
            self.pos_status_label.setText(status)

    def _save_step_feed(self):
        try:
            step = float(self.step_size.text())
            feed = float(self.feed_rate.text())
            self.cfg.remember_step_feed(step, feed)
        except ValueError:
            pass
    
    def _on_backlight_toggle(self, checked: bool):
        logger.debug(f"🔍 DEBUG: _on_backlight_toggle chamado com checked={checked}")
        result = self.orchestrator.set_backlight(checked)
        
        if result.success:
            if checked:
                self.backlight_button.setText("💡 Backlight ON")
                logger.info("ILUMINAÇÃO: Backlight ligado")
            else:
                self.backlight_button.setText("💡 Backlight OFF")
                logger.info("ILUMINAÇÃO: Backlight desligado")
        else:
            logger.error(f"Falha backlight: {result.error_message}")
            self.backlight_button.blockSignals(True)
            self.backlight_button.setChecked(not checked)
            self.backlight_button.blockSignals(False)
            QMessageBox.warning(self, "Erro", f"Falha ao controlar backlight: {result.error_message}")
        
    def _on_direction_press(self, axis: str, direction: int):
        logger.info(f"⌨️ _on_direction_press chamado: axis={axis}, direction={direction}")

        step = self._get_step_size()
        feed = self._get_feed_rate()
        
        if feed is None or step is None:
            return

        self.cfg.remember_step_feed(step, feed)

        if self.mode_absolute.isChecked():
            # STEP (G90)
            logger.info(f"⌨️ Modo PASSO (G90)")
            result = self.orchestrator.step_move(axis, direction, step, feed)
        else:
            # JOG (G91)
            logger.info(f"⌨️ Modo CONTÍNUO (G91)")
            result = self.orchestrator.jog(axis, direction, feed)
            
        if not result.success:
            logger.error(f"⌨️ ERRO no movimento: {result.error_message}")
            QMessageBox.warning(self, "Erro", result.error_message)

    def _on_direction_release(self):
        if self.mode_relative.isChecked():
            result = self.orchestrator.stop_jog()
            if not result.success:
                logger.warning(f"Erro ao parar jog: {result.error_message}")

    def start_movement(self, axis: str, direction: int):
        self._on_direction_press(axis, direction)

    def _get_feed_rate(self) -> float | None:
        try:
            val = float(self.feed_rate.text())
            # Validação via orchestrator para limites
            res = self.orchestrator.validate_feed_rate(val)
            
            if res.success and res.data.get('clamped', False):
                limit = res.data.get('limit')
                # Pergunta ao usuário se quer atualizar configurações
                # Nota: Lógica de atualização de config ($110) não está no orchestrator ainda
                # Mantendo comportamento legado por enquanto, mas usando o limite validado
                resp = QMessageBox.question(
                    self, "Feed acima do limite",
                    f"O valor F={val:.0f} mm/min excede o limite ({limit}).\n"
                    "Deseja usar o limite máximo?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if resp == QMessageBox.StandardButton.Yes:
                    val = limit
                    self.feed_rate.setText(str(limit))
                else:
                    return None
            return val
        except ValueError:
            QMessageBox.warning(self, "Erro", "Feed-rate inválido")
            return None

    def _get_step_size(self) -> float | None:
        try:
            return float(self.step_size.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Step size inválido")
            return None

    def go_to_zero(self):
        result = self.orchestrator.home()
        if not result.success:
            QMessageBox.warning(self, "Erro", result.error_message)
        else:
            if self.window():
                self.window().statusBar().showMessage("Homing iniciado/concluído")
    
    def get_current_feed_rate(self):
        try:
            return float(self.feed_rate.text())
        except ValueError:
            return 1000.0

    def stop_movement(self):
        self._on_direction_release()

    def show_go_to_dialog(self):
        from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QHBoxLayout, QPushButton, QMessageBox
        from PyQt6.QtGui import QDoubleValidator

        dialog = QDialog(self)
        dialog.setWindowTitle("Go to Position")
        dialog.setModal(True)
        layout = QGridLayout(dialog)

        # Usar orchestrator para obter posição se possível, ou controller direto
        # O orchestrator não expõe get_position diretamente na API simplificada ainda,
        # mas podemos adicionar ou acessar controller.
        try:
            current = self.controller.cnc.get_current_position()
        except Exception:
            current = {'x': 0.0, 'y': 0.0}

        layout.addWidget(QLabel("X (mm):"), 0, 0)
        x_input = QLineEdit()
        x_input.setValidator(QDoubleValidator(-10000.0, 10000.0, 4, x_input))
        x_input.setText(f"{current.get('x', 0.0):.3f}")
        layout.addWidget(x_input, 0, 1)

        layout.addWidget(QLabel("Y (mm):"), 1, 0)
        y_input = QLineEdit()
        y_input.setValidator(QDoubleValidator(-10000.0, 10000.0, 4, y_input))
        y_input.setText(f"{current.get('y', 0.0):.3f}")
        layout.addWidget(y_input, 1, 1)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout, 2, 0, 1, 2)

        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                x = float(x_input.text())
                y = float(y_input.text())
                self.go_to_position(x, y)
            except ValueError:
                QMessageBox.warning(self, "Erro", "Valores inválidos para X ou Y")

    def go_to_position(self, x, y):
        feed = self._get_feed_rate()
        if feed is None: return

        # Executa movimento absoluto via orchestrator
        # Nota: Idealmente seria assíncrono para não travar a UI se for bloqueante.
        # O MovementOrchestrator.move_absolute é bloqueante ou não?
        # No PLC controller, move_to_absolute_position parece retornar rápido após enviar comando?
        # Vamos assumir que sim por enquanto. Se precisar de thread, o orchestrator deveria gerenciar ou o widget.
        # Por enquanto, chamada direta.
        
        result = self.orchestrator.move_absolute(x, y, 0, feed)
        if result.success:
            if self.window(): self.window().statusBar().showMessage(f"Movendo para {x},{y}")
        else:
            QMessageBox.warning(self, "Erro", result.error_message)

    def set_motion_mode(self, mode):
        # Atualiza UI
        if mode == "G90":
            self.mode_absolute.setChecked(True)
            self.mode_relative.setChecked(False)
        else:
            self.mode_absolute.setChecked(False)
            self.mode_relative.setChecked(True)
            
        # Não temos set_motion_mode no orchestrator ainda?
        # Ah, no controller tem current_motion_mode. 
        # Vamos adicionar no futuro se necessário, mas G90/G91 é implícito nas chamadas jog/step do orchestrator.
        pass

    def on_emergency_stop_toggle(self, checked):
        if checked:
            # RESET / PARADA
            result = self.orchestrator.emergency_stop()
            if result.success:
                self.emergency_stop_button.setText("Reset")
                self.emergency_stop_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS.WARNING};
                        color: {COLORS.ON_PRIMARY};
                        border: none;
                        border-radius: {DIM.RADIUS_SM}px;
                        padding: {SPACE.SM}px {SPACE.MD}px;
                        font-size: {TYPO.BODY_LARGE}px;
                        font-weight: bold;
                    }}
                """)
                if self.window(): self.window().statusBar().showMessage("Máquina parada.")
            else:
                QMessageBox.critical(self, "Erro", f"Falha na parada: {result.error_message}")
                self.emergency_stop_button.setChecked(False)
        else:
            # UNLOCK
            result = self.orchestrator.unlock()
            if result.success:
                self.emergency_stop_button.setText("STOP")
                # StandardButton danger variant handles STOP state
                if self.window(): self.window().statusBar().showMessage("Máquina desbloqueada.")
            else:
                QMessageBox.critical(self, "Erro", f"Falha no desbloqueio: {result.error_message}")
                self.emergency_stop_button.setChecked(True)

    def closeEvent(self, event):
        """
        Limpeza quando widget é fechado.

        Remove do registro de MovementControlWidgets para evitar memory leaks.
        """
        # Remover do registro de atualizações de posição
        if _REGISTRY_AVAILABLE:
            unregister_movement_widget(self)
            logger.debug("MovementControlWidget removido do registro")

        # Chamar implementação base
        super().closeEvent(event)