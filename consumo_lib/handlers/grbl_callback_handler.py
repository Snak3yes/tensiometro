"""
GRBL Callback Handler

Este módulo contém o handler para processar callbacks do GRBLStreamer,
isolando a lógica complexa de eventos GRBL do main_window.

Autor: Refatoração Session 19
Data: 2026-01-05
"""

import logging
from typing import Callable, Any, Dict, Tuple

logger = logging.getLogger("consumo_lib")


class GRBLCallbackHandler:
    """
    Gerencia callbacks massivos do GRBL.

    Responsabilidade:
    - Processar todos os eventos GRBL (on_hash_stateupdate, on_gcode_parser_stateupdate, on_stateupdate)
    - Atualizar estado do CNC (WCS, offsets, posição)
    - Sincronizar UI com estado GRBL
    - Converter MPos → WPos considerando offsets e inversões

    Atributos Gerenciados (do main_window):
    - active_wcs: Sistema de coordenadas ativo (G54-G59)
    - current_wcs_offset: Offset do WCS ativo
    - current_mpos: Última posição da máquina conhecida

    Nota: Este handler acessa e modifica atributos do main_window diretamente
    para manter compatibilidade com o código existente.
    """

    def __init__(self, main_window):
        """
        Inicializa o handler de callback GRBL.

        Args:
            main_window: Referência para AOIControllerApp (usada para acessar
                        controller, widgets e estado interno)
        """
        self.main_window = main_window
        self.controller = main_window.controller

    def create_callback(self) -> Callable:
        """
        Cria e retorna a função de callback para o GRBLStreamer.

        O callback retornado processa todos os eventos do GRBL e atualiza
        o estado do main_window e do controlador CNC.

        Returns:
            Callable: Função de callback com assinatura (eventstring, *data)
        """
        def grbl_callback(eventstring: str, *data):
            """
            Callback principal para eventos do GRBL.

            Args:
                eventstring: Tipo do evento (ex: "on_stateupdate", "on_hash_stateupdate")
                *data: Dados do evento (variável por tipo de evento)
            """
            logger.debug(f"CALLBACK: Evento '{eventstring}' recebido com data: {data}")

            # Roteia para o handler apropriado
            if eventstring == "on_hash_stateupdate":
                self._on_hash_stateupdate(data)
            elif eventstring == "on_gcode_parser_stateupdate":
                self._on_parser_stateupdate(data)
            elif eventstring == "on_stateupdate":
                self._on_stateupdate(data)
            elif eventstring == "on_write":
                logger.debug(f"CALLBACK: Comando enviado para GRBL: {data[0] if data else 'vazio'}")
            # Outros eventos podem ser adicionados aqui se necessário

        return grbl_callback

    # =========================================================================
    # HANDLERS DE EVENTOS GRBL
    # =========================================================================

    def _on_hash_stateupdate(self, data: tuple):
        """
        Processa atualização de hash (offsets G54-G59).

        Atualiza o offset do WCS ativo (G54) quando o comando $# é executado.
        IMPORTANTE: Só processa G54 se ele for o WCS ativo, para evitar
        que respostas tardias sobrescrevam offsets definidos manualmente.

        Args:
            data: Tupla com (hash_state,) onde hash_state é dict com chaves 'G54', 'G55', etc.
        """
        if not data or not isinstance(data[0], dict):
            return

        hash_state = data[0]

        # Processar G54 APENAS se o WCS ativo for G54
        if self.main_window.active_wcs == "G54":
            g54_offset_data = hash_state.get('G54')

            if isinstance(g54_offset_data, (list, tuple)) and len(g54_offset_data) >= 2:
                try:
                    new_offset_x_phys = float(g54_offset_data[0])
                    new_offset_y_phys = float(g54_offset_data[1])
                    new_offset_z_phys = float(g54_offset_data[2]) if len(g54_offset_data) > 2 else 0.0

                    # Converte Y físico → lógico (depende de invert_y)
                    if self.controller.cnc.invert_y:
                        new_offset_y_log = -new_offset_y_phys
                    else:
                        new_offset_y_log = new_offset_y_phys

                    # Atualiza offset no main_window
                    self.main_window.current_wcs_offset = {
                        'x': new_offset_x_phys,
                        'y': new_offset_y_phys,  # guardamos FÍSICO para operar com G10 L20
                        'z': new_offset_z_phys
                    }

                    logger.info(
                        "CALLBACK: Offset G54 atualizado "
                        f"(físico): {{x:{new_offset_x_phys:.3f}, y:{new_offset_y_phys:.3f}, z:{new_offset_z_phys:.3f}}}; "
                        f"(lógico Y={new_offset_y_log:.3f})"
                    )
                except (ValueError, TypeError):
                    logger.error(
                        f"CALLBACK: Erro ao converter offset G54 de $#: {g54_offset_data}"
                    )
            else:
                logger.warning(
                    f"CALLBACK: Offset G54 não encontrado ou inválido nos dados hash "
                    f"para WCS ativo G54: {hash_state}"
                )
        else:
            logger.debug(
                f"CALLBACK: Ignorando atualização de offset G54 de $# "
                f"porque WCS ativo é {self.main_window.active_wcs}"
            )

    def _on_parser_stateupdate(self, data: tuple):
        """
        Processa atualização do estado do parser G-code.

        Atualiza:
        - WCS ativo (G54-G59)
        - Modo de distância (G90/G91)
        - Sincroniza UI de modo absoluto/relativo

        Args:
            data: Tupla com (parser_state,) onde parser_state é lista com estado do parser
        """
        if not data or not isinstance(data[0], list) or len(data[0]) <= 1:
            return

        parser_state = data[0]

        # parser_state[1] = WCS ativo (ex: "54", "55")
        # parser_state[4] = Modo de distância (ex: "90" para G90, "91" para G91)
        new_active_wcs = f"G{parser_state[1]}"
        new_distance_mode = f"G{parser_state[4]}"

        # Atualiza WCS ativo se mudou
        if new_active_wcs != self.main_window.active_wcs:
            logger.info(
                f"CALLBACK: WCS Ativo mudou de {self.main_window.active_wcs} "
                f"para {new_active_wcs}"
            )
            self.main_window.active_wcs = new_active_wcs

        # Sincroniza UI de modo G90/G91
        if hasattr(self.main_window, 'movement_widget'):
            if new_distance_mode == "G90":
                if not self.main_window.movement_widget.mode_absolute.isChecked():
                    logger.info("CALLBACK ($G): Sincronizando UI para G90 (Absoluto)")
                    self.main_window.movement_widget.mode_absolute.setChecked(True)
                    self.main_window.movement_widget.mode_relative.setChecked(False)
            elif new_distance_mode == "G91":
                if not self.main_window.movement_widget.mode_relative.isChecked():
                    logger.info("CALLBACK ($G): Sincronizando UI para G91 (Relativo)")
                    self.main_window.movement_widget.mode_absolute.setChecked(False)
                    self.main_window.movement_widget.mode_relative.setChecked(True)

    def _on_stateupdate(self, data: tuple):
        """
        Processa atualização de estado (posição e status da máquina).

        Responsabilidade mais complexa:
        - Atualiza status da máquina (Idle, Run, Hold, etc.)
        - Converte MPos → WPos calculada
        - Suporta modo cartesiano E CoreXY
        - Aplica inversões de eixo configuradas
        - Atualiza posição no controlador

        Args:
            data: Tupla com (state, mpos_tuple, wpos_tuple)
                  - state: Status da máquina
                  - mpos_tuple: Posição da máquina (X, Y, Z)
                  - wpos_tuple: Posição de trabalho (IGNORADO, vem zerado)
        """
        if len(data) < 3:
            logger.error(
                f"CALLBACK: 'on_stateupdate' recebido com dados insuficientes "
                f"(len={len(data)}). Dados: {data}"
            )
            return

        state = data[0]
        mpos_tuple = data[1]  # Posição da Máquina (MPos)
        # wpos_tuple = data[2]  # IGNORADO - vem zerado do GRBL

        logger.debug(f"CALLBACK DETALHADO: state={state}, mpos={mpos_tuple}")

        # Atualiza estado da máquina
        old_state = self.controller.cnc.machine_status if hasattr(
            self.controller.cnc, 'machine_status'
        ) else None
        self.controller.cnc.machine_status = state

        if old_state != state:
            logger.debug(f"CALLBACK: Estado da máquina mudou de '{old_state}' para '{state}'")

        # Calcular WPOS a partir de MPOS e do offset armazenado
        if isinstance(mpos_tuple, (list, tuple)) and len(mpos_tuple) >= 2:
            try:
                self._process_position_update(mpos_tuple)
            except (ValueError, TypeError, IndexError) as e:
                logger.error(
                    f"CALLBACK: Erro ao processar MPOS ou calcular WPOS: {e}, "
                    f"mpos={mpos_tuple}"
                )
        else:
            logger.error(
                f"CALLBACK: Formato inválido para MPOS: {type(mpos_tuple)}, "
                f"valor: {mpos_tuple}"
            )

    def _process_position_update(self, mpos_tuple: tuple):
        """
        Processa atualização de posição e calcula WPos.

        Este método encapsula a lógica complexa de conversão MPos → WPos,
        suportando modos cartesianos e CoreXY, com inversões de eixo.

        Args:
            mpos_tuple: Tupla (x, y, z) com posição física da máquina
        """
        # 1) valores FÍSICOS reportados pelo GRBL
        mpos_x_phys = float(mpos_tuple[0])
        mpos_y_phys = float(mpos_tuple[1])
        mpos_z_phys = float(mpos_tuple[2]) if len(mpos_tuple) > 2 else 0.0

        # 2) guarda MPos física para rotinas G10
        self.main_window.current_mpos = {
            'x': mpos_x_phys,
            'y': mpos_y_phys,
            'z': mpos_z_phys
        }

        # 3) Converte considerando o modo de cinemática
        if self.controller.cnc.kinematics_mode == "corexy":
            # MODO COREXY
            calculated_wpos = self._calculate_wpos_corexy(
                mpos_x_phys, mpos_y_phys, mpos_z_phys
            )
        else:
            # MODO CARTESIANO
            calculated_wpos = self._calculate_wpos_cartesian(
                mpos_x_phys, mpos_y_phys, mpos_z_phys
            )

        # 4) Atualiza posição no controlador se mudou
        self._update_position_if_changed(calculated_wpos)

    def _calculate_wpos_corexy(
        self,
        mpos_x_phys: float,
        mpos_y_phys: float,
        mpos_z_phys: float
    ) -> Dict[str, float]:
        """
        Calcula WPos em modo CoreXY.

        No CoreXY:
        - mpos_x_phys = posição do motor A
        - mpos_y_phys = posição do motor B
        - Precisa converter A,B → X,Y cartesianas

        Args:
            mpos_x_phys: Posição física do motor A
            mpos_y_phys: Posição física do motor B
            mpos_z_phys: Posição física do eixo Z

        Returns:
            Dict com {'x', 'y', 'z'} da posição de trabalho calculada
        """
        # Converte A,B → X,Y cartesianas
        x_cart, y_cart = self.controller.cnc._convert_ab_to_xy(
            mpos_x_phys, mpos_y_phys
        )

        # Converte offset de motores → cartesianas
        off_a = self.main_window.current_wcs_offset['x']
        off_b = self.main_window.current_wcs_offset['y']
        off_x_cart, off_y_cart = self.controller.cnc._convert_ab_to_xy(off_a, off_b)
        off_z_cart = self.main_window.current_wcs_offset['z']

        # Aplica inversão lógica se configurada
        y_cart_log = -y_cart if self.controller.cnc.invert_y else y_cart
        z_cart_log = -mpos_z_phys if self.controller.cnc.invert_z else mpos_z_phys

        # Aplica inversão também ao offset para consistência
        off_y_cart_log = -off_y_cart if self.controller.cnc.invert_y else off_y_cart
        off_z_cart_log = -off_z_cart if self.controller.cnc.invert_z else off_z_cart

        # Calcula WPos usando coordenadas cartesianas
        return {
            'x': x_cart - off_x_cart,
            'y': y_cart_log - off_y_cart_log,
            'z': z_cart_log - off_z_cart_log
        }

    def _calculate_wpos_cartesian(
        self,
        mpos_x_phys: float,
        mpos_y_phys: float,
        mpos_z_phys: float
    ) -> Dict[str, float]:
        """
        Calcula WPos em modo cartesiano.

        Modo padrão onde cada motor corresponde a um eixo cartesiano.

        Args:
            mpos_x_phys: Posição física do eixo X
            mpos_y_phys: Posição física do eixo Y
            mpos_z_phys: Posição física do eixo Z

        Returns:
            Dict com {'x', 'y', 'z'} da posição de trabalho calculada
        """
        # Aplica inversão lógica
        mpos_y_log = -mpos_y_phys if self.controller.cnc.invert_y else mpos_y_phys
        mpos_z_log = -mpos_z_phys if self.controller.cnc.invert_z else mpos_z_phys

        # Aplica inversão no offset
        off_y_log = (
            -self.main_window.current_wcs_offset['y']
            if self.controller.cnc.invert_y
            else self.main_window.current_wcs_offset['y']
        )
        off_z_log = (
            -self.main_window.current_wcs_offset['z']
            if self.controller.cnc.invert_z
            else self.main_window.current_wcs_offset['z']
        )

        # Calcula WPos
        return {
            'x': mpos_x_phys - self.main_window.current_wcs_offset['x'],
            'y': mpos_y_log - off_y_log,
            'z': mpos_z_log - off_z_log
        }

    def _update_position_if_changed(self, new_position: Dict[str, float]):
        """
        Atualiza posição no controlador se houve mudança significativa.

        Args:
            new_position: Dict com {'x', 'y', 'z'} da nova posição
        """
        old_position = None
        if hasattr(self.controller.cnc, 'current_position'):
            old_position = self.controller.cnc.current_position.copy()

        logger.debug(
            f"CALLBACK: MPos offset={self.main_window.current_wcs_offset}, "
            f"WPos Calculada={new_position}"
        )
        logger.debug(
            f"CALLBACK: Tentando atualizar posição interna (usando WPOS CALCULADA) "
            f"para: {new_position}"
        )

        # Verifica se posição mudou significativamente (> 0.0001 mm)
        position_changed = (
            old_position is None or
            abs(old_position['x'] - new_position['x']) > 1e-4 or
            abs(old_position['y'] - new_position['y']) > 1e-4 or
            abs(old_position.get('z', 0.0) - new_position.get('z', 0.0)) > 1e-4
        )

        if position_changed:
            logger.info(
                f"CALLBACK: POSIÇÃO INTERNA ATUALIZADA (usando WPOS CALCULADA): "
                f"{old_position} -> {new_position}"
            )
            self.controller.cnc.current_position = new_position
