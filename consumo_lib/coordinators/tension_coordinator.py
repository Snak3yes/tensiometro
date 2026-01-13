"""
coordinators/tension_coordinator.py
------------------------------------

Orquestra o fluxo completo de medição de tensão do stencil:
1. Configurar grid de medição (NxM pontos)
2. Mover CNC para cada posição
3. Descer sensor Z
4. Ler tensão via serial (AS-120N)
5. Subir sensor Z
6. Registrar medição
7. Gerar heatmap e relatório

Centraliza lógica espalhada pelo código e implementa
o padrão Coordinator para gerenciar interações complexas
entre CNC, câmera, sensor serial e UI.
"""

import logging
from typing import Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class TensionStep(Enum):
    """Etapas do fluxo de medição de tensão"""
    IDLE = "idle"
    CONFIGURING = "configuring"
    POSITIONING = "positioning"          # Movendo para posição
    DESCENDING = "descending"            # Descendo sensor Z
    READING = "reading"                  # Lendo tensão
    ASCENDING = "ascending"              # Subindo sensor Z
    MOVING_NEXT = "moving_next"          # Movendo para próximo ponto
    GENERATING_HEATMAP = "generating_heatmap"
    GENERATING_REPORT = "generating_report"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"


@dataclass
class TensionConfig:
    """Configuração de medição de tensão"""
    grid_size: int = 3                   # Grid 3x3 (9 pontos)
    step_x: float = 50.0                 # Distância X entre pontos (mm)
    step_y: float = 50.0                 # Distância Y entre pontos (mm)
    z_approach: float = 10.0             # Altitude de aproximação (mm)
    z_contact_depth: float = 2.0         # Profundidade de contato (mm)
    approach_speed: float = 500.0        # Velocidade de aproximação (mm/min)
    measurement_speed: float = 100.0     # Velocidade de medição (mm/min)
    retract_speed: float = 800.0         # Velocidade de retração (mm/min)
    serial_port: str = None              # Porta serial (auto-detected se None)
    baud_rate: int = 2400               # Taxa de transmissão (AS-120N)
    timeout: float = 5.0                 # Timeout de leitura (segundos)

    # Limites de segurança
    z_min_limit: float = -50.0           # Limite mínimo Z (segurança)
    z_max_limit: float = 10.0            # Limite máximo Z


@dataclass
class TensionPoint:
    """Ponto de medição"""
    x: float                              # Posição X (mm)
    y: float                              # Posição Y (mm)
    z: float = 0.0                        # Posição Z (mm)
    tension: Optional[float] = None       # Tensão medida (N/cm)
    status: str = "pending"               # pending, ok, warning, nok, error
    timestamp: Optional[datetime] = None  # Timestamp da medição
    error: Optional[str] = None           # Erro se houve


@dataclass
class TensionResult:
    """Resultado de medição de tensão"""
    success: bool
    step: TensionStep
    points: List[TensionPoint] = field(default_factory=list)
    grid_size: int = 3
    measurements: List[float] = field(default_factory=list)
    average_tension: Optional[float] = None
    min_tension: Optional[float] = None
    max_tension: Optional[float] = None
    classification: Optional[str] = None  # ok, warning, nok
    heatmap_path: Optional[str] = None
    report_path: Optional[str] = None
    error: Optional[str] = None
    summary: Optional[str] = None

    def __post_init__(self):
        if self.success and self.measurements:
            self.average_tension = sum(self.measurements) / len(self.measurements)
            self.min_tension = min(self.measurements)
            self.max_tension = max(self.measurements)


class TensionCoordinator(QObject):
    """
    Coordena o fluxo completo de medição de tensão.

    Responsabilidades:
        - Orquestrar movimento CNC + leitura serial
        - Gerenciar grid de medição (zig-zag pattern)
        - Controlar descida/subida segura do sensor
        - Emitir signals para notificar progresso
        - Gerar heatmap e relatório

    Substitui lógica espalhada entre main_window, tabs, e managers.
    """

    # Signals de progresso
    step_changed = pyqtSignal(TensionStep, str)  # step, message
    point_started = pyqtSignal(int, TensionPoint)  # index, point
    point_completed = pyqtSignal(int, TensionPoint)  # index, point
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    measurement_taken = pyqtSignal(float, float, float)  # x, y, tension

    # Signals específicos
    grid_generated = pyqtSignal(list)  # List[TensionPoint]
    all_measurements_completed = pyqtSignal(object)  # TensionResult
    heatmap_generated = pyqtSignal(str)  # heatmap_path

    # Signals finais
    measurement_completed = pyqtSignal(object)  # TensionResult
    measurement_failed = pyqtSignal(str)  # error_message

    def __init__(self, controller, config_manager):
        """
        Inicializa o coordinator.

        Args:
            controller: CNCAOIController
            config_manager: AOIConfigManager
        """
        super().__init__()
        self.controller = controller
        self.config = config_manager

        # Estado atual
        self._current_step = TensionStep.IDLE
        self._current_config: Optional[TensionConfig] = None
        self._grid_points: List[TensionPoint] = []
        self._current_point_index = 0
        self._is_paused = False
        self._should_stop = False

    # ==================== PROPRIEDADES ====================

    @property
    def current_step(self) -> TensionStep:
        """Retorna a etapa atual da medição."""
        return self._current_step

    @property
    def is_measuring(self) -> bool:
        """Retorna True se uma medição está em andamento."""
        return self._current_step != TensionStep.IDLE

    @property
    def is_paused(self) -> bool:
        """Retorna True se medição está pausada."""
        return self._is_paused

    @property
    def grid_size(self) -> int:
        """Retorna o tamanho do grid (NxN)."""
        return self._current_config.grid_size if self._current_config else 3

    @property
    def total_points(self) -> int:
        """Retorna o total de pontos a medir."""
        return len(self._grid_points)

    @property
    def completed_points(self) -> int:
        """Retorna o número de pontos completados."""
        return sum(1 for p in self._grid_points if p.tension is not None)

    @property
    def progress_percent(self) -> int:
        """Retorna o progresso em percentual."""
        if not self._grid_points:
            return 0
        return int(self.completed_points / len(self._grid_points) * 100)

    # ==================== MÉTODOS PÚBLICOS ====================

    def start_measurement(self, config: TensionConfig):
        """
        Inicia uma nova medição de tensão.

        Args:
            config: Configuração da medição
        """
        if self.is_measuring:
            logger.warning("Medição já em andamento")
            return

        self._current_config = config
        self._should_stop = False
        self._is_paused = False
        self._current_point_index = 0

        self._set_step(TensionStep.CONFIGURING, "Configurando medição...")

        try:
            # Gerar grid de pontos
            self._generate_grid()

            self._set_step(TensionStep.POSITIONING, "Posicionando no primeiro ponto...")
            self.progress_updated.emit(0, len(self._grid_points), "Iniciando medição")

            logger.info(f"Medição de tensão iniciada: {config.grid_size}x{config.grid_size} grid")

            # Iniciar medição do primeiro ponto
            self._measure_next_point()

        except Exception as e:
            error_msg = f"Erro ao iniciar medição: {e}"
            logger.error(error_msg)
            self._set_error(error_msg)

    def pause_measurement(self):
        """Pausa a medição em andamento."""
        if not self.is_measuring:
            logger.warning("Nenhuma medição em andamento para pausar")
            return

        self._is_paused = True
        self._set_step(TensionStep.PAUSED, "Medição pausada")
        logger.info("Medição pausada")

    def resume_measurement(self):
        """Retoma medição pausada."""
        if self._current_step != TensionStep.PAUSED:
            logger.warning("Medição não está pausada")
            return

        self._is_paused = False
        self._set_step(TensionStep.MOVING_NEXT, "Retomando medição...")
        logger.info("Medição retomada")

        # Continuar medição
        self._measure_next_point()

    def stop_measurement(self):
        """Para a medição em andamento."""
        if not self.is_measuring:
            logger.warning("Nenhuma medição em andamento para parar")
            return

        self._should_stop = True
        logger.info("Sinalização de parada enviada")

    def reset(self):
        """Reseta o estado da medição."""
        self._current_step = TensionStep.IDLE
        self._current_config = None
        self._grid_points = []
        self._current_point_index = 0
        self._is_paused = False
        self._should_stop = False

        logger.info("TensionCoordinator resetado")

    # ==================== MÉTODOS PRIVADOS ====================

    def _generate_grid(self):
        """Gera grid de pontos de medição (zig-zag pattern)."""
        grid = self._current_config.grid_size
        step_x = self._current_config.step_x
        step_y = self._current_config.step_y

        points = []
        index = 0

        # Zig-zag pattern
        for row in range(grid):
            # Linhas pares: esquerda → direita
            # Linhas ímpares: direita → esquerda
            cols = range(grid) if row % 2 == 0 else range(grid - 1, -1, -1)

            for col in cols:
                point = TensionPoint(
                    x=col * step_x,
                    y=row * step_y,
                    status="pending"
                )
                points.append(point)
                index += 1

        self._grid_points = points

        logger.info(f"Grid gerado: {len(points)} pontos ({grid}x{grid})")

        # Emitir signal
        self.grid_generated.emit(points)

    def _measure_next_point(self):
        """Mede o próximo ponto do grid."""
        # Verificar se deve parar
        if self._should_stop:
            self._finalize_measurement(stopped=True)
            return

        # Verificar se pausado
        if self._is_paused:
            return

        # Verificar se completou todos os pontos
        if self._current_point_index >= len(self._grid_points):
            self._finalize_measurement(stopped=False)
            return

        point = self._grid_points[self._current_point_index]

        # Emitir signal que vai medir este ponto
        self.point_started.emit(self._current_point_index, point)

        # Medir o ponto (sequência de operações)
        try:
            self._measure_point(point)
        except Exception as e:
            error_msg = f"Erro ao medir ponto {self._current_point_index}: {e}"
            logger.error(error_msg)

            # Marcar ponto com erro
            point.status = "error"
            point.error = str(e)

            # Continuar para próximo ponto
            self._current_point_index += 1
            self._measure_next_point()

    def _measure_point(self, point: TensionPoint):
        """
        Executa a sequência de medição para um ponto.

        Sequência:
        1. Mover para posição X, Y
        2. Descer sensor Z (approach rápido)
        3. Descer lentamente para contato
        4. Ler tensão via serial
        5. Subir sensor Z
        6. Registrar medição
        """
        # 1. Mover para posição X, Y
        self._set_step(TensionStep.POSITIONING, f"Movendo para ponto {self._current_point_index + 1}")
        self.controller.cnc.move_to(point.x, point.y, point.z)

        # Verificar se parou durante movimento
        if self._should_stop:
            return

        # 2. Descer para altura de aproximação
        self._set_step(TensionStep.DESCENDING, "Descendo sensor...")
        approach_z = self._current_config.z_approach
        self.controller.cnc.move_z(approach_z, speed=self._current_config.approach_speed)

        # 3. Descer lentamente para contato
        contact_z = approach_z - self._current_config.z_contact_depth

        # Verificar limite de segurança
        if contact_z < self._current_config.z_min_limit:
            raise ValueError(f"Profundidade de contato excede limite mínimo Z: {contact_z} < {self._current_config.z_min_limit}")

        self.controller.cnc.move_z(contact_z, speed=self._current_config.measurement_speed)

        # Aguardar estabilização
        import time
        time.sleep(0.5)  # 500ms para estabilizar

        # 4. Ler tensão
        self._set_step(TensionStep.READING, "Lendo tensão...")
        tension = self._read_tension()

        if tension is not None:
            point.tension = tension
            point.timestamp = datetime.now()
            point.status = "ok"  # Será reclassificado depois baseado em limites

            logger.info(f"Ponto {self._current_point_index}: ({point.x:.1f}, {point.y:.1f}) = {tension:.2f} N/cm")

            # Emitir signal
            self.measurement_taken.emit(point.x, point.y, tension)
        else:
            point.status = "error"
            point.error = "Falha na leitura"
            logger.error(f"Falha ao ler ponto {self._current_point_index}")

        # 5. Subir sensor Z
        self._set_step(TensionStep.ASCENDING, "Subindo sensor...")
        self.controller.cnc.move_z(approach_z, speed=self._current_config.retract_speed)
        self.controller.cnc.move_z(0, speed=self._current_config.retract_speed)

        # Emitir signal de ponto completado
        self.point_completed.emit(self._current_point_index, point)

        # Atualizar progresso
        self._current_point_index += 1
        progress = int(self._current_point_index / len(self._grid_points) * 100)
        self.progress_updated.emit(
            self._current_point_index,
            len(self._grid_points),
            f"{progress}% concluído"
        )

        # 6. Próximo ponto
        if self._current_point_index < len(self._grid_points):
            self._set_step(TensionStep.MOVING_NEXT, "Movendo para próximo ponto...")
            self._measure_next_point()
        else:
            self._finalize_measurement(stopped=False)

    def _read_tension(self) -> Optional[float]:
        """
        Lê tensão do sensor serial AS-120N.

        Returns:
            Tensão em N/cm ou None se falhar
        """
        try:
            # Importar aqui para evitar circular import
            from aoi_lib.tensiometer import TensiometerSerialManager

            # Criar gerenciador serial
            serial_mgr = TensiometerSerialManager()

            # Conectar se necessário
            port = self._current_config.serial_port
            if not serial_mgr.is_connected:
                if port is None:
                    # Auto-detectar porta
                    port = serial_mgr.auto_detect_port()
                    if port is None:
                        logger.error("Não foi possível detectar porta serial do tensiômetro")
                        return None

                if not serial_mgr.connect(port):
                    logger.error(f"Falha ao conectar na porta {port}")
                    return None

            # Ler tensão
            tension = serial_mgr.read_tension(timeout=self._current_config.timeout)

            return tension

        except Exception as e:
            logger.error(f"Erro ao ler tensão: {e}")
            return None

    def _finalize_measurement(self, stopped: bool = False):
        """
        Finaliza a medição e gera resultados.

        Args:
            stopped: True se foi interrompida pelo usuário
        """
        if stopped:
            self._set_step(TensionStep.IDLE, "Medição interrompida")
            logger.info("Medição interrompida pelo usuário")
            return

        self._set_step(TensionStep.GENERATING_HEATMAP, "Gerando heatmap...")

        try:
            # Criar resultado
            measurements = [p.tension for p in self._grid_points if p.tension is not None]

            result = TensionResult(
                success=len(measurements) > 0,
                step=TensionStep.COMPLETED,
                points=self._grid_points,
                grid_size=self._current_config.grid_size,
                measurements=measurements,
                summary=f"{len(measurements)} pontos medidos"
            )

            # Gerar heatmap
            self._generate_heatmap(result)

            # Classificar resultado
            self._classify_result(result)

            self._set_step(TensionStep.COMPLETED, "Medição concluída")

            # Emitir signals
            self.all_measurements_completed.emit(result)
            self.measurement_completed.emit(result)

            logger.info(f"Medição concluída: {len(measurements)} pontos medidos")

        except Exception as e:
            error_msg = f"Erro ao finalizar medição: {e}"
            logger.error(error_msg)
            self._set_error(error_msg)

    def _generate_heatmap(self, result: TensionResult):
        """
        Gera heatmap das medições.

        Args:
            result: Resultado da medição
        """
        try:
            # Importar visualizador
            from consumo_lib.widgets.tension_viz import TensionVisualizationWidget

            viz = TensionVisualizationWidget()

            # Carregar dados
            data = {
                'grid_size': result.grid_size,
                'measurements': result.measurements,
                'points': [(p.x, p.y, p.tension) for p in result.points if p.tension is not None]
            }

            viz.load_tension_data(data)

            # Salvar heatmap
            import matplotlib.pyplot as plt
            from datetime import datetime

            fig = viz.figure
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"temp/tension/heatmap_{timestamp}.png"

            import os
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            fig.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)

            result.heatmap_path = filepath

            logger.info(f"Heatmap gerado: {filepath}")

            # Emitir signal
            self.heatmap_generated.emit(filepath)

        except Exception as e:
            logger.error(f"Erro ao gerar heatmap: {e}")

    def _classify_result(self, result: TensionResult):
        """
        Classifica o resultado baseado nos critérios da receita.

        Args:
            result: Resultado a classificar
        """
        # TODO: Obter limites da receita atual
        # Por ora, usar valores padrão
        ok_min = 30.0      # N/cm
        warning_min = 20.0  # N/cm

        if result.average_tension < warning_min:
            result.classification = "nok"
        elif result.average_tension < ok_min:
            result.classification = "warning"
        else:
            result.classification = "ok"

        logger.info(f"Classificação: {result.classification} (média: {result.average_tension:.2f} N/cm)")

    def _set_step(self, step: TensionStep, message: str):
        """Define a etapa atual e emite signal."""
        self._current_step = step
        self.step_changed.emit(step, message)
        logger.debug(f"Tension step: {step.value} - {message}")

    def _set_error(self, error: str):
        """Define estado de erro e emite signal."""
        self._set_step(TensionStep.ERROR, error)
        self.measurement_failed.emit(error)
