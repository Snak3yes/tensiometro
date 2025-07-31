# plate_flow.py
from __future__ import annotations
import time
from enum import Enum, auto
from PyQt6.QtCore import QObject, QTimer

class FlowState(Enum):
    IDLE        = auto()
    MOVING_IN   = auto()
    PROCESSING  = auto()
    MOVING_OUT  = auto()

class PlateFlowManager(QObject):
    """
    Gerencia o fluxo de uma ÚNICA mesa:
        – monitora M20/M30 (botão do operador);
        – move a placa até o 1º fiducial;
        – dispara o SequenceControlWidget da aba;
        – ao terminar, devolve a placa ao operador;
        – sinaliza “done” em M21/M31 (pulso de 100 ms).
    """
    _POLL_MS = 100

    def __init__(self, ctrl, mesa_id: int, mesa_tab):
        """
        ctrl     → MultiAxisMotorController
        mesa_id  → 1 ou 2
        mesa_tab → TableProgramTab correspondente
        """
        super().__init__(mesa_tab)
        assert mesa_id in (1, 2)
        self._c       = ctrl
        self._tab     = mesa_tab
        self._mesa    = mesa_id
        self._state   = FlowState.IDLE

        if mesa_id == 1:
            self._mem_btn  = 'M20'
            self._mem_done = 'M21'
            self._y_axis   = 'Y1'
            self._y_limit  = ctrl.table_limits[1]['y'][1]
        else:
            self._mem_btn  = 'M30'
            self._mem_done = 'M31'
            self._y_axis   = 'Y2'
            self._y_limit  = ctrl.table_limits[2]['y'][1]

        self._addr_btn  = ctrl.addresses[self._mem_btn]
        self._addr_done = ctrl.addresses[self._mem_done]
        # estado anterior do botão físico (para borda ↑)
        self._btn_prev  = False

        # pooler – evita mexer no thread de GUI da aplicação
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll)
        self._timer.start(self._POLL_MS)

        # callback quando a sequência acaba
        self._tab.seq_widget.sequenceFinished.connect(self._on_sequence_finished)
        self._tab.seq_widget.sequenceError.connect(self._on_sequence_error)

    # -----------------------------------------------------------------
    #  P U B L I C
    # -----------------------------------------------------------------
    def poll_now(self):            # pode ser chamado em testes
        self._poll()

    # -----------------------------------------------------------------
    #  I N T E R N O S
    # -----------------------------------------------------------------
    def _poll(self):
        if (not self._c.connected or
                self._state is not FlowState.IDLE or
                not self._c._global_cycle_active):     # só depois do Start Geral
            return
        try:
            r = self._c.client.read_coils(self._addr_btn, count=1)
            if r.isError():
                return
            pressed = r.bits[0]
            if pressed and not self._btn_prev:         # Borda de subida
                self._start_send_cycle()
            self._btn_prev = pressed
        except Exception as exc:
            self._c.log(f"■ PlateFlow polling erro: {exc}")

    # ---------------------  S T A T E   M A C H I N E  ----------------
    def _start_send_cycle(self):
        """Etapa 1 – leva a placa para dentro."""
        # ----------------------------------------------------------
        #  LIMPA _targets de ciclos anteriores para que o próximo
        #  wait_for_idle() considere apenas o movimento atual.
        # ----------------------------------------------------------
        self._c._plc_motion_backend._targets.clear()
        fid_y = self._first_fiducial_y()
        if fid_y is None:
            # sem fiducial → usa primeiro ponto ou mantém posição actual
            fid_y = self._first_point_y() or 0
            self._c.log(f"■ Mesa {self._mesa}: sem fiducial; usando Y={fid_y}")
        self._state = FlowState.MOVING_IN
        self._c.log(f"■ Mesa {self._mesa}: enviando placa (destino Y={fid_y})")
        getattr(self._c, f'pulsos_spin_{self._y_axis}').setValue(int(fid_y))
        self._c.move_axis_absolute(self._y_axis)
        # espera aqui mesmo pois é simples
        if self._c._plc_motion_backend.wait_for_idle():
            self._start_sequence()
        else:
            self._error("Timeout movendo placa para dentro")

    def _start_sequence(self):
        """Etapa 2 – roda SequenceControlWidget em modo APPLY."""
        self._state = FlowState.PROCESSING
        # garante modo APPLY
        self._tab.seq_widget.radio_apply.setChecked(True)
        # --------------------------------------------------------------
        #  FIX   – informa ao controlador qual eixo Y físico
        #          está vinculado à sequência que será iniciada.
        #          SequenceRunnerThread usará esse atributo em vez de
        #          depender da aba currently selected.
        # --------------------------------------------------------------
        self._c._active_plate_y = self._y_axis   # 'Y1' ou 'Y2'
        self._tab.seq_widget._start()

    def _on_sequence_finished(self):
        if self._state != FlowState.PROCESSING:
            return
        # Etapa 3 – devolve a placa
        self._state = FlowState.MOVING_OUT
        limit = int(self._y_limit)
        self._c.log(f"■ Mesa {self._mesa}: devolvendo placa (Y→{limit})")
        getattr(self._c, f'pulsos_spin_{self._y_axis}').setValue(limit)
        self._c.move_axis_absolute(self._y_axis)
        if self._c._plc_motion_backend.wait_for_idle():
            self._finish_cycle()
        else:
            self._error("Timeout devolvendo placa")

    def _on_sequence_error(self, msg):
        if self._state == FlowState.PROCESSING:
            # sinaliza erro mas devolve placa ao operador
            self._error(f"Seq. erro: {msg}")
            self._return_after_error()

    def _finish_cycle(self):
        """Etapa 4 – emite pulso DONE e regressa ao estado IDLE."""
        self._state = FlowState.IDLE
        try:
            # pulso de 100 ms em M21 / M31
            self._c.client.write_coil(self._addr_done, True)
            QTimer.singleShot(100, lambda a=self._addr_done:
                              self._c.client.write_coil(a, False))
            # ------------------------------------------------------------------
            #  ZERA O OFFSET DINÂMICO APLICADO PELOS FIDUCIAIS
            #  Evita que ΔX/ΔY acumulado no ciclo anterior seja reutilizado
            #  e somado novamente aos destinos do próximo ciclo,
            #  o que causava travamento em wait_for_idle().
            # ------------------------------------------------------------------
            self._c._plc_motion_backend.apply_dynamic_offset(0, 0)
            # zera lista de metas atingidas
            self._c._plc_motion_backend._targets.clear()
        except Exception as exc:
            self._c.log(f"■ Erro pulso {self._mem_done}: {exc}")
        self._c.log(f"■ Mesa {self._mesa}: ciclo concluído ✓")

    # -----------------------------------------------------------------
    def _return_after_error(self):
        """
        Falhou durante PROCESSING: devolve a placa e emite DONE
        para que o ladder reset M20 / M30.
        """
        limit = int(self._y_limit)
        getattr(self._c, f'pulsos_spin_{self._y_axis}').setValue(limit)
        self._c.move_axis_absolute(self._y_axis)
        self._c._plc_motion_backend.wait_for_idle()
        # pulso de conclusão mesmo em erro
        try:
            self._c.client.write_coil(self._addr_done, True)
            QTimer.singleShot(100,
                              lambda a=self._addr_done: self._c.client.write_coil(a, False))
        except Exception:
            print("■ Erro pulso DONE após erro na sequência")
            pass
        # ------------------------------------------------------------------
        #  Mesmo em caso de erro devolvemos a placa e RESETAMOS o offset
        #  dinâmico para garantir que o próximo ciclo comece “limpo”.
        # ------------------------------------------------------------------
        self._c._plc_motion_backend.apply_dynamic_offset(0, 0)
        # limpa metas anteriores
        self._c._plc_motion_backend._targets.clear()
        self._state = FlowState.IDLE

    # -----------------------------------------------------------------
    def _first_fiducial_y(self):
        """Procura o 1º ponto fiducial e devolve coordenada Y em pulsos."""
        for p in self._tab.inspect_widget.positions():
            if (p.meta or {}).get('action') == 'fiducial':
                return p.y1 if self._mesa == 1 else p.y2
        return None
    
    def _first_point_y(self):
        """Retorna Y do primeiro ponto do programa (qualquer ação)."""
        try:
            p0 = self._tab.inspect_widget.positions()[0]
            return p0.y1 if self._mesa == 1 else p0.y2
        except IndexError:
            self._c.log(f"■ Mesa {self._mesa}: sem pontos no programa")
            return None

    def _error(self, msg):
        self._c.log(f"■ Mesa {self._mesa}: {msg}")
        self._state = FlowState.IDLE
