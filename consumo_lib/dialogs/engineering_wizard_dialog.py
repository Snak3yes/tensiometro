"""
EngineeringWizardDialog - Dialogo principal do Engineering Wizard

Este módulo implementa o dialogo principal que orquestra as 7 abas do
Engineering Wizard, gerenciando estado compartilhado e navegação.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QProgressBar, QMessageBox,
    QWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from consumo_lib.models.engineering.wizard_state import EngineeringWizardState
from consumo_lib.widgets.engenharia import (
    ProgramDataWidget,
    GerberUploadWidget,
    FiducialCaptureWidget,
    MosaicCaptureWidget,
    AlignmentWidget,
    InspectionWindowsWidget,
    ConfirmSaveWidget
)
from consumo_lib.utils.ux_helpers import (
    setup_engineering_wizard_shortcuts,
    set_tooltip,
    ENGINEERING_WIZARD_TOOLTIPS
)
from aoi_lib.config_manager import AOIConfigManager

logger = logging.getLogger(__name__)


class EngineeringWizardDialog(QDialog):
    """
    Dialogo principal do Engineering Wizard.

    Orquestra as 7 abas do wizard, gerenciando navegação, validação
    e estado compartilhado entre todas as abas.

    Attributes:
        state: Estado compartilhado entre todas as abas
        current_tab: Índice da aba atual (0-6)
        auto_save_timer: QTimer para auto-save periódico
    """

    # Signals
    state_changed = pyqtSignal(object)  # EngineeringWizardState
    program_completed = pyqtSignal(dict)  # ProgramConfig

    def __init__(self, parent=None):
        """Inicializa o Engineering Wizard Dialog.

        Args:
            parent: Widget pai
        """
        super().__init__(parent)

        self.state = EngineeringWizardState()
        self.current_tab = 0
        self.auto_save_timer = QTimer()  # Removido - não necessário

        self.auto_save_timer.timeout.connect(self._on_auto_save)

        # Carregar configuração de navegação livre
        self.config_manager = AOIConfigManager()
        self.free_navigation_mode = self.config_manager.get_free_navigation_enabled()

        # NOTA: MovementControlWidget não precisa mais ser passado
        # O FiducialCaptureWidget encontrará a CNCControlTab automaticamente

        self._setup_ui()
        self._connect_signals()
        self._update_ui_state()
        self._setup_keyboard_shortcuts()
        self._setup_tooltips()
        self._update_title_for_free_navigation()

        # NOTA: Chamar set_wizard_mode(True) após criar abas
        QTimer.singleShot(100, self._on_wizard_opened)

        logger.info(f"📋 EngineeringWizardDialog inicializado (free_navigation={self.free_navigation_mode})")

    def _on_wizard_opened(self):
        """
        Chamado quando wizard é aberto (100ms após __init__).

        Notifica a CNCControlTab para ocultar o movement_widget
        e mostra placeholder no lugar.
        """
        # Buscar CNCControlTab e alternar visibilidade
        if hasattr(self, 'tab_fiducial_capture') and self.tab_fiducial_capture is not None:
            parent_tab = self._find_parent_cnc_control_tab(self.tab_fiducial_capture)

            if parent_tab is not None:
                parent_tab.set_wizard_mode(True)
                logger.info("📖 MovementControlWidget oculto na aba principal (wizard aberto)")
            else:
                logger.warning("⚠️ CNCControlTab não encontrado para notificar abertura")
        else:
            logger.warning("ⓖ FiducialCaptureWidget não disponível para notificar abertura")

    def _find_parent_cnc_control_tab(self, widget=None):
        """
        Busca recursivamente pela CNCControlTab na hierarquia de widgets.

        SOBRE APENAS PAIS (não busca em filhos para evitar recursão infinita).

        Args:
            widget: Widget atual na busca (padrão: self)
            visited: Conjunto de IDs já visitados para evitar loops

        Returns:
            CNCControlTab se encontrada, None caso contrário
        """
        if widget is None:
            widget = self

        # Inicializa conjunto de visitados
        if visited is None:
            visited = set()

        # Proteção contra loops: rastreia widgets visitados por ID
        widget_id = id(widget)
        if widget_id in visited:
            logger.debug("⚠️ Loop detectado em _find_parent_cnc_control_tab, widget já visitado")
            return None
        visited.add(widget_id)

        # Se este widget é CNCControlTab, retorna
        if widget.__class__.__name__ == 'CNCControlTab':
            logger.debug("✅ CNCControlTab encontrado")
            return widget

        # Busca APENAS no pai (não busca em filhos para evitar explosão combinatória)
        if widget.parent() is not None:
            return self._find_parent_cnc_control_tab(widget.parent(), visited)

        logger.debug("ℹ️ CNCControlTab não encontrado na hierarquia")
        return None

    def _setup_ui(self):
        """Configura a interface do usuario."""
        self.setWindowTitle("Engineering Wizard - Novo Programa de Inspeção")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Barra de progresso no topo
        self._create_progress_bar(main_layout)

        # Tab widget com as 7 abas
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)
        self._create_tabs()
        main_layout.addWidget(self.tab_widget)

        # Barra de botoes
        self._create_button_bar(main_layout)

        # Configurar auto-save (2 minutos)
        self.auto_save_timer.start(120000)  # 120000 ms = 2 minutos

        logger.debug("✓ UI configurada")

    def _create_progress_bar(self, parent_layout):
        """Cria a barra de progresso no topo do dialogo."""
        progress_layout = QVBoxLayout()
        progress_layout.setContentsMargins(0, 0, 0, 5)

        # Label com texto de progresso
        self.progress_label = QLabel("Etapa 1 de 7: Dados do Programa")
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.progress_label.setFont(font)
        progress_layout.addWidget(self.progress_label)

        # Barra de progresso visual
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 7)
        self.progress_bar.setValue(1)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / 7")
        progress_layout.addWidget(self.progress_bar)

        parent_layout.addLayout(progress_layout)
        logger.debug("✓ Barra de progresso criada")

    def _create_tabs(self):
        """Cria as 7 abas do wizard."""
        # Aba 1: Dados do Programa
        self.tab_program_data = ProgramDataWidget()
        self.tab_widget.addTab(self.tab_program_data, "1. Dados do Programa")

        # Aba 2: Carregar Gerber
        self.tab_gerber_upload = GerberUploadWidget()
        self.tab_widget.addTab(self.tab_gerber_upload, "2. Carregar Gerber")

        # Aba 3: Definir Fiduciais
        self.tab_fiducial_capture = FiducialCaptureWidget()
        self.tab_widget.addTab(self.tab_fiducial_capture, "3. Definir Fiduciais")

        # Aba 4: Capturar Mosaico
        self.tab_mosaic_capture = MosaicCaptureWidget()
        self.tab_widget.addTab(self.tab_mosaic_capture, "4. Capturar Mosaico")

        # Aba 5: Alinhamento
        self.tab_alignment = AlignmentWidget()
        self.tab_widget.addTab(self.tab_alignment, "5. Alinhamento")

        # Aba 6: Janelas de Inspeção
        self.tab_inspection_windows = InspectionWindowsWidget()
        self.tab_widget.addTab(self.tab_inspection_windows, "6. Janelas de Inspeção")

        # Aba 7: Confirmar e Salvar
        self.tab_confirm_save = ConfirmSaveWidget()
        self.tab_widget.addTab(self.tab_confirm_save, "7. Confirmar e Salvar")

        # Desabilitar abas subsequentes inicialmente (apenas em modo normal)
        if not self.free_navigation_mode:
            # MODO NORMAL: Desabilitar abas 1-6 inicialmente (navegação sequencial)
            for i in range(1, 7):
                self.tab_widget.setTabEnabled(i, False)
            logger.debug("✓ Abas desabilitadas (modo normal)")
        else:
            # MODO LIVRE: Todas as abas habilitadas (navegação livre)
            logger.debug("✓ Abas habilitadas (modo navegação livre)")

        # Atualizar labels com indicadores visuais
        self._update_tab_labels()

        logger.debug("✓ 7 abas criadas")

    def _create_button_bar(self, parent_layout):
        """Cria a barra de botoes na parte inferior."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.addStretch()

        # Botao Anterior
        self.btn_previous = QPushButton("< Anterior")
        self.btn_previous.setMinimumWidth(120)
        self.btn_previous.setEnabled(False)
        button_layout.addWidget(self.btn_previous)

        # Botao Proximo
        self.btn_next = QPushButton("Próximo >")
        self.btn_next.setMinimumWidth(120)
        self.btn_next.setDefault(True)
        button_layout.addWidget(self.btn_next)

        # Botao Cancelar
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setMinimumWidth(120)
        button_layout.addWidget(self.btn_cancel)

        # Botao Concluir
        self.btn_finish = QPushButton("Concluir")
        self.btn_finish.setMinimumWidth(120)
        self.btn_finish.setEnabled(False)
        button_layout.addWidget(self.btn_finish)

        parent_layout.addLayout(button_layout)
        logger.debug("✓ Barra de botoes criada")

    def _setup_keyboard_shortcuts(self):
        """Configura atalhos de teclado do wizard."""
        setup_engineering_wizard_shortcuts(self)
        logger.debug("⌨️ Atalhos de teclado configurados")

    def _setup_tooltips(self):
        """Configura tooltips nos botões principais."""
        # Botões de navegação
        set_tooltip(self.btn_previous, 'previous_btn')
        self.btn_previous.setToolTip(
            "Voltar para aba anterior\n\n"
            "Atalho: Ctrl + ←"
        )

        set_tooltip(self.btn_next, 'next_btn')
        self.btn_next.setToolTip(
            "Avançar para próxima aba\n\n"
            "Requer: Aba atual completa\n"
            "Atalho: Ctrl + →"
        )

        set_tooltip(self.btn_cancel, 'cancel_btn')
        self.btn_cancel.setToolTip(
            "Cancelar wizard\n\n"
            "Alterações não salvas serão perdidas\n"
            "Atalho: Esc"
        )

        set_tooltip(self.btn_finish, 'finish_btn')
        self.btn_finish.setToolTip(
            "Concluir e salvar programa\n\n"
            "Requer: Todas as abas completas\n"
            "Atalho: Ctrl + Enter"
        )

        logger.debug("💡 Tooltips configurados")

    def _connect_signals(self):
        """Conecta sinais dos widgets e botoes."""
        # Botoes de navegacao
        self.btn_previous.clicked.connect(self._on_previous)
        self.btn_next.clicked.connect(self._on_next)
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_finish.clicked.connect(self._on_finish)

        # Mudanca de aba
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Signals das abas (para atualizar estado)
        self.tab_program_data.data_changed.connect(self._on_program_data_changed)
        self.tab_program_data.validation_changed.connect(self._on_validation_changed)

        self.tab_gerber_upload.gerber_loaded.connect(self._on_gerber_loaded)
        self.tab_gerber_upload.validation_changed.connect(self._on_validation_changed)

        self.tab_fiducial_capture.fiducial_captured.connect(self._on_fiducial_captured)
        self.tab_fiducial_capture.validation_changed.connect(self._on_validation_changed)

        self.tab_mosaic_capture.mosaic_captured.connect(self._on_mosaic_captured)
        self.tab_mosaic_capture.validation_changed.connect(self._on_validation_changed)

        self.tab_alignment.alignmentApplied.connect(self._on_alignment_completed)
        self.tab_alignment.validationChanged.connect(self._on_validation_changed)

        self.tab_inspection_windows.group_count_changed.connect(self._on_inspection_groups_changed)
        self.tab_inspection_windows.validation_changed.connect(self._on_validation_changed)

        self.tab_confirm_save.save_requested.connect(self._on_save_confirmed)

        logger.debug("✓ Signals conectados")

    def _on_previous(self):
        """Handler para botao Anterior."""
        if self.current_tab > 0:
            self.tab_widget.setCurrentIndex(self.current_tab - 1)
        logger.info(f"⬅️ Voltou para aba {self.current_tab}")

    def _on_next(self):
        """Handler para botao Proximo."""
        if self.current_tab < 6:
            # MODO LIVRE: Pular validações e avançar diretamente
            if self.free_navigation_mode:
                self.tab_widget.setCurrentIndex(self.current_tab + 1)
                logger.info(f"➡️ MODO LIVRE: Avançou para aba {self.current_tab + 1} (sem validação)")
                return

            # MODO NORMAL: Validar aba atual antes de avançar
            if not self.state.is_valid(self.current_tab):
                # Obter mensagem específica de validação
                validation_msg = self.state.get_validation_message(self.current_tab)
                QMessageBox.warning(
                    self,
                    "⚠️ Aba Incompleta",
                    f"Complete a aba atual antes de avançar.\n\n{validation_msg}"
                )
                logger.warning(f"⚠️ Tentou avançar com aba {self.current_tab} inválida")
                return

            # Validar dependencias
            can_proceed, message = self.state.can_proceed_to_tab(self.current_tab + 1)
            if not can_proceed:
                QMessageBox.warning(
                    self,
                    "⚠️ Dependências Não Atendidas",
                    message
                )
                logger.warning(f"⚠️ Dependências não atendidas: {message}")
                return

            self.tab_widget.setCurrentIndex(self.current_tab + 1)
            logger.info(f"➡️ Avançou para aba {self.current_tab}")

    def _on_cancel(self):
        """Handler para botao Cancelar."""
        # PRIMEIRO: Notificar CNCControlTab para restaurar o movement_widget
        try:
            parent_tab = self._find_parent_cnc_control_tab(self.tab_fiducial_capture)

            if parent_tab is not None:
                parent_tab.set_wizard_mode(False)
                logger.info("✅ MovementControlWidget restaurado à aba principal (cancelamento)")
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar MovementControlWidget no cancel: {e}")

        # Depois, processa o cancelamento normalmente
        if self.state.is_dirty:
            reply = QMessageBox.question(
                self,
                "Cancelar Engineering Wizard",
                "Há mudanças não salvas. Deseja realmente cancelar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._cleanup_auto_saves()
                self.reject()
                logger.info("❌ Wizard cancelado pelo usuário")
        else:
            self.reject()
            logger.info("❌ Wizard cancelado (sem mudanças)")

    def _on_finish(self):
        """Handler para botao Concluir."""
        # Validar todas as abas
        all_valid = all(self.state.is_valid(i) for i in range(7))
        if not all_valid:
            QMessageBox.warning(
                self,
                "Validação",
                "Complete todas as abas antes de concluir."
            )
            logger.warning("⚠️ Tentou concluir com abas inválidas")
            return

        # Confirmar salvamento
        reply = QMessageBox.question(
            self,
            "Concluir Engineering Wizard",
            "Deseja salvar o programa de inspeção?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Compilar configuracao final
            program_config = self._compile_program_config()
            self.state.program_config = program_config
            self.state.update_timestamp()

            # Emitir signal de conclusao
            self.program_completed.emit(program_config)

            # Limpar auto-saves
            self._cleanup_auto_saves()

            # PRIMEIRO: Notificar CNCControlTab para restaurar o movement_widget
            try:
                parent_tab = self._find_parent_cnc_control_tab(self.tab_fiducial_capture)

                if parent_tab is not None:
                    parent_tab.set_wizard_mode(False)
                    logger.info("✅ MovementControlWidget restaurado à aba principal (conclusão)")
            except Exception as e:
                logger.error(f"❌ Erro ao restaurar MovementControlWidget na conclusão: {e}")

            self.accept()
            logger.info("✅ Engineering Wizard concluído com sucesso")
        else:
            logger.info("❌ Usuário cancelou conclusão")

    def _on_tab_changed(self, index: int):
        """Handler para mudanca de aba."""
        # MODO LIVRE: Permitir qualquer navegação sem validações
        if self.free_navigation_mode:
            old_tab = self.current_tab
            self.current_tab = index
            self.state.current_tab = index

            # Atualizar barra de progresso
            self.progress_label.setText(f"Etapa {index + 1} de 7: {self._get_tab_name(index)}")
            self.progress_bar.setValue(index + 1)

            # Atualizar estado dos botoes
            self._update_button_states()

            logger.debug(f"🔄 MODO LIVRE: Mudou da aba {old_tab} para aba {index} (sem validação)")
            return

        # MODO NORMAL: Bloquear navegação para abas não permitidas
        if index > self.current_tab:
            # Tentando avançar - validar dependências
            can_proceed, message = self.state.can_proceed_to_tab(index)
            if not can_proceed:
                # Bloquear mudança de aba
                QMessageBox.warning(
                    self,
                    "⚠️ Navegação Bloqueada",
                    f"{message}\n\nComplete as etapas anteriores para continuar."
                )
                # Reverter para aba atual
                self.tab_widget.blockSignals(True)
                self.tab_widget.setCurrentIndex(self.current_tab)
                self.tab_widget.blockSignals(False)
                logger.warning(f"⚠️ Tentou navegar para aba {index} sem permissão")
                return

        old_tab = self.current_tab
        self.current_tab = index
        self.state.current_tab = index

        # Atualizar barra de progresso
        self.progress_label.setText(f"Etapa {index + 1} de 7: {self._get_tab_name(index)}")
        self.progress_bar.setValue(index + 1)

        # Atualizar estado dos botoes
        self._update_button_states()

        logger.debug(f"🔄 Mudou da aba {old_tab} para aba {index}")

    def _update_title_for_free_navigation(self):
        """Atualiza título do dialog com indicador de modo livre."""
        base_title = "Engineering Wizard - Novo Programa de Inspeção"
        if self.free_navigation_mode:
            self.setWindowTitle(f"🔓 {base_title} [Navegação Livre]")
        else:
            self.setWindowTitle(base_title)

    def _get_tab_name(self, index: int) -> str:
        """Retorna o nome da aba."""
        names = [
            "Dados do Programa",
            "Carregar Gerber",
            "Definir Fiduciais",
            "Capturar Mosaico",
            "Alinhamento",
            "Janelas de Inspeção",
            "Confirmar e Salvar"
        ]
        return names[index] if 0 <= index < len(names) else "Desconhecido"

    def _update_button_states(self):
        """Atualiza estado habilitado/desabilitado dos botoes."""
        # Botao Anterior
        self.btn_previous.setEnabled(self.current_tab > 0)

        # Botao Proximo
        can_next = self.current_tab < 6 and self.state.is_valid(self.current_tab)
        self.btn_next.setEnabled(can_next)

        # Botao Concluir (so na ultima aba)
        is_last_tab = self.current_tab == 6
        all_valid = all(self.state.is_valid(i) for i in range(7))
        self.btn_finish.setEnabled(is_last_tab and all_valid)

    def _update_ui_state(self):
        """Atualiza o estado da UI baseado no estado compartilhado."""
        self._update_button_states()

        # MODO LIVRE: Não desabilitar abas (todas permanecem habilitadas)
        if self.free_navigation_mode:
            logger.debug("🔓 MODO LIVRE: Pulando desabilitação de abas")
        else:
            # MODO NORMAL: Habilitar abas subsequentes se dependencias atendidas
            for i in range(1, 7):
                can_proceed, _ = self.state.can_proceed_to_tab(i)
                self.tab_widget.setTabEnabled(i, can_proceed)

        # Atualizar labels com indicadores visuais
        self._update_tab_labels()

    def _update_tab_labels(self):
        """Atualiza os nomes das abas com indicadores visuais de validação."""
        tab_names = [
            "1. Dados do Programa",
            "2. Carregar Gerber",
            "3. Definir Fiduciais",
            "4. Capturar Mosaico",
            "5. Alinhamento",
            "6. Janelas de Inspeção",
            "7. Confirmar e Salvar"
        ]

        for i in range(7):
            base_name = tab_names[i]
            # Adicionar indicador visual
            if self.state.is_valid(i):
                # Aba completa - adiciona checkmark
                self.tab_widget.setTabText(i, f"{base_name} ✓")
            else:
                # Aba incompleta - sem indicador ou com aviso
                self.tab_widget.setTabText(i, base_name)

        logger.debug("🏷️ Labels das abas atualizados")

    # ========================
    # Handlers de signals das abas
    # ========================

    def _on_program_data_changed(self, data: Dict[str, Any]):
        """Handler para mudanca de dados do programa (Aba 1)."""
        self.state.program_data = data
        self.state.update_timestamp()
        self.state_changed.emit(self.state)
        logger.debug("📝 Dados do programa atualizados")

    def _on_gerber_loaded(self, data: Dict[str, Any]):
        """Handler para Gerber carregado (Aba 2)."""
        self.state.gerber_data = data
        self.state.gerber_file = data.get('file_path')
        self.state.update_timestamp()
        self.state_changed.emit(self.state)

        # Habilitar aba 3
        self.tab_widget.setTabEnabled(2, True)
        logger.debug("📄 Arquivo Gerber carregado")

    def _on_fiducial_captured(self, data: Dict[str, Any]):
        """Handler para fiducial capturado (Aba 3)."""
        fiducials = self.state.fiducial_templates
        fiducials.append(data)
        self.state.update_timestamp()
        self.state_changed.emit(self.state)

        if len(fiducials) >= 2:
            # Habilitar aba 4
            self.tab_widget.setTabEnabled(3, True)
        logger.debug(f"🎯 Fiducial capturado ({len(fiducials)}/2)")

    def _on_mosaic_captured(self, data: Dict[str, Any]):
        """Handler para mosaico capturado (Aba 4)."""
        self.state.mosaic_config = data
        self.state.mosaic_image_path = data.get('image_path')
        self.state.update_timestamp()
        self.state_changed.emit(self.state)

        # Habilitar aba 5
        self.tab_widget.setTabEnabled(4, True)
        logger.debug("🖼️ Mosaico capturado")

    def _on_alignment_completed(self, data: Dict[str, Any]):
        """Handler para alinhamento concluído (Aba 5)."""
        self.state.alignment_transform = data
        self.state.update_timestamp()
        self.state_changed.emit(self.state)

        # Habilitar aba 6
        self.tab_widget.setTabEnabled(5, True)
        logger.debug("🔧 Alinhamento concluído")

    def _on_inspection_groups_changed(self, group_count: int):
        """Handler para grupos de inspeção mudaram (Aba 6)."""
        # Atualiza estado apenas com o count (a lista será obtida do widget quando necessário)
        if group_count > 0:
            # Habilitar aba 7
            self.tab_widget.setTabEnabled(6, True)
        logger.debug(f"🔍 Grupos de inspeção atualizados ({group_count} grupos)")

    def _on_validation_changed(self, is_valid: bool):
        """Handler para mudanca de validacao de qualquer aba."""
        self._update_button_states()
        self._update_ui_state()
        logger.debug(f"✅ Validação mudou: aba {self.current_tab} = {is_valid}")

    def _on_save_confirmed(self, save_data: Dict[str, Any]):
        """Handler para confirmacao de salvamento (Aba 7)."""
        logger.debug("💾 Salvamento confirmado na aba 7")
        self._on_finish()

    # ========================
    # Auto-Save
    # ========================

    def _on_auto_save(self):
        """Handler para timer de auto-save."""
        if self.state.is_dirty:
            self._save_auto_save()
            logger.debug("💾 Auto-save executado")

    def _save_auto_save(self):
        """Salva estado atual em arquivo de auto-save."""
        autosave_dir = Path("data/inspection_programs/.autosaves")
        autosave_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = autosave_dir / f".autosave_{timestamp}.json"

        try:
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.state.to_dict(), f, indent=2, ensure_ascii=False)

            self.state.auto_save_path = str(filename)
            logger.info(f"💾 Auto-save salvo: {filename}")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar auto-save: {e}")

    def _load_auto_save(self) -> Optional[Dict[str, Any]]:
        """Carrega auto-save mais recente se existir."""
        autosave_dir = Path("data/inspection_programs/.autosaves")
        if not autosave_dir.exists():
            return None

        # Encontrar auto-save mais recente
        autosaves = sorted(autosave_dir.glob(".autosave_*.json"), reverse=True)
        if not autosaves:
            return None

        latest_autosave = autosaves[0]
        try:
            import json
            with open(latest_autosave, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"📥 Auto-save carregado: {latest_autosave}")
            return data
        except Exception as e:
            logger.error(f"❌ Erro ao carregar auto-save: {e}")
            return None

    def _cleanup_auto_saves(self):
        """Limpa arquivos de auto-save."""
        autosave_dir = Path("data/inspection_programs/.autosaves")
        if autosave_dir.exists():
            try:
                import shutil
                shutil.rmtree(autosave_dir)
                logger.info("🧹 Auto-saves limpos")
            except Exception as e:
                logger.error(f"❌ Erro ao limpar auto-saves: {e}")

    # ========================
    # Compilação de Programa
    # ========================

    def _compile_program_config(self) -> Dict[str, Any]:
        """Compila configuracao final do programa."""
        # Obter grupos de inspeção do widget
        inspection_groups = getattr(self.tab_inspection_windows, 'get_groups', lambda: [])()

        return {
            'program_name': self.state.program_data.get('program_name'),
            'stencil_code': self.state.program_data.get('stencil_code'),
            'description': self.state.program_data.get('description'),
            'version': self.state.program_data.get('version'),
            'created_by': self.state.program_data.get('created_by'),
            'created_at': self.state.program_data.get('created_at'),

            'gerber_file': self.state.gerber_file,
            'gerber_data': self.state.gerber_data,

            'fiducial_templates': self.state.fiducial_templates,

            'mosaic_config': self.state.mosaic_config,
            'mosaic_image_path': self.state.mosaic_image_path,

            'alignment_transform': self.state.alignment_transform,

            'inspection_groups': inspection_groups,

            'metadata': {
                'wizard_version': '1.0.0',
                'completed_at': datetime.now().isoformat()
            }
        }

    # ========================
    # Sobrecarga de closeEvent
    # ========================

    def closeEvent(self, event):
        """Handler para fechamento do dialogo."""
        # PRIMEIRO: Notificar CNCControlTab para restaurar o movement_widget
        try:
            parent_tab = self._find_parent_cnc_control_tab(self.tab_fiducial_capture)

            if parent_tab is not None:
                parent_tab.set_wizard_mode(False)
                logger.info("✅ MovementControlWidget restaurado à aba principal (wizard fechado)")
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar MovementControlWidget: {e}")

        # Depois, processa o fechamento normal
        if self.state.is_dirty:
            reply = QMessageBox.question(
                self,
                "Fechar Engineering Wizard",
                "Há mudanças não salvas. Deseja realmente fechar?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._cleanup_auto_saves()
                event.accept()
                logger.info("🚪 Dialogo fechado (mudanças descartadas)")
            else:
                event.ignore()
                logger.info("🚪 Fechamento cancelado pelo usuário")
        else:
            self._cleanup_auto_saves()
            event.accept()
            logger.info("🚪 Dialogo fechado (sem mudanças)")
