from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QPushButton, QLabel, QDoubleSpinBox, QSpinBox, QMessageBox, QSizePolicy,
    QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QDoubleValidator, QIntValidator
from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.plc_axis_controller import PLCAxisController
import logging

logger = logging.getLogger(__name__)

class MovementControlWidget(QWidget):
    """
    Widget for controlling CNC movement (jog).

    Esta versão é compatível com MovementService.
    Se MovementService for fornecido, usa-o; caso contrário,
    usa o controller diretamente (compatibilidade com código antigo).
    """

    def __init__(self, controller, cfg: AOIConfigManager, movement_service=None, parent=None):
        """
        Inicializa o widget.

        Args:
            controller: CNCAOIController
            cfg: AOIConfigManager
            movement_service: MovementService (opcional) - se fornecido, usa-o em vez de controller direto
            parent: Widget pai
        """
        super().__init__(parent)
        self.controller = controller
        self.cfg = cfg
        self.movement_service = movement_service  # Pode ser None (compatibilidade)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Group box for movement controls
        movement_group = QGroupBox("Movement Controls")
        # Vertical size fixed to its contents (no stretch)
        movement_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        movement_layout = QGridLayout()
        
        # Directional control buttons
        self.up_button = QPushButton("↑")
        self.down_button = QPushButton("↓")
        self.left_button = QPushButton("←")
        self.right_button = QPushButton("→")
        
        # Style the buttons
        for btn in [self.up_button, self.down_button, self.left_button, self.right_button]:
            btn.setMinimumSize(50, 50)
            font = QFont()
            font.setBold(True)
            font.setPointSize(16)
            btn.setFont(font)
        
        # Connect press/release events for continuous movement
        self.up_button.pressed.connect(lambda: self._on_direction_press("Y",  -1))
        self.up_button.released.connect(self._on_direction_release)
        self.down_button.pressed.connect(lambda: self._on_direction_press("Y", 1))
        self.down_button.released.connect(self._on_direction_release)
        self.left_button.pressed.connect(lambda: self._on_direction_press("X", -1))
        self.left_button.released.connect(self._on_direction_release)
        self.right_button.pressed.connect(lambda: self._on_direction_press("X", 1))
        self.right_button.released.connect(self._on_direction_release)

        # --------- NOVOS BOTÕES Z -----------------
        self.z_up_button   = QPushButton("Z+")
        self.z_down_button = QPushButton("Z-")
        for zbtn in (self.z_up_button, self.z_down_button):
            zbtn.setMinimumSize(50, 30)
        self.z_up_button.pressed.connect(  lambda: self._on_direction_press("Z",  -1))
        self.z_up_button.released.connect(self._on_direction_release)
        self.z_down_button.pressed.connect(lambda: self._on_direction_press("Z", 1))
        self.z_down_button.released.connect(self._on_direction_release)
        
        # Add buttons to grid
        movement_layout.addWidget(self.up_button, 0, 1)
        movement_layout.addWidget(self.left_button, 1, 0)
        movement_layout.addWidget(self.right_button, 1, 2)
        movement_layout.addWidget(self.down_button, 2, 1)

        # Coloca Z+ acima de STOP e Z- abaixo
        movement_layout.addWidget(self.z_up_button,   0, 3)
        movement_layout.addWidget(self.z_down_button, 2, 3)

        # Botão de Emergency Stop / Reset
        self.emergency_stop_button = QPushButton("STOP")
        self.emergency_stop_button.setCheckable(True) # Torna o botão toggle
        self.emergency_stop_button.setMinimumSize(100, 40)
        font_stop = QFont()
        font_stop.setBold(True)
        self.emergency_stop_button.setFont(font_stop)
        # Estilo inicial (vermelho)
        self.emergency_stop_button.setStyleSheet("background-color: red; color: white;")
        self.emergency_stop_button.toggled.connect(self.on_emergency_stop_toggle) # Conecta ao handler

        # Adiciona o botão ao layout, centralizado abaixo dos direcionais
        movement_layout.addWidget(self.emergency_stop_button, 1, 1, Qt.AlignmentFlag.AlignCenter) # Coloca no centro (linha 1, coluna 1)
        
        # Step size and feed rate controls
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Step Size:"))
        # ---------- STEP SIZE ---------------
        default_step = self.cfg.get("movement", "step_size", default=10.0)
        self.step_size = QLineEdit(f"{default_step:.2f}")  # Formata com 2 decimais
        # ▸ VALIDAÇÃO numérica (0.01 a 100000 mm, com 2 decimais)
        step_validator = QDoubleValidator(0.01, 100000.0, 2, self)
        step_validator.setNotation(QDoubleValidator.Notation.StandardNotation)  # Evita notação científica
        # CRÍTICO: Define locale para usar ponto (.) como separador decimal
        from PyQt6.QtCore import QLocale
        step_validator.setLocale(QLocale(QLocale.Language.C))  # Locale C = ponto decimal
        self.step_size.setValidator(step_validator)
        step_layout.addWidget(self.step_size)
        step_layout.addWidget(QLabel("mm"))
        
        feed_layout = QHBoxLayout()
        feed_layout.addWidget(QLabel("Feed Rate:"))

        # ---------- FEED RATE ---------------
        default_feed = self.cfg.get("movement", "feed_rate", default=1000.0)
        self.feed_rate = QLineEdit(f"{default_feed}")
        # ▸ feed entre 1 e 30000 mm/min
        self.feed_rate.setValidator(QDoubleValidator(1.0, 30000.0, 0, self))
        feed_layout.addWidget(self.feed_rate)
        feed_layout.addWidget(QLabel("mm/min"))
        
        # Add step and feed rate controls
        movement_layout.addLayout(step_layout, 3, 0, 1, 3)
        movement_layout.addLayout(feed_layout, 4, 0, 1, 3)

        # ---- grava no JSON quando o usuário termina de editar -----
        self.step_size.editingFinished.connect(self._save_step_feed)
        self.feed_rate.editingFinished.connect(self._save_step_feed)

        self.go_to_zero_btn = QPushButton("Go to Zero")
        self.go_to_zero_btn.clicked.connect(self.go_to_zero)
        self.go_to_zero_btn.setMinimumHeight(40)  # Altura mínima para facilitar o clique
        font = QFont()
        font.setBold(True)
        self.go_to_zero_btn.setFont(font)
        movement_layout.addWidget(self.go_to_zero_btn, 6, 0, 1, 3)  # Posiciona abaixo dos controles existentes

        # Botão para deslocar a head para posição de trabalho definida pelo usuário (WPos)
        self.go_to_position_btn = QPushButton("Go to Position")
        self.go_to_position_btn.setToolTip("Ir para posição de trabalho específica (WPos)")
        self.go_to_position_btn.clicked.connect(self.show_go_to_dialog)
        movement_layout.addWidget(self.go_to_position_btn, 7, 0, 1, 3)

        # Checkbox "Enable Keyboard Control" agora na linha 8 (posição anterior do Test Motor Hold)
        self.keyboard_control_checkbox = QCheckBox("Enable Keyboard Control")
        self.keyboard_control_checkbox.setChecked(False)
        movement_layout.addWidget(self.keyboard_control_checkbox, 8, 0, 1, 3)
        
        # ========== BOTÃO DE BACKLIGHT ==========
        # Controla a iluminação inferior (Y0.7) para inspeção de stencil
        self.backlight_button = QPushButton("💡 Backlight OFF")
        self.backlight_button.setCheckable(True)
        self.backlight_button.setMinimumHeight(35)
        self.backlight_button.setStyleSheet("""
            QPushButton { background-color: #444; color: white; border-radius: 5px; }
            QPushButton:checked { background-color: #FFD700; color: black; font-weight: bold; }
        """)
        self.backlight_button.toggled.connect(self._on_backlight_toggle)
        movement_layout.addWidget(self.backlight_button, 9, 0, 1, 4)  # Ocupa toda a largura
        
        # Movement mode (G90/G91)
        mode_layout = QHBoxLayout()
        self.mode_absolute = QPushButton("Passo")
        self.mode_absolute.setCheckable(True)
        self.mode_absolute.clicked.connect(lambda: self.set_motion_mode("G90"))
        
        self.mode_relative = QPushButton("Contínuo")
        self.mode_relative.setCheckable(True)
        self.mode_relative.setChecked(True)  # Default to relative mode
        self.mode_relative.clicked.connect(lambda: self.set_motion_mode("G91"))
        
        mode_layout.addWidget(self.mode_absolute)
        mode_layout.addWidget(self.mode_relative)
        movement_layout.addLayout(mode_layout, 5, 0, 1, 3)
        
        movement_group.setLayout(movement_layout)
        layout.addWidget(movement_group)
        # Keep the groupbox at top without stretching
        layout.setAlignment(movement_group, Qt.AlignmentFlag.AlignTop)

    def _save_step_feed(self):
        try:
            step = float(self.step_size.text())
            feed = float(self.feed_rate.text())
            self.cfg.remember_step_feed(step, feed)
        except ValueError:
            # silencioso – validação já existe
            return
    
    def _on_backlight_toggle(self, checked: bool):
        """
        Controla o backlight (iluminação inferior do stencil).
        Liga/desliga a saída Y0.7 do CLP.
        """
        logger.debug(f"🔍 DEBUG: _on_backlight_toggle chamado com checked={checked}")

        if not hasattr(self.controller, 'cnc') or not self.controller.cnc.is_connected:
            # Bloqueia sinais para evitar loop infinito ao reverter o estado
            logger.debug("🔍 DEBUG: CLP não conectado, revertendo botão")
            self.backlight_button.blockSignals(True)
            self.backlight_button.setChecked(not checked)
            self.backlight_button.blockSignals(False)
            QMessageBox.warning(self, "Erro", "CLP não conectado")
            return

        # Verifica se o controlador tem suporte a backlight
        if not hasattr(self.controller.cnc, 'backlight_set'):
            logger.debug("🔍 DEBUG: Controlador não suporta backlight, revertendo botão")
            self.backlight_button.blockSignals(True)
            self.backlight_button.setChecked(not checked)
            self.backlight_button.blockSignals(False)
            QMessageBox.warning(self, "Erro", "Controlador não suporta backlight")
            return
        
        # Aciona o backlight
        logger.debug(f"🔍 DEBUG: Chamando backlight_set({checked})")
        success = self.controller.cnc.backlight_set(checked)
        logger.debug(f"🔍 DEBUG: backlight_set retornou success={success}")
        
        if success:
            if checked:
                self.backlight_button.setText("💡 Backlight ON")
                logger.info("ILUMINAÇÃO: Backlight ligado (Y0.7 = HIGH)")
            else:
                self.backlight_button.setText("💡 Backlight OFF")
                logger.info("ILUMINAÇÃO: Backlight desligado (Y0.7 = LOW)")
        else:
            # Bloqueia sinais para evitar loop infinito ao reverter o estado
            logger.debug(f"🔍 DEBUG: backlight_set falhou, revertendo botão de {checked} para {not checked}")
            self.backlight_button.blockSignals(True)
            self.backlight_button.setChecked(not checked)
            self.backlight_button.blockSignals(False)
            QMessageBox.warning(self, "Erro", "Falha ao controlar backlight")
        
    def _on_direction_press(self, axis: str, direction: int):
        """
        Chamada quando o usuário pressiona um botão (ou tecla).
        Decide entre STEP ou JOG e delega ao MovementService.
        """
        logger.info(f"⌨️ _on_direction_press chamado: axis={axis}, direction={direction}")

        # Verificar se MovementService está disponível
        if self.movement_service is None:
            logger.error("MovementService não disponível. Movimento não funcionará.")
            QMessageBox.warning(
                self, "Service Não Disponível",
                "MovementService não foi injetado. Controle de movimento não disponível."
            )
            return

        # Salvar step/feed antes de mover
        step = self._get_step_size()
        feed = self._get_feed_rate()
        logger.info(f"⌨️ step={step} mm, feed={feed} mm/min")

        if feed is None or step is None:
            logger.warning("⌨️ step ou feed é None, abortando")
            return

        # --- grava imediatamente no JSON ---
        self.cfg.remember_step_feed(step, feed)

        # Usar MovementService
        if self.mode_absolute.isChecked():
            # STEP (G90)
            logger.info(f"⌨️ Modo PASSO (G90) - chamando start_step_move")
            result = self.movement_service.start_step_move(axis, direction, step, feed)
            logger.info(f"⌨️ start_step_move result: success={result.success}, error={result.error_message}")
            if not result.success:
                logger.error(f"⌨️ ERRO no movimento passo: {result.error_message}")
                QMessageBox.warning(self, "Erro", result.error_message)
        else:
            # JOG (G91)
            logger.info(f"⌨️ Modo CONTÍNUO (G91) - chamando start_jog")
            result = self.movement_service.start_jog(axis, direction, feed)
            logger.info(f"⌨️ start_jog result: success={result.success}, error={result.error_message}")
            if not result.success:
                logger.error(f"⌨️ ERRO no movimento jog: {result.error_message}")
                QMessageBox.warning(self, "Erro", result.error_message)

    def _on_direction_release(self):
        """Interrompe jog se estivermos em modo contínuo."""
        if self.mode_relative.isChecked():      # só há jog se G91
            if self.movement_service is None:
                logger.warning("MovementService não disponível. Não é possível parar jog.")
                return

            # Usar MovementService
            result = self.movement_service.stop_jog()
            if not result.success:
                logger.warning(f"Erro ao parar jog: {result.error_message}")

    def start_movement(self, axis: str, direction: int):
        """
        Mantido apenas para chamadas vindas de eventFilter (atalhos de
        teclado). Encaminha para _on_direction_press.
        """
        self._on_direction_press(axis, direction)

    def _get_feed_rate(self) -> float | None:
        """Lê o feed-rate; devolve None e avisa em caso de erro."""
        try:
            val = float(self.feed_rate.text())

            if self.controller.cnc.is_connected:
                max_lim = max(self.controller.cnc.max_feed.values())
                if val > max_lim + 1e-3:
                    resp = QMessageBox.question(
                        self, "Feed acima do limite",
                        (f"O valor F={val:.0f} mm/min excede o limite atual "
                         f"(≤ {max_lim:.0f}).\n\n"
                         "Deseja atualizar $110 e $111 para permitir essa "
                         "velocidade em X e Y?"),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if resp == QMessageBox.StandardButton.Yes:
                        # novo limite com folga de 10 %
                        new_lim = int(val * 1.1)                 # 10 % de folga
                        new_acc = int((new_lim / 60) * 5)        # ≈5 s para atingir Vmáx

                        cmds = [
                            f"$110={new_lim}", f"$111={new_lim}",
                            f"$120={new_acc}", f"$121={new_acc}"
                        ]
                        for c in cmds:
                            self.controller.cnc.send_command(c, priority=True)

                        # actualiza cache interno
                        self.controller.cnc.max_feed['x'] = new_lim
                        self.controller.cnc.max_feed['y'] = new_lim
                        self.controller.cnc.max_acc ['x'] = new_acc
                        self.controller.cnc.max_acc ['y'] = new_acc
                        # desabilita avisos futuros de clamp
                        self.controller.cnc._feed_clamp_warned = True
                        QMessageBox.information(
                            self, "Limites actualizados",
                            (f"Feed-máx X/Y = {new_lim} mm/min\n"
                             f"Aceleração X/Y = {new_acc} mm/s²")
                        )
                    else:
                        # clampará ao valor máximo existente
                        QMessageBox.information(self, "Feed ajustado",
                                                f"A velocidade será limitada a {max_lim} mm/min.")
                        val = max_lim
            return val
        except ValueError:
            QMessageBox.warning(self, "Erro", "Feed-rate inválido")
            return None

    def _get_step_size(self) -> float | None:
        """Lê o step-size; devolve None e avisa em caso de erro."""
        try:
            return float(self.step_size.text())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Step size inválido")
            return None

    def go_to_zero(self):
        """
        Executa homing ou movimento para zero usando MovementService.
        """
        # Verificar se MovementService está disponível
        if self.movement_service is None:
            logger.error("MovementService não disponível. Homing não funcionará.")
            QMessageBox.warning(
                self, "Service Não Disponível",
                "MovementService não foi injetado. Homing não disponível."
            )
            return

        # Usar MovementService
        result = self.movement_service.go_to_zero()
        if not result.success:
            QMessageBox.warning(self, "Erro", result.error_message)
        else:
            # Atualizar interface
            if self.window():
                self.window().update_position_display()
                self.window().statusBar().showMessage("Homing concluído")
    
    def get_current_feed_rate(self):
        """Método público para outras classes acessarem a velocidade configurada"""
        try:
            return float(self.feed_rate.text())
        except ValueError:
            return 1000.0  # fallback

    def stop_movement(self):
        self._on_direction_release()

    def show_go_to_dialog(self):
        """Exibe diálogo para coletar coordenadas de destino (WPos)."""
        from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QHBoxLayout, QPushButton, QMessageBox
        from PyQt6.QtGui import QDoubleValidator

        dialog = QDialog(self)
        dialog.setWindowTitle("Go to Position")
        dialog.setModal(True)
        layout = QGridLayout(dialog)

        # Captura a posição de trabalho atual (WPos) para pré‑preencher os campos
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
        """Realiza movimento para a posição absoluta de trabalho (WPos)."""
        from PyQt6.QtWidgets import QMessageBox

        # 1. Verifica se há conexão
        if not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            return

        # 2. Verifica se a máquina está livre
        status = self.controller.cnc.machine_status
        if status in ("Alarm", "Run", "Jog"):
            QMessageBox.warning(self, "Aviso", f"Máquina ocupada ({status})")
            return

        # 4. Obtém feed rate
        try:
            feed_rate = float(self.feed_rate.text())
        except:
            feed_rate = 1000

        # 5. Deslocamento assíncrono
        self._start_move_thread(x, y, feed_rate,
                                status_msg=f"Movendo para X:{x:.3f}, Y:{y:.3f}")

    def _start_move_thread(self, x=None, y=None, z=None,
                           feed=1000, status_msg="Movendo…"):
        stbar = self.window().statusBar()
        stbar.showMessage(status_msg)

        self._move_thread = MoveTaskThread(
                                self.controller.cnc, x, y, z, feed
                            )

        def _on_done(xx, yy, zz):
            stbar.showMessage(f"Head em X:{xx:.3f}, Y:{yy:.3f}, Z:{zz:.3f}")
            # força atualização UI
            QTimer.singleShot(50, self.window().update_position_display)

        def _on_err(msg):
            QMessageBox.critical(self, "Erro", msg)
            stbar.showMessage("Falha no deslocamento")

        self._move_thread.finished.connect(_on_done)
        self._move_thread.error.connect(_on_err)
        self._move_thread.start()

    def _execute_resume_and_update(self):
        """Executa o resumo após parada e força atualização de posição em sequência"""
        try:
            # Primeiro envia o comando para retomar após hold
            self.controller.cnc.grbl.send_immediately("~")
            logger.debug("MOVIMENTO: Enviado comando de retomada (~)")

            # --- INÍCIO DA MODIFICAÇÃO ---
            # REMOVIDO: Chamada para _force_position_update. A atualização agora
            # dependerá do polling regular iniciado em connect_cnc.
            # QTimer.singleShot(150, lambda: self._force_position_update(1))
            logger.debug("MOVIMENTO: Atualização de posição dependerá do polling regular.")
            # --- FIM DA MODIFICAÇÃO ---

        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao executar sequência de retomada: {e}")
            
    # A função _force_position_update pode ser mantida, mas não será mais chamada
    # a partir de _execute_resume_and_update.
    def _force_position_update(self, attempt=1):
        """Força múltiplas atualizações de posição para garantir precisão

        Args:
            attempt: Número da tentativa atual (para limitar tentativas)
        """
        if not hasattr(self.controller.cnc, 'grbl') or not self.controller.cnc.is_connected:
            return

        try:
            # Envia comando de status para obter posição atualizada
            # --- INÍCIO DA MODIFICAÇÃO ---
            # logger.debug(f"MOVIMENTO: Forçando atualização de posição - tentativa {attempt}") # REMOVIDO/COMENTADO
            # --- FIM DA MODIFICAÇÃO ---
            self.controller.cnc.grbl.send_immediately("?")

            # Se ainda estamos dentro do limite de tentativas, agenda outra verificação
            if attempt < 3:
                # Aumento progressivo do tempo entre tentativas (150ms, 200ms, 250ms)
                delay = 150 + (attempt * 50)
                # A chamada recursiva ainda existe, mas o log dentro dela foi removido
                QTimer.singleShot(delay, lambda: self._force_position_update(attempt + 1))

        except Exception as e:
            # Manter o log de erro
            logger.error(f"MOVIMENTO: Erro ao forçar atualização de posição: {e}")
            
    def set_motion_mode(self, mode):
        """Set the motion mode (G90/G91)"""
        # Se for PLC, não existe GRBL: apenas atualiza UI e guarda modo internamente
        
        if isinstance(self.controller.cnc, PLCAxisController):
            if mode == "G90":
                self.mode_absolute.setChecked(True)
                self.mode_relative.setChecked(False)
            else:
                self.mode_absolute.setChecked(False)
                self.mode_relative.setChecked(True)
            # opcional: armazenar no controller para referência futura
            self.controller.cnc.current_motion_mode = mode
            logger.info(f"MOVIMENTO (PLC): modo de movimento definido para {mode}")
            return

        # Se não estiver conectado (nem PLC, nem GRBL), só atualiza UI e volta
        if not self.controller.cnc.is_connected:
            if mode == "G90":
                self.mode_absolute.setChecked(True)
                self.mode_relative.setChecked(False)
            else:
                self.mode_absolute.setChecked(False)
                self.mode_relative.setChecked(True)
            logger.warning(f"MOVIMENTO: CNC não conectada, modo {mode} definido apenas na UI.")
            return

        # Atualiza a UI (GRBL)
        if mode == "G90":
            self.mode_absolute.setChecked(True)
            self.mode_relative.setChecked(False)
        else:  # G91
            self.mode_absolute.setChecked(False)
            self.mode_relative.setChecked(True)
        # Envia o comando G90/G91 para o GRBL
        try:
            logger.debug(f"MOVIMENTO: Definindo modo de movimento para {mode}")
            self.controller.cnc.grbl.send_immediately(mode)
        except Exception as e:
            logger.error(f"MOVIMENTO: Erro ao definir modo de movimento: {e}")
            QMessageBox.warning(self, "Error", f"Error setting motion mode: {e}")

    def on_emergency_stop_toggle(self, checked):
        """
        Manipula o clique no botão Emergency Stop/Reset.
        """
        is_plc = isinstance(self.controller.cnc, PLCAxisController)

        if not hasattr(self.controller.cnc, 'is_connected') or not self.controller.cnc.is_connected:
            QMessageBox.warning(self, "Erro", "CNC não conectada")
            self.emergency_stop_button.setChecked(not checked)
            return

        if checked:
            # Botão foi pressionado para entrar no modo RESET
            logger.info("EMERGENCY STOP: Botão pressionado. Enviando Soft Reset.")
            if self.controller.cnc.send_soft_reset():
                # Configura visual do botão para Reset
                self.emergency_stop_button.setText("Reset")
                self.emergency_stop_button.setStyleSheet("background-color: orange; color: black;")

                # Atualiza status
                main_window = self.window()
                if hasattr(main_window, 'statusBar'):
                    main_window.statusBar().showMessage("Máquina parada. Clique em Reset para desbloquear.")
            else:
                # Soft reset falhou, reverte o botão
                logger.error("EMERGENCY STOP: Falha ao enviar Soft Reset")
                QMessageBox.critical(self, "Erro", "Falha ao enviar comando de parada")
                self.emergency_stop_button.setChecked(False)
        else:
            # Botão foi pressionado para sair do modo RESET
            logger.info(
                "RESET: Botão pressionado para desbloquear.%s",
                " Enviando $X." if not is_plc else " Liberando PLC."
            )
            if self.controller.cnc.unlock():
                # Configura visual do botão para STOP
                self.emergency_stop_button.setText("STOP")
                self.emergency_stop_button.setStyleSheet("background-color: red; color: white;")

                # Atualiza status
                main_window = self.window()
                if hasattr(main_window, 'statusBar'):
                    main_window.statusBar().showMessage("Máquina desbloqueada e pronta.")

                # Solicita atualização de status para verificar nova condição (apenas GRBL)
                if hasattr(self.controller.cnc, "grbl") and getattr(self.controller.cnc, "grbl", None):
                    QTimer.singleShot(200, lambda: self.controller.cnc.grbl.send_immediately("?"))
            else:
                # Desbloqueio falhou, reverte o botão
                logger.error("RESET: Falha ao enviar comando de desbloqueio")
                QMessageBox.critical(self, "Erro", "Falha ao desbloquear a máquina")
                self.emergency_stop_button.setChecked(True)

    def _auto_unlock_after_reset(self):
        """Executa sequência automática de desbloqueio após reset de emergência"""
        logger.info("AUTO UNLOCK: Iniciando sequência de desbloqueio automático após reset")
        
        try:
            # 1. Envia comando de desbloqueio
            self.controller.cnc.grbl.send_immediately("$X")
            logger.info("AUTO UNLOCK: Comando $X enviado")
            
            # 2. Pequena pausa
            QTimer.singleShot(200, lambda: self._check_if_unlocked())
        except Exception as e:
            logger.error(f"AUTO UNLOCK: Erro ao enviar comando de desbloqueio: {e}")
            main_window = self.window()
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage(f"Erro no desbloqueio automático: {e}")

    def _check_if_unlocked(self):
        """Verifica se o desbloqueio foi bem-sucedido e restaura configurações se necessário"""
        try:
            # Solicita status para conferir se saiu do alarme
            self.controller.cnc.grbl.send_immediately("?")

            # Exibe mensagem de sucesso
            main_window = self.window()
            if hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage("Sistema parado e desbloqueado automaticamente.")

            logger.info("AUTO UNLOCK: Sequência de desbloqueio automático concluída")
        except Exception as e:
            logger.error(f"AUTO UNLOCK: Erro ao verificar status após desbloqueio: {e}")




