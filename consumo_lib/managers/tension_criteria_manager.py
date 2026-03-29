"""
Gerenciador de Configuração de Critérios de Tensão

Gerencia configurações globais de critérios de aceitação de tensão:
- Valores mínimo/máximo e warning low/high
- Persistência via AOIConfigManager
- Notificação de mudanças via signals

Author: Claude
Created: 2026-03-29
"""

import logging
from typing import Dict
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal

from aoi_lib.config_manager import AOIConfigManager

logger = logging.getLogger(__name__)


@dataclass
class TensionCriteriaConfig:
    """Configuração de critérios de tensão."""
    min_tension: float = 25.0
    max_tension: float = 45.0
    warning_low: float = 28.0
    warning_high: float = 42.0

    def to_dict(self) -> Dict:
        """Converte para dict."""
        return {
            "min_tension": self.min_tension,
            "max_tension": self.max_tension,
            "warning_low": self.warning_low,
            "warning_high": self.warning_high
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TensionCriteriaConfig":
        """Cria from dict."""
        return cls(
            min_tension=data.get("min_tension", 25.0),
            max_tension=data.get("max_tension", 45.0),
            warning_low=data.get("warning_low", 28.0),
            warning_high=data.get("warning_high", 42.0)
        )


class TensionCriteriaManager(QObject):
    """
    Gerencia configurações globais de critérios de tensão.

    Responsabilidades:
        - Ler configurações de tensão do arquivo de configuração
        - Atualizar configurações com persistência
        - Emitir signals quando critérios mudam
        - Permitir que componentes escutem mudanças

    Atributos:
        config_manager: Gerenciador de configuração AOI
        criteria_changed: Signal emitido quando critérios mudam

    Exemplo:
        >>> criteria_mgr = TensionCriteriaManager(config_mgr)
        >>> criteria_mgr.criteria_changed.connect(update_ui)
        >>> criteria = criteria_mgr.get_criteria()
    """

    criteria_changed = pyqtSignal(object)  # TensionCriteriaConfig

    def __init__(self, config_manager: AOIConfigManager):
        """
        Inicializa gerenciador de critérios de tensão.

        Args:
            config_manager: Gerenciador de configuração AOI
        """
        super().__init__()
        self.config_manager = config_manager
        self.log = logger

    def get_criteria(self) -> TensionCriteriaConfig:
        """
        Obtém critérios atuais do arquivo de configuração.

        Returns:
            TensionCriteriaConfig com valores atuais
        """
        try:
            data = self.config_manager.get("tension_criteria", default=None)
            if data is None:
                self.log.warning("Seção tension_criteria não encontrada, usando padrões")
                return TensionCriteriaConfig()

            return TensionCriteriaConfig.from_dict(data)

        except Exception as e:
            self.log.error(f"Erro ao ler critérios: {e}")
            return TensionCriteriaConfig()

    def update_criteria(self, criteria: TensionCriteriaConfig) -> bool:
        """
        Atualiza critérios no arquivo de configuração.

        Args:
            criteria: Nova configuração de critérios

        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        try:
            data = criteria.to_dict()

            # Atualiza cada campo individualmente
            self.config_manager.set("tension_criteria", "min_tension", value=data["min_tension"])
            self.config_manager.set("tension_criteria", "max_tension", value=data["max_tension"])
            self.config_manager.set("tension_criteria", "warning_low", value=data["warning_low"])
            self.config_manager.set("tension_criteria", "warning_high", value=data["warning_high"])

            self.log.info(f"Critérios atualizados: {data}")

            # Emite signal para notificar componentes
            self.criteria_changed.emit(criteria)

            return True

        except Exception as e:
            self.log.error(f"Erro ao salvar critérios: {e}")
            return False

    def set_criteria_values(
        self,
        min_tension: float,
        max_tension: float,
        warning_low: float,
        warning_high: float
    ) -> bool:
        """
        Atualiza critérios com valores individuais.

        Args:
            min_tension: Tensão mínima aceitável
            max_tension: Tensão máxima aceitável
            warning_low: Limite warning inferior
            warning_high: Limite warning superior

        Returns:
            True se atualizado com sucesso
        """
        criteria = TensionCriteriaConfig(
            min_tension=min_tension,
            max_tension=max_tension,
            warning_low=warning_low,
            warning_high=warning_high
        )
        return self.update_criteria(criteria)