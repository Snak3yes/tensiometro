"""
FiducialCaptureWidget - Widget de Captura de Fiduciais (Aba 3 do Engineering Wizard)

Este widget permite capturar templates dos 2 fiduciais do stencil
usados para alinhamento automático.

Funcionalidades:
- Preview de câmera em tempo real
- Clique para capturar template
- Definição de posição XYZ
- Preview do template capturado
- Validação de qualidade

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QGroupBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QImage
import numpy as np

# Design System
from consumo_lib.ui import COLORS, TYPO, SPACE, DIM

# Import para criar MovementControlWidget na aba 3
from consumo_lib.widgets.movement_control import MovementControlWidget
# Import para usar CameraCaptureWidget unificado
from consumo_lib.widgets.camera_capture import CameraCaptureWidget

logger = logging.getLogger(__name__)


@dataclass
class FiducialTemplate:
    """Template de fiducial capturado."""
    id: int
    x: float
    y: float
    z: float
    image: np.ndarray
    window_size: int = 50
    captured_at: str = ""

    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'window_size': self.window_size,
            'captured_at': self.captured_at
        }

class FiducialCaptureWidget(QWidget):
    """
    Widget para capturar templates dos 2 fiduciais.

    Signals:
        fiducial_captured(dict): Emitido quando fiducial é capturado
        validation_changed(bool): Emitido quando validação muda
    """

    fiducial_captured = pyqtSignal(dict)
    validation_changed = pyqtSignal(bool)

    def __init__(self, parent=None, hardware_coordinator=None, cnc_control_tab=None):
        """Inicializa o widget.

        Args:
            parent: Widget pai
            hardware_coordinator: EngineeringHardwareCoordinator (opcional)
            cnc_control_tab: CNCControlTab para compartilhar MovementControlWidget (opcional)
        """
        super().__init__(parent)
        logger.info("🎨 Inicializando FiducialCaptureWidget")

        # Estado
        self._fiducials: List[FiducialTemplate] = []
        self._current_fiducial_id = 0  # 0 ou 1
        self._window_size = 50
        self._is_valid = False

        # Hardware coordinator (nova arquitetura)
        self._hardware_coordinator = hardware_coordinator
        # Legado: camera_controller (para compatibilidade)
        self._camera_controller = None

        # CNCControlTab passada como parâmetro (prioridade sobre busca recursiva)
        self._cnc_control_tab = cnc_control_tab
        self._movement_widget = None

        # Setup UI
        self._setup_ui()

        # Conectar signals
        self._connect_signals()

        # Atualizar estado inicial
        self._update_hardware_status()

        logger.info("✅ FiducialCaptureWidget inicializado")

    def set_hardware_coordinator(self, coordinator):
        """Define o coordenador de hardware (injeção de dependência).

        Args:
            coordinator: EngineeringHardwareCoordinator
        """
        self._hardware_coordinator = coordinator
        self._update_hardware_status()
        logger.info("🔧 Hardware coordinator definido")

    def _update_hardware_status(self):
        """Atualiza display de status do hardware."""
        # Verificar se hardware está disponível
        has_coordinator = self._hardware_coordinator is not None
        has_camera = self._camera_controller is not None

        if has_coordinator:
            # Usar coordinator
            from consumo_lib.coordinators.engineering_hardware_coordinator import HardwareType
            ready, _ = self._hardware_coordinator.is_hardware_ready([
                HardwareType.CAMERA,
                HardwareType.PLC
            ])
            status = "✅ Pronto" if ready else "⚠️ Hardware não conectado"
        elif has_camera:
            # Modo legado
            ready = self._camera_controller.is_connected
            status = "✅ Pronto" if ready else "⚠️ Câmera não conectada"
        else:
            status = "❌ Sem hardware"

        # Se existir label de hardware status, atualizar
        if hasattr(self, 'lbl_hardware_status'):
            self.lbl_hardware_status.setText(f"Hardware: {status}")

    def _setup_ui(self):
        """Configura interface do usuário."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Layout principal (preview | coluna direita)
        main_layout = QHBoxLayout()

        # Preview da câmera (usa CameraCaptureWidget unificado)
        preview_group = QGroupBox("Preview da Câmera")
        preview_layout = QVBoxLayout(preview_group)

        # Criar CameraCaptureWidget
        # NOTA: Precisamos injetar controller e cfg depois via set_camera_controller
        # Por enquanto, cria sem parâmetros (será configurado depois)
        self.camera_capture = CameraCaptureWidget(
            controller=None,  # Será injetado depois
            cfg=None,  # Será injetado depois
            click_to_move_service=None,  # Opcional
            fov_converter=None  # Opcional
        )
        preview_layout.addWidget(self.camera_capture, 1)

        main_layout.addWidget(preview_group, 2)

        # Coluna direita (Controle de Movimento + Controles de Captura)
        right_column = QVBoxLayout()

        # Controles de movimento (CRIAR NOVA INSTÂNCIA)
        # A nova instância compartilha o MESMO estado via controller/orchestrator
        if self._movement_widget is None and self._cnc_control_tab is not None:
            # Usa CNCControlTab passada como parâmetro
            if hasattr(self._cnc_control_tab, 'controller') and hasattr(self._cnc_control_tab, 'config_manager'):
                # Criar nova instância do MovementControlWidget com os MESMOS parâmetros
                self._movement_widget = MovementControlWidget(
                    self._cnc_control_tab.controller,
                    self._cnc_control_tab.config_manager,
                    orchestrator=self._cnc_control_tab.orchestrator
                )
                logger.info("✅ Nova instância de MovementControlWidget criada para aba 3")
            else:
                logger.warning("⚠️ CNCControlTab não possui controller/config_manager necessários")
        elif self._movement_widget is None:
            logger.warning("⚠️ CNCControlTab não foi passada como parâmetro - não foi possível criar MovementControlWidget")

        # Adicionar MovementControlWidget à coluna direita (SEM GROUPBOX - usa o título interno do widget)
        if self._movement_widget is not None:
            right_column.addWidget(self._movement_widget)
            logger.info("✅ MovementControlWidget adicionado à aba 3 do Engineering Wizard (sem groupbox externa)")

        # Controles
        controls_group = QGroupBox("Controles de Captura")
        controls_layout = QVBoxLayout(controls_group)

        # Seletor de fiducial
        controls_layout.addWidget(QLabel("Fiducial:"))
        self.fiducial_selector = QGridLayout()
        self.btn_fid1 = QPushButton("Fiducial 1")
        self.btn_fid2 = QPushButton("Fiducial 2")
        self.btn_fid1.setCheckable(True)
        self.btn_fid2.setCheckable(True)
        self.btn_fid1.setChecked(True)
        self.btn_fid1.setStyleSheet(f"""
            QPushButton:checked {{
                background-color: {COLORS.SUCCESS};
                color: {COLORS.TEXT_PRIMARY};
                font-weight: bold;
            }}
        """)
        self.btn_fid2.setStyleSheet(f"""
            QPushButton:checked {{
                background-color: {COLORS.SUCCESS};
                color: {COLORS.TEXT_PRIMARY};
                font-weight: bold;
            }}
        """)
        self.fiducial_selector.addWidget(self.btn_fid1, 0, 0)
        self.fiducial_selector.addWidget(self.btn_fid2, 0, 1)
        controls_layout.addLayout(self.fiducial_selector)

        # Label de instruções
        instructions = QLabel(
            "<b>Instruções:</b><br>"
            "1. Selecione Fiducial 1 ou 2<br>"
            "2. Inicie o preview da câmera<br>"
            "3. Mova a máquina até o fiducial<br>"
            "4. Clique em 'Capturar Template'<br>"
            "5. Repita para o outro fiducial"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet(f"""
            QLabel {{
                padding: {SPACE.SM}px;
                background-color: {COLORS.SECONDARY_LIGHT};
                border-radius: {DIM.RADIUS_SM}px;
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        controls_layout.addWidget(instructions)

        controls_layout.addStretch()

        # Status dos fiduciais (labels lado a lado)
        status_layout = QHBoxLayout()
        self.lbl_fid1_status = QLabel("❌ Fiducial 1: Não capturado")
        self.lbl_fid2_status = QLabel("❌ Fiducial 2: Não capturado")
        status_layout.addWidget(self.lbl_fid1_status)
        status_layout.addWidget(self.lbl_fid2_status)
        controls_layout.addLayout(status_layout)

        # Adicionar Controles de Captura à coluna direita
        right_column.addWidget(controls_group)

        # Adicionar coluna direita ao layout principal
        main_layout.addLayout(right_column, 1)

        layout.addLayout(main_layout, 1)

        # Status geral
        self.status_label = QLabel("⚠️ Capture 2 fiduciais para continuar")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                padding: {SPACE.SM}px;
                background-color: {COLORS.WARNING_LIGHT};
                border: 1px solid {COLORS.BORDER};
                border-radius: {DIM.RADIUS_SM}px;
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        """Conecta signals."""
        self.btn_fid1.clicked.connect(lambda: self._select_fiducial(0))
        self.btn_fid2.clicked.connect(lambda: self._select_fiducial(1))
        # Conectar signal do CameraCaptureWidget para capturar template
        self.camera_capture.image_captured.connect(self._on_template_captured)

    def set_camera_controller(self, camera_controller, cfg=None, click_to_move_service=None, fov_converter=None):
        """
        Define controller de câmera (injeção de dependência).

        Args:
            camera_controller: CameraController
            cfg: AOIConfigManager (opcional)
            click_to_move_service: ClickToMoveService (opcional)
            fov_converter: CameraFOVConverter (opcional)
        """
        self._camera_controller = camera_controller

        # Injeta parâmetros no CameraCaptureWidget
        if camera_controller:
            self.camera_capture.controller = camera_controller
            if cfg:
                self.camera_capture.cfg = cfg
            if click_to_move_service:
                self.camera_capture.click_to_move_service = click_to_move_service
            if fov_converter:
                self.camera_capture.fov_converter = fov_converter

            logger.info("✅ CameraCaptureWidget configurado com controller, cfg e services")

    def _select_fiducial(self, fid_id: int):
        """Seleciona fiducial ativo."""
        self._current_fiducial_id = fid_id

        # Atualizar botões
        if fid_id == 0:
            self.btn_fid1.setChecked(True)
            self.btn_fid2.setChecked(False)
        else:
            self.btn_fid1.setChecked(False)
            self.btn_fid2.setChecked(True)

    def _on_template_captured(self, image: np.ndarray, metadata: dict):
        """
        Handler quando template é capturado via CameraCaptureWidget.

        Args:
            image: Imagem capturada (numpy array)
            metadata: Metadados da captura (x, y, z, window_size, etc)
        """
        try:
            # Criar fiducial
            fiducial = FiducialTemplate(
                id=self._current_fiducial_id,
                x=metadata.get('x', 0.0),
                y=metadata.get('y', 0.0),
                z=metadata.get('z', 0.0),
                image=image,
                window_size=metadata.get('window_size', self._window_size),
                captured_at=datetime.now().isoformat()
            )

            # Remover fiducial anterior do mesmo ID se existir
            self._fiducials = [f for f in self._fiducials if f.id != self._current_fiducial_id]
            self._fiducials.append(fiducial)

            # Emitir signal
            self.fiducial_captured.emit(fiducial.to_dict())

            # Atualizar UI
            self._update_status()

            logger.info(
                f"✅ Fiducial {self._current_fiducial_id + 1} capturado "
                f"em ({fiducial.x:.2f}, {fiducial.y:.2f}, {fiducial.z:.2f})"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao processar template capturado: {e}")
            QMessageBox.critical(
                self,
                "Erro de Captura",
                f"Não foi possível processar template:\n{e}"
            )

    def _update_status(self):
        """Atualiza display de status."""
        # Atualizar labels individuais
        fid1_captured = any(f.id == 0 for f in self._fiducials)
        fid2_captured = any(f.id == 1 for f in self._fiducials)

        if fid1_captured:
            self.lbl_fid1_status.setText("✅ Fiducial 1: Capturado")
            self.lbl_fid1_status.setStyleSheet(f"color: {COLORS.SUCCESS}; font-weight: bold;")
        else:
            self.lbl_fid1_status.setText("❌ Fiducial 1: Não capturado")
            self.lbl_fid1_status.setStyleSheet(f"color: {COLORS.ERROR};")

        if fid2_captured:
            self.lbl_fid2_status.setText("✅ Fiducial 2: Capturado")
            self.lbl_fid2_status.setStyleSheet(f"color: {COLORS.SUCCESS}; font-weight: bold;")
        else:
            self.lbl_fid2_status.setText("❌ Fiducial 2: Não capturado")
            self.lbl_fid2_status.setStyleSheet(f"color: {COLORS.ERROR};")

        # Validar
        is_valid = fid1_captured and fid2_captured
        was_valid = self._is_valid
        self._is_valid = is_valid

        if is_valid:
            self.status_label.setText(
                f"✅ 2 fiduciais capturados - Pronto para alinhamento"
            )
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    padding: {SPACE.SM}px;
                    background-color: {COLORS.SUCCESS};
                    border: 1px solid {COLORS.SUCCESS};
                    border-radius: {DIM.RADIUS_SM}px;
                    color: {COLORS.TEXT_PRIMARY};
                }}
            """)
        else:
            captured_count = len(self._fiducials)
            self.status_label.setText(
                f"⚠️ Capture {2 - captured_count} fiduciais para continuar"
            )
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    padding: {SPACE.SM}px;
                    background-color: {COLORS.WARNING_LIGHT};
                    border: 1px solid {COLORS.BORDER};
                    border-radius: {DIM.RADIUS_SM}px;
                    color: {COLORS.TEXT_PRIMARY};
                }}
            """)

        # Emitir signal se validação mudou
        if was_valid != is_valid:
            self.validation_changed.emit(is_valid)

    def get_fiducial_templates(self) -> List[Dict]:
        """
        Retorna templates capturados.

        Returns:
            Lista de dicts com dados dos fiduciais
        """
        return [f.to_dict() for f in self._fiducials]

    def is_valid(self) -> bool:
        """Verifica se 2 fiduciais foram capturados."""
        return self._is_valid

    def clear(self):
        """Limpa todas as capturas."""
        logger.info("🗑️ Limpando fiduciais")

        self._fiducials.clear()
        self._update_status()

    def _find_parent_cnc_control_tab(self, widget=None, visited=None):
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
            logger.debug(f"⚠️ Loop detectado em _find_parent_cnc_control_tab, widget já visitado")
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

    def _find_movement_widget_in_tab(self):
        """
        Busca o MovementControlWidget dentro da CNCControlTab.

        Returns:
            MovementControlWidget se encontrada, None caso contrário
        """
        # Primeiro, encontrar a CNCControlTab
        cnc_tab = self._find_parent_cnc_control_tab()

        if cnc_tab is not None:
            # Buscar por movement_widget dentro da aba
            if hasattr(cnc_tab, 'movement_widget') and cnc_tab.movement_widget is not None:
                return cnc_tab.movement_widget

        logger.debug("ℹ️ MovementControlWidget não encontrado na CNCControlTab")
        return None
