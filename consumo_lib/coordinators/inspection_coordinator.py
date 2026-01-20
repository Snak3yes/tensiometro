"""
coordinators/inspection_coordinator.py
--------------------------------------

Orquestra o fluxo completo de inspeção visual de stencil:
1. Carregar arquivo Gerber
2. Capturar fiduciais
3. Alinhar sistema de coordenadas
4. Capturar imagem de inspeção
5. Analisar aberturas
6. Gerar relatório

Centraliza lógica espalhada pelo código e implementa
o padrão Coordinator para gerenciar interações complexas.
"""

import logging
from typing import Optional, Tuple
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class InspectionStep(Enum):
    """Etapas do fluxo de inspeção"""
    IDLE = "idle"
    LOADING_GERBER = "loading_gerber"
    CAPTURING_FIDUCIALS = "capturing_fiducials"
    ALIGNING = "aligning"
    CAPTURING_IMAGE = "capturing_image"
    ANALYZING = "analyzing"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class InspectionConfig:
    """Configuração de uma inspeção"""
    gerber_file: str
    fiducial_templates: list = None
    threshold_ok: float = 80.0
    threshold_partial: float = 50.0
    backlight_enabled: bool = True

    def __post_init__(self):
        if self.fiducial_templates is None:
            self.fiducial_templates = []


@dataclass
class InspectionResult:
    """Resultado de uma inspeção"""
    success: bool
    step: InspectionStep
    data: dict = None
    error: str = None
    image_path: str = None
    overlay_path: str = None
    summary: str = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}


class InspectionCoordinator(QObject):
    """
    Coordena o fluxo completo de inspeção visual.

    Responsabilidades:
        - Orquestrar interação entre Gerber, FiducialAlignment, Inspection
        - Gerenciar estado da inspeção (step-by-step)
        - Emitir signals para notificar progresso
        - Centralizar lógica de inspeção

    Substitui lógica espalhada entre main_window, tabs, e managers.
    """

    # Signals de progresso
    step_changed = pyqtSignal(InspectionStep, str)  # step, message
    progress_updated = pyqtSignal(int, str)  # percent, message
    gerber_loaded = pyqtSignal(object)  # gerber_data
    fiducials_captured = pyqtSignal(list)  # templates
    alignment_completed = pyqtSignal(object)  # transformation matrix
    image_captured = pyqtSignal(str)  # image_path
    analysis_completed = pyqtSignal(object, object)  # result, overlay
    report_generated = pyqtSignal(str)  # report_path

    # Signals finais
    inspection_completed = pyqtSignal(object)  # InspectionResult
    inspection_failed = pyqtSignal(str)  # error_message

    def __init__(self, controller, config_manager, inspection_manager):
        """
        Inicializa o coordinator.

        Args:
            controller: CNCAOIController
            config_manager: AOIConfigManager
            inspection_manager: InspectionManager existente
        """
        super().__init__()
        self.controller = controller
        self.config = config_manager
        self.inspection_manager = inspection_manager

        # Estado atual
        self._current_step = InspectionStep.IDLE
        self._current_config: Optional[InspectionConfig] = None
        self._gerber_data = None
        self._fiducial_templates = []
        self._transformation_matrix = None
        self._last_image = None
        self._last_result = None

    # ==================== PROPRIEDADES ====================

    @property
    def current_step(self) -> InspectionStep:
        """Retorna a etapa atual da inspeção."""
        return self._current_step

    @property
    def is_inspecting(self) -> bool:
        """Retorna True se uma inspeção está em andamento."""
        return self._current_step != InspectionStep.IDLE

    @property
    def has_gerber(self) -> bool:
        """Retorna True se um arquivo Gerber está carregado."""
        return self._gerber_data is not None

    @property
    def has_fiducials(self) -> bool:
        """Retorna True se fiduciais foram capturados."""
        return len(self._fiducial_templates) > 0

    @property
    def is_aligned(self) -> bool:
        """Retorna True se o alinhamento foi completado."""
        return self._transformation_matrix is not None

    # ==================== MÉTODOS PÚBLICOS ====================

    def start_inspection(self, config: InspectionConfig):
        """
        Inicia uma nova inspeção.

        Args:
            config: Configuração da inspeção
        """
        if self.is_inspecting:
            logger.warning("Inspeção já em andamento")
            return

        self._current_config = config
        self._set_step(InspectionStep.LOADING_GERBER, "Carregando arquivo Gerber...")

        try:
            # Carregar arquivo Gerber
            self._load_gerber(config.gerber_file)

            # Emitir signal de progresso
            self.step_changed.emit(InspectionStep.LOADING_GERBER, "Gerber carregado com sucesso")
            self.progress_updated.emit(20, "Gerber carregado")

            logger.info(f"Inspeção iniciada: {config.gerber_file}")

        except Exception as e:
            error_msg = f"Erro ao carregar Gerber: {e}"
            logger.error(error_msg)
            self._set_error(error_msg)

    def capture_fiducials(self, templates: list):
        """
        Registra templates de fiduciais capturados.

        Args:
            templates: Lista de templates capturados
        """
        if self._current_step != InspectionStep.LOADING_GERBER:
            logger.warning(f"Captura de fiduciais não permitida na etapa {self._current_step}")
            return

        self._fiducial_templates = templates
        self._set_step(InspectionStep.CAPTURING_FIDUCIALS, "Fiduciais capturados")
        self.progress_updated.emit(40, "Fiduciais capturados")

        # Emitir signal
        self.fiducials_captured.emit(templates)

        logger.info(f"Fiduciais capturados: {len(templates)} templates")

    def perform_alignment(self):
        """Executa o alinhamento usando os fiduciais capturados."""
        if not self.has_fiducials:
            error_msg = "Capture fiduciais primeiro"
            logger.error(error_msg)
            self._set_error(error_msg)
            return

        self._set_step(InspectionStep.ALIGNING, "Alinhando sistema de coordenadas...")

        try:
            # Importar aqui para evitar circular import
            from aoi_lib.fiducial_alignment import FiducialAlignment

            # Criar aligner
            aligner = FiducialAlignment()

            # Adicionar templates
            for template in self._fiducial_templates:
                aligner.add_template(template)

            # Executar alinhamento
            transformation = aligner.compute_transformation()

            if transformation is None:
                raise ValueError("Falha ao computar matriz de transformação")

            self._transformation_matrix = transformation

            self._set_step(InspectionStep.CAPTURING_IMAGE, "Alinhamento completado")
            self.progress_updated.emit(60, "Sistema alinhado")

            # Emitir signal
            self.alignment_completed.emit(transformation)

            logger.info("Alinhamento completado com sucesso")

        except Exception as e:
            error_msg = f"Erro no alinhamento: {e}"
            logger.error(error_msg)
            self._set_error(error_msg)

    def capture_inspection_image(self):
        """Captura a imagem de inspeção com backlight."""
        if not self.is_aligned:
            error_msg = "Alinhe o sistema primeiro"
            logger.error(error_msg)
            self._set_error(error_msg)
            return

        self._set_step(InspectionStep.CAPTURING_IMAGE, "Capturando imagem de inspeção...")

        try:
            # Ativar backlight
            if hasattr(self.controller.cnc, 'set_backlight'):
                self.controller.cnc.set_backlight(True)

            # Capturar imagem
            image = self.controller.camera.capture()

            if image is None:
                raise ValueError("Falha ao capturar imagem")

            # Salvar imagem temporária
            temp_path = self._save_temp_image(image)
            self._last_image = temp_path

            self._set_step(InspectionStep.ANALYZING, "Imagem capturada")
            self.progress_updated.emit(80, "Imagem capturada")

            # Emitir signal
            self.image_captured.emit(temp_path)

            logger.info(f"Imagem capturada: {temp_path}")

            # Iniciar análise automaticamente
            self.analyze_image(image)

        except Exception as e:
            error_msg = f"Erro ao capturar imagem: {e}"
            logger.error(error_msg)
            self._set_error(error_msg)
        finally:
            # Desligar backlight
            if hasattr(self.controller.cnc, 'set_backlight'):
                self.controller.cnc.set_backlight(False)

    def analyze_image(self, image):
        """
        Analisa a imagem capturada.

        Args:
            image: Imagem capturada (numpy array)
        """
        if self._current_step != InspectionStep.ANALYZING:
            logger.warning(f"Análise não permitida na etapa {self._current_step}")
            return

        try:
            # Usar InspectionManager existente
            # Nota: Isso pode precisar ser adaptado dependendo da estrutura do InspectionManager
            from aoi_lib.stencil_inspector import StencilInspector

            inspector = StencilInspector()

            # Analisar imagem
            result = inspector.inspect(
                image=image,
                gerber_data=self._gerber_data,
                transformation=self._transformation_matrix,
                threshold_ok=self._current_config.threshold_ok,
                threshold_partial=self._current_config.threshold_partial
            )

            self._last_result = result

            self._set_step(InspectionStep.COMPLETED, "Inspeção completada")
            self.progress_updated.emit(100, "Inspeção concluída")

            # Emitir signals
            self.analysis_completed.emit(result, None)
            self.inspection_completed.emit(
                InspectionResult(
                    success=True,
                    step=InspectionStep.COMPLETED,
                    data=result.to_dict() if hasattr(result, 'to_dict') else result,
                    summary=result.summary if hasattr(result, 'summary') else "Inspeção concluída"
                )
            )

            logger.info("Análise completada com sucesso")

        except Exception as e:
            error_msg = f"Erro na análise: {e}"
            logger.error(error_msg)
            self._set_error(error_msg)

    def generate_report(self, output_path: str = None):
        """
        Gera relatório PDF da inspeção.

        Args:
            output_path: Caminho do arquivo PDF (opcional)
        """
        if self._last_result is None:
            error_msg = "Nenhum resultado para gerar relatório"
            logger.error(error_msg)
            self._set_error(error_msg)
            return

        self._set_step(InspectionStep.GENERATING_REPORT, "Gerando relatório...")

        try:
            # Usar ReportGenerator existente
            from aoi_lib.reports import ReportGenerator

            generator = ReportGenerator()

            # Gerar relatório
            if output_path is None:
                output_path = self._generate_report_path()

            generator.generate(
                result=self._last_result,
                image_path=self._last_image,
                output_path=output_path
            )

            self._set_step(InspectionStep.COMPLETED, "Relatório gerado")

            # Emitir signal
            self.report_generated.emit(output_path)

            logger.info(f"Relatório gerado: {output_path}")

        except Exception as e:
            error_msg = f"Erro ao gerar relatório: {e}"
            logger.error(error_msg)
            self._set_error(error_msg)

    def reset(self):
        """Reseta o estado da inspeção."""
        self._current_step = InspectionStep.IDLE
        self._current_config = None
        self._gerber_data = None
        self._fiducial_templates = []
        self._transformation_matrix = None
        self._last_image = None
        self._last_result = None

        logger.info("InspectionCoordinator resetado")

    # ==================== MÉTODOS PRIVADOS ====================

    def _load_gerber(self, gerber_file: str):
        """Carrega arquivo Gerber."""
        from aoi_lib.gerber_parser import GerberParser

        parser = GerberParser()
        self._gerber_data = parser.parse(gerber_file)

        # Emitir signal
        self.gerber_loaded.emit(self._gerber_data)

    def _save_temp_image(self, image) -> str:
        """Salva imagem capturada em arquivo temporário."""
        import cv2
        import uuid

        # Criar diretório temp se não existir
        temp_dir = Path("temp/inspections")
        temp_dir.mkdir(parents=True, exist_ok=True)

        # Gerar nome único
        filename = f"inspection_{uuid.uuid4().hex[:8]}.png"
        filepath = temp_dir / filename

        # Salvar
        cv2.imwrite(str(filepath), image)

        return str(filepath)

    def _generate_report_path(self) -> str:
        """Gera caminho para relatório."""
        from datetime import datetime

        reports_dir = Path("reports/inspections")
        reports_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inspection_{timestamp}.pdf"

        return str(reports_dir / filename)

    def _set_step(self, step: InspectionStep, message: str):
        """Define a etapa atual e emite signal."""
        self._current_step = step
        self.step_changed.emit(step, message)
        logger.debug(f"Inspection step: {step.value} - {message}")

    def _set_error(self, error: str):
        """Define estado de erro e emite signal."""
        self._set_step(InspectionStep.ERROR, error)
        self.inspection_failed.emit(error)

        # Criar resultado de erro
        result = InspectionResult(
            success=False,
            step=InspectionStep.ERROR,
            error=error
        )
        self.inspection_completed.emit(result)
