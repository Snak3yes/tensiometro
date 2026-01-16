"""
Tab Factory - Factory para criar abas da aplicação

Responsável por criar todas as abas da aplicação de forma desacoplada.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aoi_lib import CNCAOIController
    from aoi_lib.config_manager import AOIConfigManager
    from consumo_lib.tabs import (
        CNCControlTab,
        TensionTab,
        TrackingTab,
        InspectionTab,
        MapTab
    )

logger = logging.getLogger(__name__)


class TabFactory:
    """
    Factory para criar abas da aplicação.

    Responsabilidades:
    - Criar todas as abas (CNC, Tensão, Rastreabilidade, etc.)
    - Injetar dependências necessárias
    - Configurar cada aba adequadamente
    """

    def __init__(self,
                 controller: 'CNCAOIController',
                 config: 'AOIConfigManager',
                 stencil_tracker,
                 main_window):
        """
        Inicializa a factory com dependências necessárias.

        Args:
            controller: Controller principal CNC
            config: Gerenciador de configuração
            stencil_tracker: Tracker de stencils
            main_window: Janela principal (para parent widgets)
        """
        self.controller = controller
        self.config = config
        self.stencil_tracker = stencil_tracker
        self.main_window = main_window

        logger.debug("TabFactory inicializada")

    def create_cnc_control_tab(self) -> 'CNCControlTab':
        """
        Cria aba de controle CNC e câmera.

        Returns:
            Instância de CNCControlTab configurada
        """
        from consumo_lib.tabs import CNCControlTab

        tab = CNCControlTab(
            self.controller,
            self.config,
            parent=self.main_window
        )

        logger.debug("CNCControlTab criada")
        return tab

    def create_tension_tab(self) -> 'TensionTab':
        """
        Cria aba de visualização de tensão.

        Returns:
            Instância de TensionTab configurada
        """
        from consumo_lib.tabs import TensionTab

        tab = TensionTab(parent=self.main_window)

        logger.debug("TensionTab criada")
        return tab

    def create_tracking_tab(self) -> 'TrackingTab':
        """
        Cria aba de rastreabilidade.

        Returns:
            Instância de TrackingTab configurada
        """
        from consumo_lib.tabs import TrackingTab

        tab = TrackingTab(
            self.stencil_tracker,
            parent=self.main_window
        )

        logger.debug("TrackingTab criada")
        return tab

    def create_inspection_tab(self) -> 'InspectionTab':
        """
        Cria aba de inspeção visual.

        Returns:
            Instância de InspectionTab configurada
        """
        from consumo_lib.tabs import InspectionTab

        tab = InspectionTab(parent=self.main_window)

        logger.debug("InspectionTab criada")
        return tab

    def create_map_tab(self) -> 'MapTab':
        """
        Cria aba de programação de mapa.

        Returns:
            Instância de MapTab configurada
        """
        from consumo_lib.tabs import MapTab

        tab = MapTab(parent=self.main_window)

        logger.debug("MapTab criada")
        return tab

    def create_all_tabs(self, tab_widget):
        """
        Cria e adiciona todas as abas ao QTabWidget.

        Args:
            tab_widget: QTabWidget onde adicionar as abas

        Returns:
            Lista de abas criadas
        """
        tabs = []

        # Aba 1: Câmera & Movimento
        cnc_tab = self.create_cnc_control_tab()
        cnc_tab.image_captured.connect(
            self.main_window.on_image_captured
        )
        tab_widget.addTab(cnc_tab, "Câmera & Movimento")
        tabs.append(cnc_tab)

        # Expose widgets internos para compatibilidade
        self.main_window.cnc_control_tab = cnc_tab
        self.main_window.camera_preview = cnc_tab.camera_preview
        self.main_window.movement_widget = cnc_tab.movement_widget

        # Aba 2: Monitor CLP (criada diretamente, não via factory ainda)
        from consumo_lib.widgets.plc_monitor import PLCMonitorWidget
        plc_monitor = PLCMonitorWidget(self.controller)
        tab_widget.addTab(plc_monitor, "Monitor CLP")
        self.main_window.plc_monitor = plc_monitor
        tabs.append(plc_monitor)

        # Aba 3: Visualização de Tensão
        tension_tab = self.create_tension_tab()
        self.main_window.tension_visualization = tension_tab
        self.main_window.tension_viz_widget = tension_tab.visualization
        tab_widget.addTab(tension_tab, "Visualização de Tensão")
        tabs.append(tension_tab)

        # Aba 4: Rastreabilidade
        tracking_tab = self.create_tracking_tab()
        tracking_tab.tension_measurement_requested.connect(
            self.main_window._run_tension_measurement
        )
        tracking_tab.stencil_management_requested.connect(
            self.main_window.show_stencil_manager
        )
        tracking_tab.new_stencil_requested.connect(
            self.main_window.show_new_stencil_dialog
        )
        self.main_window.stencil_identification = tracking_tab.stencil_identification
        self.main_window.btn_run_tension = tracking_tab.btn_run_tension
        tab_widget.addTab(tracking_tab, "🏷️ Rastreabilidade")
        tabs.append(tracking_tab)

        # Aba 5: Inspeção Visual
        inspection_tab = self.create_inspection_tab()
        inspection_tab.settings_requested.connect(
            self.main_window.show_inspection_settings
        )
        tab_widget.addTab(inspection_tab, "🔍 Inspeção")
        tabs.append(inspection_tab)

        # Aba 6: Programação de Mapa
        map_tab = self.create_map_tab()
        map_tab.map_definition_requested.connect(
            lambda: self.main_window.map_controller.show_dialog(
                self.main_window,
                self.main_window.cnc_control_tab.camera_preview if hasattr(
                    self.main_window, 'cnc_control_tab'
                ) else None
            )
        )
        map_tab.mosaic_builder_requested.connect(
            self.main_window.show_mosaic_builder
        )
        tab_widget.addTab(map_tab, "🗺️ Mapa")
        tabs.append(map_tab)

        logger.info(f"{len(tabs)} abas criadas e adicionadas ao QTabWidget")
        return tabs
