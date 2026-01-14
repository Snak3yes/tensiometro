"""
report_generator.py
--------------------
Orchestrator principal para geração de relatórios PDF.

Este módulo fornece a interface principal para gerar relatórios,
delegando a implementação aos builders especializados.
"""

import logging
from typing import Dict, List, Optional, Any

from .config import ReportConfig
from .builders import (
    TensionReportBuilder,
    StencilHistoryReportBuilder,
    InspectionReportBuilder
)

log = logging.getLogger(__name__)


class ReportGenerator:
    """
    Classe principal para geração de relatórios.

    Uso:
        config = ReportConfig(company_name="MinhaEmpresa")
        generator = ReportGenerator(config)

        # Relatório de tensão
        path = generator.generate_tension_report(tension_data, stencil_code="STN-001")

        # Relatório de histórico
        path = generator.generate_stencil_history_report(stencil, history)

        # Relatório de inspeção
        path = generator.generate_inspection_report(inspection_result)
    """

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()

    def generate_tension_report(
        self,
        tension_data: Dict[str, Any],
        stencil_code: Optional[str] = None,
        stencil_description: Optional[str] = None,
        recipe_name: Optional[str] = None,
        operator: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Gera relatório de medição de tensão.

        Returns:
            Caminho do arquivo PDF gerado
        """
        builder = TensionReportBuilder(self.config)
        return builder.build(
            tension_data=tension_data,
            stencil_code=stencil_code,
            stencil_description=stencil_description,
            recipe_name=recipe_name,
            operator=operator,
            output_path=output_path
        )

    def generate_stencil_history_report(
        self,
        stencil: Dict[str, Any],
        history: List[Dict[str, Any]],
        output_path: Optional[str] = None
    ) -> str:
        """
        Gera relatório de histórico do stencil.

        Returns:
            Caminho do arquivo PDF gerado
        """
        builder = StencilHistoryReportBuilder(self.config)
        return builder.build(
            stencil=stencil,
            history=history,
            output_path=output_path
        )

    def generate_inspection_report(
        self,
        inspection_result: Dict[str, Any],
        overlay_image_path: Optional[str] = None,
        stencil_code: Optional[str] = None,
        operator: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Gera relatório de inspeção visual.

        Args:
            inspection_result: Resultado da inspeção (dict ou InspectionResult)
            overlay_image_path: Caminho da imagem de overlay (PNG)
            stencil_code: Código do stencil
            operator: Nome do operador
            output_path: Caminho de saída (opcional)

        Returns:
            Caminho do arquivo PDF gerado
        """
        builder = InspectionReportBuilder(self.config)
        return builder.build(
            inspection_result=inspection_result,
            overlay_image_path=overlay_image_path,
            stencil_code=stencil_code,
            operator=operator,
            output_path=output_path
        )

    def update_config(self, **kwargs):
        """Atualiza configuração."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)


# Re-exportar classes antigas para compatibilidade
from .config import ReportConfig, get_custom_styles

# Manter compatibilidade com imports antigos
TensionReportBuilder = TensionReportBuilder
StencilHistoryReportBuilder = StencilHistoryReportBuilder
InspectionReportBuilder = InspectionReportBuilder
