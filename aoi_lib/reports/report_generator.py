"""
Report Generator (Refatorado)

Facade principal para geração de relatórios PDF.

Responsável por:
- Criar e compartilhar serviços especializados entre builders
- Delegar geração de relatórios aos builders apropriados
- Manter compatibilidade com interface original
"""

import logging
from typing import Dict, List, Optional, Any

# Import config from parent module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from report_generator import ReportConfig

# Import specialized services
from .pdf_generator import PDFGenerator
from .chart_generator import ChartGenerator
from .statistics_calculator import StatisticsCalculator
from .report_layout_manager import ReportLayoutManager

# Import refactored builders
from .builders import (
    TensionReportBuilder,
    StencilHistoryReportBuilder,
)

log = logging.getLogger(__name__)


class ReportGenerator:
    """
    Refatorado: Facade principal para geração de relatórios.

    Otimizações:
    - Serviços compartilhados entre todos os builders (criados uma vez)
    - Dependency injection dos serviços para cada builder
    - Redução de uso de memória (não cria múltiplas instâncias dos mesmos serviços)

    Uso:
        config = ReportConfig(company_name="MinhaEmpresa")
        generator = ReportGenerator(config)

        # Relatório de tensão
        path = generator.generate_tension_report(tension_data, stencil_code="STN-001")

        # Relatório de histórico
        path = generator.generate_stencil_history_report(stencil, history)

    """

    def __init__(self, config: Optional[ReportConfig] = None):
        """
        Initialize report generator with shared services.

        Args:
            config: Report configuration (optional, uses default if None)
        """
        self.config = config or ReportConfig()

        # Criar serviços compartilhados (injetados em todos os builders)
        # Isso evita que cada builder crie suas próprias instâncias
        self.pdf = PDFGenerator(self.config)
        self.chart = ChartGenerator(self.config)
        self.stats = StatisticsCalculator()
        self.layout = ReportLayoutManager(self.config)

        log.debug("ReportGenerator inicializado com serviços compartilhados")

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

        Usa TensionReportBuilder com todos os 4 serviços compartilhados.

        Returns:
            Caminho do arquivo PDF gerado
        """
        builder = TensionReportBuilder(
            self.config,
            pdf_generator=self.pdf,
            chart_generator=self.chart,
            stats_calculator=self.stats,
            layout_manager=self.layout
        )
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

        Usa StencilHistoryReportBuilder com todos os 4 serviços compartilhados.

        Returns:
            Caminho do arquivo PDF gerado
        """
        builder = StencilHistoryReportBuilder(
            self.config,
            pdf_generator=self.pdf,
            chart_generator=self.chart,
            stats_calculator=self.stats,
            layout_manager=self.layout
        )
        return builder.build(
            stencil=stencil,
            history=history,
            output_path=output_path
        )

    def update_config(self, **kwargs):
        """
        Atualiza configuração.

        NOTA: Atualizar a configuração após criação dos serviços
        requer recriar os serviços para que as mudanças tenham efeito.
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        # Recriar serviços afetados pela configuração
        self.pdf = PDFGenerator(self.config)
        self.chart = ChartGenerator(self.config)
        self.layout = ReportLayoutManager(self.config)
        # StatisticsCalculator não depende de config, não precisa recriar

        log.debug("Configuração atualizada e serviços recriados")


# ============================================================================
#  COMPATIBILIDADE COM IMPORTS ANTIGOS
# ============================================================================

# Para compatibilidade, permitir imports do módulo antigo
__all__ = [
    "ReportGenerator",
    "ReportConfig",
]
