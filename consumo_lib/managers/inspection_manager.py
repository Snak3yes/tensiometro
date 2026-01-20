"""
managers/inspection_manager.py
-------------------------------
Gerencia workflow de inspeção visual (StencilInspector).
"""
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
import numpy as np
from aoi_lib.stencil_inspector import StencilInspector, InspectionThresholds, InspectionResult

logger = logging.getLogger(__name__)


class InspectionManager(QObject):
    """
    Gerencia workflow de inspeção visual de stencils.

    Responsabilidades:
        - Gerenciar StencilInspector
        - Configurar thresholds de inspeção
        - Executar inspeção visual
        - Gerenciar resultados e overlays
        - Emitir signals de eventos
    """

    # Signals
    inspection_completed = pyqtSignal(object, object)  # InspectionResult, overlay (np.ndarray)
    inspection_failed = pyqtSignal(str)  # error_message
    thresholds_changed = pyqtSignal(object)  # InspectionThresholds

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.thresholds = InspectionThresholds()
        self.inspector = StencilInspector(self.thresholds)
        self._last_result: Optional[InspectionResult] = None
        self._last_overlay: Optional[np.ndarray] = None

        # Carregar thresholds salvos
        self._load_thresholds()

        logger.info("InspectionManager inicializado")

    def _load_thresholds(self):
        """Carrega thresholds de inspeção da configuração."""
        thresholds_data = self.config.get("inspection", "thresholds", default=None)

        if thresholds_data:
            try:
                self.thresholds = InspectionThresholds.from_dict(thresholds_data)
                self.inspector = StencilInspector(self.thresholds)
                logger.info("Thresholds de inspeção carregados")
            except Exception as e:
                logger.warning(f"Erro ao carregar thresholds de inspeção: {e}")
                self.thresholds = InspectionThresholds()
                self.inspector = StencilInspector(self.thresholds)
        else:
            self.thresholds = InspectionThresholds()
            self.inspector = StencilInspector(self.thresholds)

    def update_thresholds(self, thresholds: InspectionThresholds, save=True):
        """
        Atualiza thresholds de inspeção.

        Args:
            thresholds: Novos thresholds
            save: Se True, salva na configuração
        """
        self.thresholds = thresholds
        self.inspector = StencilInspector(thresholds)

        if save:
            self.config.set("inspection", "thresholds", value=thresholds.to_dict())
            self.config.save()

        self.thresholds_changed.emit(thresholds)
        logger.info("Thresholds de inspeção atualizados")

    def get_thresholds(self) -> InspectionThresholds:
        """Retorna os thresholds atuais."""
        return self.thresholds

    def load_gerber(self, gerber_path: str):
        """
        Carrega arquivo Gerber para inspeção.

        Args:
            gerber_path: Caminho do arquivo Gerber

        Returns:
            bool: True se carregou com sucesso
        """
        try:
            self.inspector.load_gerber(gerber_path)
            logger.info(f"Gerber carregado: {gerber_path}")
            return True
        except Exception as e:
            error_msg = f"Erro ao carregar Gerber: {e}"
            logger.error(error_msg)
            self.inspection_failed.emit(error_msg)
            return False

    def set_mosaic(self, mosaic_image: np.ndarray):
        """
        Define imagem de mosaico para inspeção.

        Args:
            mosaic_image: Imagem do mosaico (numpy array)
        """
        self.inspector.set_mosaic(mosaic_image)
        logger.info("Mosaico definido para inspeção")

    def set_alignment(self, transform):
        """
        Define transformação de alinhamento fiducial.

        Args:
            transform: Tupla (tx, ty, angle, scale)
        """
        self.inspector.set_alignment(transform)
        logger.info(f"Alinhamento definido: {transform}")

    def run_inspection(self):
        """
        Executa inspeção visual.

        Returns:
            tuple: (InspectionResult, overlay) ou (None, None) se falhar
        """
        try:
            result = self.inspector.inspect()
            overlay = self.inspector.get_result_overlay(show_all=True)

            # Salvar último resultado
            self._last_result = result
            self._last_overlay = overlay

            logger.info(f"Inspeção concluída: {result.summary}")
            self.inspection_completed.emit(result, overlay)

            return result, overlay
        except Exception as e:
            error_msg = f"Erro ao executar inspeção: {e}"
            logger.error(error_msg)
            self.inspection_failed.emit(error_msg)
            return None, None

    def get_last_result(self) -> Optional[InspectionResult]:
        """Retorna o último resultado de inspeção."""
        return self._last_result

    def get_last_overlay(self) -> Optional[np.ndarray]:
        """Retorna o último overlay de inspeção."""
        return self._last_overlay

    def has_last_result(self) -> bool:
        """Verifica se há resultado de inspeção disponível."""
        return self._last_result is not None

    def clear_last_result(self):
        """Limpa o último resultado de inspeção."""
        self._last_result = None
        self._last_overlay = None
        logger.debug("Último resultado de inspeção limpo")

    def get_inspector(self) -> StencilInspector:
        """Retorna o inspector subjacente (para uso avançado)."""
        return self.inspector
