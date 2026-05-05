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
        RecipeManagementTab,
        TensionTab,
        TensionMeasurementTab,
        TrackingTab,
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

    def create_tension_measurement_tab(self) -> 'TensionMeasurementTab':
        """
        Cria aba unificada de Medição de Tensão.

        Returns:
            Instância de TensionMeasurementTab configurada
        """
        from consumo_lib.tabs import TensionMeasurementTab

        tab = TensionMeasurementTab(
            stencil_manager=self.stencil_tracker,
            config_manager=self.config,
            parent=self.main_window
        )

        logger.debug("TensionMeasurementTab criada")
        return tab

    def create_recipe_management_tab(self) -> 'RecipeManagementTab':
        """
        Cria aba de gerenciamento de receitas.

        Returns:
            Instância de RecipeManagementTab configurada
        """
        from consumo_lib.tabs import RecipeManagementTab

        tab = RecipeManagementTab(
            recipe_manager=self.main_window.recipe_manager,
            recipe_controller=self.main_window.recipe_manager_controller,
            parent=self.main_window
        )

        logger.debug("RecipeManagementTab criada")
        return tab

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

    def create_all_tabs(self, tab_widget):
        """
        Cria e adiciona todas as abas ao QTabWidget.

        Args:
            tab_widget: QTabWidget onde adicionar as abas

        Returns:
            Lista de abas criadas
        """
        tabs = []

        # REMOVIDO (release/v0.5-tension): Aba "Câmera & Movimento"
        # O controle de movimento agora está em um diálogo acessível via menu
        # Ferramentas → Controle de Movimento (Ctrl+M)
        #
        # NOTA: Criamos movement_widget oculto para compatibilidade com keyboard handler
        from consumo_lib.widgets.movement_control import MovementControlWidget
        self.main_window.movement_widget = MovementControlWidget(
            self.controller,
            self.config,
            parent=self.main_window
        )
        self.main_window.movement_widget.hide()  # Oculto - acessível via diálogo

        # REMOVIDO (2026-03-29): Abas "Stencils" e "Visualização de Tensão"
        # Substituídas pela aba unificada "Medição de Tensão"
        # As classes TreeViewTab e TensionTab são mantidas por compatibilidade

        # REMOVIDO (2026-03-29): Aba "Rastreabilidade"
        # Substituída por diálogo acessível via menu Ferramentas → Rastreabilidade (Ctrl+R)
        # stencil_identification agora é definido em MainWindow.open_tracking_dialog()

        # Aba 1: Medição de Tensão (Unificada)
        tension_measurement_tab = self.create_tension_measurement_tab()
        self.main_window.tension_measurement_tab = tension_measurement_tab
        tab_widget.addTab(tension_measurement_tab, "Medição de Tensão")
        tabs.append(tension_measurement_tab)

        recipe_management_tab = self.create_recipe_management_tab()
        self.main_window.recipe_management_tab = recipe_management_tab
        tab_widget.addTab(recipe_management_tab, "Receitas")
        tabs.append(recipe_management_tab)

        logger.info(f"{len(tabs)} aba criada e adicionada ao QTabWidget")
        return tabs
