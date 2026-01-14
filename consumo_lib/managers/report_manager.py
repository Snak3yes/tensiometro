"""
managers/report_manager.py
---------------------------
Gerencia geração de relatórios PDF (ReportGenerator).
"""
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from pathlib import Path
from aoi_lib.reports import ReportGenerator, ReportConfig

logger = logging.getLogger(__name__)


class ReportManagerWrapper(QObject):
    """
    Gerencia geração de relatórios PDF.

    Responsabilidades:
        - Gerenciar ReportGenerator
        - Configurar parâmetros de relatório
        - Gerar relatórios de tensão
        - Gerar relatórios de histórico de stencil
        - Gerar relatórios de inspeção visual
        - Emitir signals de eventos
    """

    # Signals
    report_generated = pyqtSignal(str, str)  # report_type, output_path
    report_failed = pyqtSignal(str, str)  # report_type, error_message
    config_changed = pyqtSignal(object)  # ReportConfig

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.report_config = ReportConfig()
        self.generator = ReportGenerator(self.report_config)

        # Carregar configuração salva
        self._load_config()

        logger.info(f"ReportManagerWrapper inicializado. Diretório: {self.report_config.output_dir}")

    def _load_config(self):
        """Carrega configuração de relatórios da configuração."""
        report_config_data = self.config.get("reports", "config", default=None)

        if report_config_data:
            try:
                self.report_config = ReportConfig.from_dict(report_config_data)
                self.generator = ReportGenerator(self.report_config)
                logger.info("Configuração de relatórios carregada")
            except Exception as e:
                logger.warning(f"Erro ao carregar config de relatórios: {e}")
                self.report_config = ReportConfig()
                self.generator = ReportGenerator(self.report_config)
        else:
            self.report_config = ReportConfig()
            self.generator = ReportGenerator(self.report_config)

    def update_config(self, config: ReportConfig, save=True):
        """
        Atualiza configuração de relatórios.

        Args:
            config: Nova configuração
            save: Se True, salva na configuração
        """
        self.report_config = config
        self.generator = ReportGenerator(config)

        if save:
            self.config.set("reports", "config", config.to_dict())
            self.config.save()

        self.config_changed.emit(config)
        logger.info("Configuração de relatórios atualizada")

    def get_config(self) -> ReportConfig:
        """Retorna a configuração atual."""
        return self.report_config

    def generate_tension_report(self, tension_data: dict, stencil_code: str = None,
                                operator: str = None) -> Optional[str]:
        """
        Gera relatório de tensão.

        Args:
            tension_data: Dados da medição de tensão
            stencil_code: Código do stencil (opcional)
            operator: Nome do operador (opcional)

        Returns:
            Caminho do PDF gerado ou None se falhar
        """
        try:
            output_path = self.generator.generate_tension_report(
                tension_data=tension_data,
                stencil_code=stencil_code,
                operator=operator
            )
            logger.info(f"Relatório de tensão gerado: {output_path}")
            self.report_generated.emit("tension", output_path)
            return output_path
        except Exception as e:
            error_msg = f"Erro ao gerar relatório de tensão: {e}"
            logger.error(error_msg)
            self.report_failed.emit("tension", error_msg)
            return None

    def generate_stencil_history_report(self, stencil_code: str,
                                       include_tension: bool = True,
                                       include_inspections: bool = True) -> Optional[str]:
        """
        Gera relatório de histórico de stencil.

        Args:
            stencil_code: Código do stencil
            include_tension: Incluir histórico de tensão
            include_inspections: Incluir histórico de inspeções

        Returns:
            Caminho do PDF gerado ou None se falhar
        """
        try:
            output_path = self.generator.generate_stencil_history_report(
                stencil_code=stencil_code,
                include_tension=include_tension,
                include_inspections=include_inspections
            )
            logger.info(f"Relatório de histórico gerado: {output_path}")
            self.report_generated.emit("stencil_history", output_path)
            return output_path
        except Exception as e:
            error_msg = f"Erro ao gerar relatório de histórico: {e}"
            logger.error(error_msg)
            self.report_failed.emit("stencil_history", error_msg)
            return None

    def generate_inspection_report(self, inspection_result, image_path: str,
                                  gerber_path: str = None) -> Optional[str]:
        """
        Gera relatório de inspeção visual.

        Args:
            inspection_result: Resultado da inspeção
            image_path: Caminho da imagem inspecionada
            gerber_path: Caminho do arquivo Gerber (opcional)

        Returns:
            Caminho do PDF gerado ou None se falhar
        """
        try:
            output_path = self.generator.generate_inspection_report(
                inspection_result=inspection_result,
                image_path=image_path,
                gerber_path=gerber_path
            )
            logger.info(f"Relatório de inspeção gerado: {output_path}")
            self.report_generated.emit("inspection", output_path)
            return output_path
        except Exception as e:
            error_msg = f"Erro ao gerar relatório de inspeção: {e}"
            logger.error(error_msg)
            self.report_failed.emit("inspection", error_msg)
            return None

    def get_generator(self) -> ReportGenerator:
        """Retorna o gerador subjacente (para uso avançado)."""
        return self.generator
