# -*- coding: utf-8 -*-
"""
controllers_factory.py
-----------------------
Factory para criar todos os controllers da aplicação.

Responsabilidade: Criar controllers ativos da aplicação.

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (SOLID Refactoring Phase 2)
"""

import logging
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aoi_lib.config_manager import AOIConfigManager
    from aoi_lib import CNCAOIController
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class ControllersFactory:
    """
    Factory para criar todos os controllers da aplicação.

    Responsabilidade:
    - Criar controllers independentes de UI ativos (Map, CameraSettings, Calibration, etc.)
    - Criar controllers dependentes de UI (FileIO, PositionManager)
    - Tratamento robusto de erros (continua mesmo se um controller falhar)

    Methods:
    - create_controllers_independent_of_ui(): Cria controllers que não dependem de UI
    - create_controllers_dependent_on_ui(): Cria controllers que dependem de UI
    - create_all_controllers(): Cria todos os controllers
    """

    def create_controllers_independent_of_ui(
        self,
        window: 'QWidget',
        config: 'AOIConfigManager',
        controller: 'CNCAOIController',
        managers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cria controllers que não dependem de widgets da UI.

        Args:
            window: Instância da janela principal
            config: Instância de AOIConfigManager
            controller: Instância de CNCAOIController
            managers: Dict com todos os managers

        Returns:
            Dict com controllers independentes de UI
        """
        from consumo_lib.controllers import (
            MapController,
            CameraSettingsController,
            CalibrationController,
            ReportDialogController,
            SequenceController,
            TensionMeasurementController,
            DialogManagerController,
        )

        controllers = {}

        # 1. Map Controller
        try:
            controllers['map_controller'] = MapController(
                controller,
                config,
                window
            )
            controllers['map_controller'].setup_ui_handlers()
            logger.debug("MapController criado via ControllersFactory")
        except Exception as e:
            logger.error(f"Erro ao criar MapController via ControllersFactory: {e}")
            controllers['map_controller'] = None

        # 2. Camera Settings Controller
        try:
            controllers['camera_settings_controller'] = CameraSettingsController(
                controller,
                config,
                window
            )
            controllers['camera_settings_controller'].setup_ui_handlers()
            logger.debug("CameraSettingsController criado via ControllersFactory")
        except Exception as e:
            logger.error(f"Erro ao criar CameraSettingsController via ControllersFactory: {e}")
            controllers['camera_settings_controller'] = None

        # 3. Calibration Controller
        try:
            controllers['calibration_controller'] = CalibrationController(
                controller,
                config,
                window
            )
            controllers['calibration_controller'].setup_ui_handlers()
            logger.debug("CalibrationController criado via ControllersFactory")
        except Exception as e:
            logger.error(f"Erro ao criar CalibrationController via ControllersFactory: {e}")
            controllers['calibration_controller'] = None

        # 4. Report Dialog Controller
        try:
            controllers['report_dialog_controller'] = ReportDialogController(
                managers['report_manager_wrapper'],
                managers['stencil_manager_wrapper'],
                managers['stencil_tracker'],
                window
            )
            controllers['report_dialog_controller'].setup_ui_handlers()
            logger.debug("ReportDialogController criado via ControllersFactory")
        except Exception as e:
            logger.error(f"Erro ao criar ReportDialogController via ControllersFactory: {e}")
            controllers['report_dialog_controller'] = None

        # 5. Sequence Controller
        try:
            controllers['sequence_controller'] = SequenceController(
                controller,
                window
            )
            logger.debug("SequenceController criado via ControllersFactory")
        except Exception as e:
            logger.error(f"Erro ao criar SequenceController via ControllersFactory: {e}")
            controllers['sequence_controller'] = None

        # 6. ConnectionManagerController será criado após setupUI()
        controllers['connection_manager_controller'] = None

        # 7. Tension Measurement Controller
        try:
            controllers['tension_measurement_controller'] = TensionMeasurementController(
                controller,
                config,
                managers['stencil_manager_wrapper'],
                window
            )
            controllers['tension_measurement_controller'].setup_ui_handlers()
            logger.debug("TensionMeasurementController criado via ControllersFactory")
        except Exception as e:
            logger.error(f"Erro ao criar TensionMeasurementController via ControllersFactory: {e}")
            controllers['tension_measurement_controller'] = None

        # 8. Dialog Manager Controller
        try:
            controllers['dialog_manager_controller'] = DialogManagerController(
                managers['stencil_manager_wrapper'],
                managers['report_manager_wrapper'],
                managers['report_config'],
                controller,
                window
            )
            logger.debug("DialogManagerController criado via ControllersFactory")
        except Exception as e:
            logger.error(f"Erro ao criar DialogManagerController via ControllersFactory: {e}")
            controllers['dialog_manager_controller'] = None

        logger.info("Controllers independentes de UI criados via ControllersFactory")

        return controllers

    def create_controllers_dependent_on_ui(
        self,
        window: 'QWidget',
        controller: 'CNCAOIController'
    ) -> Dict[str, Any]:
        """
        Cria controllers que dependem de widgets da UI.

        Args:
            window: Instância da janela principal (UI já deve estar criada)
            controller: Instância de CNCAOIController

        Returns:
            Dict com controllers dependentes de UI
        """
        from consumo_lib.controllers import FileIOController, PositionManagerController

        controllers = {}

        # Configura widgets da UI no ConnectionManager para leitura de valores PLC
        # (correção de bug de configurações não aplicadas)
        if hasattr(window, 'connection_mgr') and hasattr(window, 'plc_host_input') and hasattr(window, 'plc_port_input'):
            from consumo_lib.managers import ConnectionManager
            connection_mgr: ConnectionManager = window.connection_mgr
            connection_mgr.set_ui_widgets(
                plc_host_input=window.plc_host_input,
                plc_port_input=window.plc_port_input
            )
            logger.debug("Widgets PLC configurados no ConnectionManager via ControllersFactory")

        # 1. File IO Controller (requer position_list_widget e sequence_widget)
        if hasattr(window, 'position_list_widget') and hasattr(window, 'sequence_widget'):
            try:
                controllers['file_io_controller'] = FileIOController(
                    controller,
                    window.position_list_widget,
                    window.sequence_widget,
                    window
                )
                logger.debug("FileIOController criado via ControllersFactory")
            except Exception as e:
                logger.error(f"Erro ao criar FileIOController via ControllersFactory: {e}")
                controllers['file_io_controller'] = None
        else:
            logger.info("FileIOController não criado - position_list_widget não disponível (release/v0.5-tension)")
            controllers['file_io_controller'] = None

        # 2. Position Manager Controller (requer position_list_widget)
        if hasattr(window, 'position_list_widget'):
            try:
                controllers['position_manager_controller'] = PositionManagerController(
                    controller,
                    window.position_list_widget,
                    window
                )
                controllers['position_manager_controller'].setup_ui_handlers()
                logger.debug("PositionManagerController criado via ControllersFactory")
            except Exception as e:
                logger.error(f"Erro ao criar PositionManagerController via ControllersFactory: {e}")
                controllers['position_manager_controller'] = None
        else:
            logger.info("PositionManagerController não criado - position_list_widget não disponível (release/v0.5-tension)")
            controllers['position_manager_controller'] = None

        logger.info("Controllers dependentes de UI criados via ControllersFactory")

        return controllers

    def create_all_controllers(
        self,
        window: 'QWidget',
        config: 'AOIConfigManager',
        controller: 'CNCAOIController',
        managers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cria todos os controllers (independentes e dependentes de UI).

        Args:
            window: Instância da janela principal
            config: Instância de AOIConfigManager
            controller: Instância de CNCAOIController
            managers: Dict com todos os managers

        Returns:
            Dict unificado com todos os controllers
        """
        controllers = {}

        # Controllers independentes de UI
        independent_controllers = self.create_controllers_independent_of_ui(
            window, config, controller, managers
        )
        controllers.update(independent_controllers)

        # Controllers dependentes de UI (requerem UI já criada)
        # Nota: Estes devem ser criados APÓS setup_ui() em SetupCoordinator
        # Por enquanto retornamos dict vazio, será chamado separadamente
        # dependent_controllers = self.create_controllers_dependent_on_ui(window, controller)
        # controllers.update(dependent_controllers)

        return controllers
