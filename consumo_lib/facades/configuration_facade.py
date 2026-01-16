# -*- coding: utf-8 -*-
"""
configuration_facade.py
-----------------------
Facade para abstrair acesso a configurações da aplicação.

Responsabilidade: Simplificar acesso a configurações do AOIConfigManager,
centralizando gets e fornecendo métodos semânticos.

Autor: Sistema AOI Tensiometro
Data: 2026-01-16 (SOLID Refactoring Phase 2)
"""

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from aoi_lib.config_manager import AOIConfigManager

logger = logging.getLogger(__name__)


class ConfigurationFacade:
    """
    Facade para abstrair acesso a configurações.

    Responsabilidade:
    - Centralizar acesso a configurações do AOIConfigManager
    - Fornecer métodos semânticos para acessar configs
    - Simplificar testes (mock de configs)

    Methods:
    - get_plc_config(): Retorna configurações de PLC
    - get_camera_config(): Retorna configurações de câmera
    - get_inspection_thresholds(): Retorna thresholds de inspeção
    - get(): Método genérico para acessar qualquer configuração
    """

    def __init__(self, config: 'AOIConfigManager'):
        """
        Inicializa a facade.

        Args:
            config: Instância de AOIConfigManager
        """
        self.config = config
        logger.debug("ConfigurationFacade inicializada")

    def get_plc_host(self) -> str:
        """
        Retorna host PLC configurado.

        Returns:
            Host PLC (ex: "192.168.1.5")
        """
        return self.config.get("connections", "plc_host", default="192.168.1.5")

    def get_plc_port(self) -> int:
        """
        Retorna porta PLC configurada.

        Returns:
            Porta PLC (ex: 502)
        """
        return self.config.get("connections", "plc_port", default=502)

    def get_plc_config(self) -> dict:
        """
        Retorna todas as configurações de PLC.

        Returns:
            Dict com host e port
        """
        return {
            'host': self.get_plc_host(),
            'port': self.get_plc_port(),
        }

    def get_camera_mirror_x(self) -> bool:
        """
        Retorna se espelhamento horizontal da câmera está ativo.

        Returns:
            True se mirror_x está ativo
        """
        return self.config.get("camera", "mirror_x", default=False)

    def get_camera_mirror_y(self) -> bool:
        """
        Retorna se espelhamento vertical da câmera está ativo.

        Returns:
            True se mirror_y está ativo
        """
        return self.config.get("camera", "mirror_y", default=False)

    def get_camera_config(self) -> dict:
        """
        Retorna todas as configurações de câmera.

        Returns:
            Dict com mirror_x e mirror_y
        """
        return {
            'mirror_x': self.get_camera_mirror_x(),
            'mirror_y': self.get_camera_mirror_y(),
        }

    def get_inspection_thresholds(self) -> dict:
        """
        Retorna thresholds padrão de inspeção.

        Returns:
            Dict com thresholds (ok, partial, blocked)
        """
        # Nota: Estes valores geralmente vêm do InspectionManager
        # A facade centraliza o acesso, mas os valores são gerenciados por InspectionManager
        return self.config.get("inspection", "thresholds", default={
            'ok_threshold': 90,
            'partial_threshold': 70,
        })

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Método genérico para acessar qualquer configuração.

        Args:
            section: Seção da configuração
            key: Chave da configuração
            default: Valor padrão se não existir

        Returns:
            Valor da configuração
        """
        return self.config.get(section, key, default=default)
