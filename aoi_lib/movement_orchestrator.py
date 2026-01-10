"""
movement_orchestrator.py
------------------------
Orquestrador de movimentos e controle de máquina.

Este módulo centraliza a lógica de controle de eixos, validações de segurança
e gerenciamento de estado da máquina, independente de interface gráfica.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class MovementResult:
    """Resultado de uma operação de movimento/controle."""
    success: bool
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class MovementOrchestrator:
    """
    Orquestrador de lógica de movimento.
    
    Responsabilidades:
    - Validar pré-condições (conexão, estado de alarme)
    - Validar parâmetros (feed rate, step size)
    - Executar comandos de movimento (JOG, STEP, Absoluto)
    - Gerenciar recursos da máquina (Backlight, Reset, Unlock)
    """
    
    def __init__(self, controller, config_manager=None):
        """
        Inicializa o orquestrador.
        
        Args:
            controller: Instância de CNCAOIController ou PLCAxisController
            config_manager: Instância de AOIConfigManager (opcional)
        """
        self.controller = controller
        self.config = config_manager
        
        # Detecta se é o controlador principal wrapper ou direto
        if hasattr(controller, 'cnc'):
            self.cnc = controller.cnc
        else:
            self.cnc = controller

    def _validate_connection(self) -> MovementResult:
        """Verifica se está conectado."""
        if not self.cnc.is_connected:
            return MovementResult(False, "CNC não conectada")
        return MovementResult(True)

    def _validate_machine_state(self) -> MovementResult:
        """Verifica se a máquina está em estado de erro."""
        status = getattr(self.cnc, 'machine_status', '')
        if status and str(status).lower().startswith('alarm'):
            return MovementResult(False, f"Máquina em alarme: {status}")
        return MovementResult(True)

    def validate_feed_rate(self, feed: float) -> MovementResult:
        """
        Valida e ajusta feed rate.
        
        Returns:
            MovementResult: data['feed'] contém o valor validado/ajustado.
                            data['clamped'] boolean indica se houve ajuste.
        """
        if not self.cnc.is_connected:
            return MovementResult(True, data={'feed': feed, 'clamped': False})
            
        try:
            max_feeds = list(self.cnc.max_feed.values())
            max_limit = max(max_feeds) if max_feeds else 30000.0
            
            if feed > max_limit:
                return MovementResult(True, data={'feed': max_limit, 'clamped': True, 'original': feed, 'limit': max_limit})
            
            return MovementResult(True, data={'feed': feed, 'clamped': False})
        except Exception as e:
            return MovementResult(False, f"Erro validando feed: {e}")

    def jog(self, axis: str, direction: int, feed: float) -> MovementResult:
        """Inicia movimento JOG (contínuo)."""
        if not (res := self._validate_connection()).success: return res
        if not (res := self._validate_machine_state()).success: return res
        
        # Valida feed
        f_res = self.validate_feed_rate(feed)
        if not f_res.success: return f_res
        valid_feed = f_res.data['feed']
        
        try:
            self.cnc.jog_start(axis, direction, valid_feed)
            return MovementResult(True)
        except Exception as e:
            logger.error(f"Erro no jog: {e}")
            return MovementResult(False, str(e))

    def stop_jog(self) -> MovementResult:
        """Para movimento JOG."""
        try:
            self.cnc.jog_stop()
            return MovementResult(True)
        except Exception as e:
            return MovementResult(False, str(e))

    def step_move(self, axis: str, direction: int, step: float, feed: float) -> MovementResult:
        """Executa movimento incremental (STEP)."""
        if not (res := self._validate_connection()).success: return res
        if not (res := self._validate_machine_state()).success: return res
        
        f_res = self.validate_feed_rate(feed)
        if not f_res.success: return f_res
        valid_feed = f_res.data['feed']
        
        try:
            distance = step * direction
            self.cnc.step_move(axis, distance, valid_feed)
            return MovementResult(True)
        except Exception as e:
            logger.error(f"Erro no step move: {e}")
            return MovementResult(False, str(e))

    def move_absolute(self, x: float, y: float, z: float, feed: float) -> MovementResult:
        """Move para posição absoluta."""
        if not (res := self._validate_connection()).success: return res
        if not (res := self._validate_machine_state()).success: return res
        
        f_res = self.validate_feed_rate(feed)
        valid_feed = f_res.data['feed']
        
        try:
            self.cnc.move_to_absolute_position(x, y, z, feed_rate=valid_feed)
            return MovementResult(True)
        except Exception as e:
            return MovementResult(False, str(e))

    def home(self) -> MovementResult:
        """Executa sequência de homing."""
        if not (res := self._validate_connection()).success: return res
        
        # Homing pode ser executado mesmo em alarme? Depende do controlador.
        # Geralmente não.
        if not (res := self._validate_machine_state()).success: return res
        
        try:
            # Detecta tipo de controlador para estratégia de homing
            from aoi_lib.plc_axis_controller import PLCAxisController
            if isinstance(self.cnc, PLCAxisController):
                # Lógica específica PLC
                # Coils padrão: X:1350, Y:850, Z:1850
                import time
                coils = {'X': 1350, 'Y': 850, 'Z': 1850}
                for axis, addr in coils.items():
                    self.cnc.client.write_coil(addr, True)
                    time.sleep(0.1)
                    self.cnc.client.write_coil(addr, False)
                self.cnc.wait_for_idle()
            else:
                # GRBL move para zero
                self.cnc.move_to_absolute_position(0, 0, 0, feed_rate=1000)
                
            return MovementResult(True)
        except Exception as e:
            return MovementResult(False, f"Erro no homing: {e}")

    def set_backlight(self, on: bool) -> MovementResult:
        """Controla iluminação."""
        if not (res := self._validate_connection()).success: return res
        
        if hasattr(self.cnc, 'backlight_set'):
            try:
                self.cnc.backlight_set(on)
                return MovementResult(True)
            except Exception as e:
                return MovementResult(False, str(e))
        return MovementResult(False, "Controlador não suporta backlight")

    def emergency_stop(self) -> MovementResult:
        """Envia soft reset."""
        try:
            if hasattr(self.cnc, 'send_soft_reset'):
                self.cnc.send_soft_reset()
                return MovementResult(True)
            return MovementResult(False, "Comando não suportado")
        except Exception as e:
            return MovementResult(False, str(e))

    def unlock(self) -> MovementResult:
        """Desbloqueia máquina."""
        try:
            if hasattr(self.cnc, 'unlock'):
                self.cnc.unlock()
                return MovementResult(True)
            return MovementResult(False, "Comando não suportado")
        except Exception as e:
            return MovementResult(False, str(e))
