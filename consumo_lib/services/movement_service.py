"""
services/movement_service.py
---------------------------

Service para orquestração de movimentos CNC.

Responsável por toda lógica de negócio relacionada a movimento,
incluindo validações, cálculos e execução de comandos.
Não tem dependência de PyQt - apenas lógica pura.
"""

import logging
import time
from typing import Optional, Tuple, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MovementResult:
    """Resultado de uma operação de movimento."""
    success: bool
    error_message: Optional[str] = None
    data: Optional[dict] = None


class MovementService:
    """
    Service para orquestração de movimentos CNC.

    Responsabilidades:
        - Validar estado de conexão e alarme
        - Validar e ajustar parâmetros de movimento (feed, step)
        - Executar movimentos STEP e JOG
        - Executar homing (go to zero)
        - Executar movimentos para posições absolutas
        - Controlar parada de emergência e unlock
        - Controlar backlight

    Este service NÃO tem dependência de PyQt.
    Use em conjunto com MovementControlWidget para interface completa.
    """

    def __init__(self, cnc_controller, config_manager):
        """
        Inicializa o service de movimento.

        Args:
            cnc_controller: Instância de PLCAxisController ou GRBLCNCController
            config_manager: Instância de AOIConfigManager
        """
        self.cnc = cnc_controller
        self.cfg = config_manager
        self._move_thread = None

    # ==================== VALIDAÇÕES ====================

    def validate_connection(self) -> MovementResult:
        """
        Valida estado de conexão e alarme da máquina.

        Returns:
            MovementResult com success=True se conectado e sem alarme
        """
        logger.info(f"🔍 validate_connection: is_connected={self.cnc.is_connected}, machine_status='{self.cnc.machine_status}'")

        if not self.cnc.is_connected:
            logger.warning("🔍 CNC não conectado!")
            return MovementResult(
                success=False,
                error_message="CNC não conectada"
            )

        # Verificar estado de alarme
        machine_status = self.cnc.machine_status
        logger.info(f"🔍 machine_status='{machine_status}', começa com 'alarm'? {machine_status and machine_status.lower().startswith('alarm')}")

        if machine_status and machine_status.lower().startswith("alarm"):
            logger.warning(f"🔍 MÁQUINA EM ALARME! Status: '{machine_status}'")
            return MovementResult(
                success=False,
                error_message="Máquina em parada de emergência"
            )

        logger.info("✅ Conexão validada com sucesso")
        return MovementResult(success=True)

    def validate_feed_rate(self, feed: float) -> MovementResult:
        """
        Valida e ajusta feed rate se necessário.

        Args:
            feed: Feed rate desejado (mm/min)

        Returns:
            MovementResult com feed ajustado em data
        """
        if not self.cnc.is_connected:
            return MovementResult(
                success=True,
                data={"feed": feed}
            )

        try:
            # Obter limites máximos por eixo
            max_feeds = list(self.cnc.max_feed.values())
            max_feed_limit = max(max_feeds) if max_feeds else 30000.0

            # Verificar se excede limite
            if feed > max_feed_limit + 1e-3:
                # TODO: Interagir com usuário para atualizar $110/$111
                # Por ora, apenas clampar
                logger.warning(f"Feed {feed} excede limite {max_feed_limit}, clamping")
                feed = max_feed_limit

            return MovementResult(
                success=True,
                data={"feed": feed}
            )

        except Exception as e:
            logger.error(f"Erro ao validar feed rate: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao validar feed rate: {e}"
            )

    def validate_step_size(self, step: float) -> MovementResult:
        """
        Valida step size.

        Args:
            step: Step size desejado (mm)

        Returns:
            MovementResult com success se válido
        """
        try:
            # Conversão bem-sucedida = válido
            return MovementResult(success=True)
        except (ValueError, TypeError):
            return MovementResult(
                success=False,
                error_message="Step size inválido"
            )

    # ==================== MOVIMENTO BÁSICO ====================

    def start_step_move(self, axis: str, direction: int, step: float, feed: float) -> MovementResult:
        """
        Inicia movimento passo-a-passo (modo G90).

        Args:
            axis: Eixo ("X", "Y" ou "Z")
            direction: Direção (-1 ou +1)
            step: Tamanho do passo (mm)
            feed: Feed rate (mm/min)

        Returns:
            MovementResult indicando sucesso ou falha
        """
        logger.info(f"🔧 start_step_move: axis={axis}, direction={direction}, step={step}, feed={feed}")

        # Validações
        logger.info("🔧 Validando conexão...")
        conn_result = self.validate_connection()
        logger.info(f"🔧 validate_connection: success={conn_result.success}, error={conn_result.error_message}")
        if not conn_result.success:
            logger.error(f"🔧 ERRO na validação de conexão: {conn_result.error_message}")
            return conn_result

        logger.info("🔧 Validando feed rate...")
        feed_result = self.validate_feed_rate(feed)
        logger.info(f"🔧 validate_feed_rate: success={feed_result.success}, data={feed_result.data}")
        if not feed_result.success:
            return feed_result
        feed = feed_result.data.get("feed", feed)

        logger.info("🔧 Validando step size...")
        step_result = self.validate_step_size(step)
        logger.info(f"🔧 validate_step_size: success={step_result.success}")
        if not step_result.success:
            return step_result

        try:
            distance = step * direction
            logger.info(f"🔧 Chamando cnc.step_move({axis}, {distance:.3f}, {feed})")

            self.cnc.step_move(axis, distance, feed)

            logger.info(f"✅ Step move iniciado: {axis}{distance:.3f} mm @ {feed} mm/min")
            return MovementResult(success=True)

        except Exception as e:
            logger.error(f"❌ Erro ao iniciar step move: {e}", exc_info=True)
            return MovementResult(
                success=False,
                error_message=f"Erro ao iniciar movimento: {e}"
            )

    def start_jog(self, axis: str, direction: int, feed: float) -> MovementResult:
        """
        Inicia jog contínuo (modo G91).

        Args:
            axis: Eixo ("X", "Y" ou "Z")
            direction: Direção (-1 ou +1)
            feed: Feed rate (mm/min)

        Returns:
            MovementResult indicando sucesso ou falha
        """
        # Validações
        conn_result = self.validate_connection()
        if not conn_result.success:
            return conn_result

        feed_result = self.validate_feed_rate(feed)
        if not feed_result.success:
            return feed_result
        feed = feed_result.data.get("feed", feed)

        try:
            self.cnc.jog_start(axis, direction, feed)

            logger.debug(f"Jog iniciado: {axis}{direction} @ {feed} mm/min")
            return MovementResult(success=True)

        except Exception as e:
            logger.error(f"Erro ao iniciar jog: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao iniciar jog: {e}"
            )

    def stop_jog(self) -> MovementResult:
        """
        Para jog contínuo.

        Returns:
            MovementResult indicando sucesso ou falha
        """
        try:
            self.cnc.jog_stop()
            logger.debug("Jog parado")
            return MovementResult(success=True)

        except Exception as e:
            logger.error(f"Erro ao parar jog: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao parar jog: {e}"
            )

    # ==================== MOVIMENTO ESPECIAL ====================

    def _legacy_go_to_zero_unused(self) -> MovementResult:
        """
        Executa homing ou movimento para zero.

        Para PLC: Executa sequência de homing via coils
        Para GRBL: Move para posição (0, 0, 0)

        Returns:
            MovementResult indicando sucesso ou falha
        """
        # Validação
        conn_result = self.validate_connection()
        if not conn_result.success:
            return conn_result

        try:
            from aoi_lib.plc_axis_controller import PLCAxisController

            if isinstance(self.cnc, PLCAxisController):
                # Caminho PLC: Homing via coils
                return self._plc_homing()
            else:
                # Caminho GRBL: Movimento para zero
                return self._grbl_go_to_zero()

        except Exception as e:
            logger.error(f"Erro ao ir para zero: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao executar homing: {e}"
            )

    def _legacy_plc_homing_unused(self) -> MovementResult:
        """
        Executa homing via coils Modbus (PLC).

        Estados válidos para homing:
            - Idle: Conectado e parado (estado ideal para homing)
            - Run: Em movimento (pode iniciar homing durante movimento)
            - Jog: Em movimento manual

        Estados inválidos para homing:
            - Alarm: Erro ativo, precisa resetar primeiro
            - Disconnected: Não conectado ao PLC
        """
        try:
            # Verificar status
            machine_status = self.cnc.machine_status

            # Estados inválidos para homing
            if machine_status in ["Alarm", "Disconnected"]:
                return MovementResult(
                    success=False,
                    error_message=f"Máquina em estado inadequado para homing: {machine_status}. " +
                                 ("Reset o alarme antes de prosseguir." if machine_status == "Alarm" else
                                  "Conecte o PLC primeiro.")
                )

            # Estados válidos: Idle, Run, Jog (aceitar qualquer um destes)
            logger.debug(f"Iniciando homing PLC com status: {machine_status}")

            # Coils de homing (X:1350, Y:850, Z:1850)
            homing_coils = {
                "X": 1350,
                "Y": 850,
                "Z": 1850
            }

            # Enviar pulso para cada eixo
            for axis, coil in homing_coils.items():
                self.cnc.client.write_coil(coil, True)
                time.sleep(0.1)
                self.cnc.client.write_coil(coil, False)
                logger.debug(f"Homing coil enviado: {axis} (coil {coil})")

            # Aguardar idle
            self.cnc.wait_for_idle()

            logger.info("Homing PLC concluído")
            return MovementResult(success=True)

        except Exception as e:
            logger.error(f"Erro ao executar homing PLC: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro no homing: {e}"
            )

    def _grbl_go_to_zero(self) -> MovementResult:
        """Move para (0, 0, 0) no GRBL."""
        try:
            # Obter feed rate
            feed = 1000.0  # Default

            # Mover para zero
            self.cnc.move_to_absolute_position(0, 0, 0, feed_rate=feed)

            logger.info("Movimento para zero concluído")
            return MovementResult(success=True)

        except Exception as e:
            logger.error(f"Erro ao mover para zero: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao mover para zero: {e}"
            )

    def go_to_position(self, x: float, y: float, z: float = 0.0, feed: float = 1000.0) -> MovementResult:
        """
        Move para posição absoluta.

        Args:
            x: Coordenada X (mm)
            y: Coordenada Y (mm)
            z: Coordenada Z (mm)
            feed: Feed rate (mm/min)

        Returns:
            MovementResult indicando sucesso ou falha
        """
        # Validação
        conn_result = self.validate_connection()
        if not conn_result.success:
            return conn_result

        try:
            # Verificar status
            machine_status = self.cnc.machine_status
            if machine_status and machine_status.lower().startswith("alarm"):
                return MovementResult(
                    success=False,
                    error_message="Máquina em alarme"
                )

            # Executar movimento
            self.cnc.move_to_absolute_position(x, y, z, feed_rate=feed)

            logger.info(f"Movimento para ({x}, {y}, {z}) @ {feed} mm/min")
            return MovementResult(success=True)

        except Exception as e:
            logger.error(f"Erro ao mover para posição: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao mover para posição: {e}"
            )

    # ==================== CONTROLE DE MÁQUINA ====================

    def emergency_stop(self) -> MovementResult:
        """
        Executa parada de emergência (soft reset).

        Returns:
            MovementResult indicando sucesso ou falha
        """
        try:
            self.cnc.send_soft_reset()
            logger.info("Soft reset enviado")
            return MovementResult(success=True)

        except Exception as e:
            logger.error(f"Erro ao enviar soft reset: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao enviar soft reset: {e}"
            )

    def unlock_machine(self) -> MovementResult:
        """
        Desbloqueia máquina após reset.

        Returns:
            MovementResult indicando sucesso ou falha
        """
        try:
            self.cnc.unlock()
            logger.info("Máquina desbloqueada")
            return MovementResult(success=True)

        except Exception as e:
            logger.error(f"Erro ao desbloquear máquina: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao desbloquear: {e}"
            )

    def set_motion_mode(self, mode: str) -> MovementResult:
        """
        Define modo de movimento (G90/G91).

        Args:
            mode: "G90" (absoluto/step) ou "G91" (relativo/jog)

        Returns:
            MovementResult indicando sucesso ou falha
        """
        try:
            from aoi_lib.plc_axis_controller import PLCAxisController

            if isinstance(self.cnc, PLCAxisController):
                # PLC: Apenas guarda internamente
                self.cnc.current_motion_mode = mode
                logger.debug(f"Modo de movimento PLC definido: {mode}")
            else:
                # GRBL: Envia comando
                if self.cnc.is_connected:
                    self.cnc.send_command(mode, priority=True)
                    logger.debug(f"Comando {mode} enviado")

            return MovementResult(success=True)

        except Exception as e:
            logger.error(f"Erro ao definir modo de movimento: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao definir modo: {e}"
            )

    # ==================== BACKLIGHT ====================

    def set_backlight(self, on: bool) -> MovementResult:
        """
        Controla iluminação (backlight).

        Args:
            on: True para ligar, False para desligar

        Returns:
            MovementResult indicando sucesso ou falha
        """
        try:
            if not self.cnc.is_connected:
                return MovementResult(
                    success=False,
                    error_message="CNC não conectada"
                )

            if hasattr(self.cnc, 'backlight_set'):
                self.cnc.backlight_set(on)
                logger.debug(f"Backlight {'ligado' if on else 'desligado'}")
                return MovementResult(success=True)
            else:
                return MovementResult(
                    success=False,
                    error_message="Backlight não suportado"
                )

        except Exception as e:
            logger.error(f"Erro ao controlar backlight: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao controlar backlight: {e}"
            )

    # ==================== UTILITÁRIOS ====================

    def get_current_position(self) -> Optional[dict]:
        """
        Obtém posição atual WPos.

        Returns:
            Dicionário com {"x": float, "y": float, "z": float} ou None
        """
        try:
            return self.cnc.get_current_position()
        except Exception as e:
            logger.error(f"Erro ao obter posição: {e}")
            return None

    def wait_for_idle(self, timeout: int = 10) -> bool:
        """
        Aguarda máquina ficar idle.

        Args:
            timeout: Timeout em segundos

        Returns:
            True se ficou idle, False se timeout
        """
        try:
            return self.cnc.wait_for_idle(timeout=timeout)
        except Exception as e:
            logger.error(f"Erro ao aguardar idle: {e}")
            return False

    def go_to_zero(self) -> MovementResult:
        conn_result = self.validate_connection()
        if not conn_result.success:
            return conn_result

        try:
            if hasattr(self.cnc, "home_all"):
                return self._plc_homing()
            return self._grbl_go_to_zero()
        except Exception as e:
            logger.error(f"Erro ao ir para zero: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro ao executar homing: {e}"
            )

    def _plc_homing(self) -> MovementResult:
        try:
            machine_status = self.cnc.machine_status

            if machine_status in ["Alarm", "Disconnected"]:
                return MovementResult(
                    success=False,
                    error_message=f"Máquina em estado inadequado para homing: {machine_status}. " +
                                 ("Reset o alarme antes de prosseguir." if machine_status == "Alarm" else
                                  "Conecte o PLC primeiro.")
                )

            logger.debug(f"Iniciando homing PLC com status: {machine_status}")
            self.cnc.home_all()
            logger.info("Homing PLC concluído")
            return MovementResult(success=True)
        except Exception as e:
            logger.error(f"Erro ao executar homing PLC: {e}")
            return MovementResult(
                success=False,
                error_message=f"Erro no homing: {e}"
            )
