"""
handlers/keyboard_handler.py
-----------------------------

Gerencia eventos de teclado para controle de movimento CNC.

Centraliza o mapeamento de teclas para ações de movimento,
removendo lógica de keyboard do main_window.py.
"""

import logging
from typing import Optional, Callable
from PyQt6.QtCore import QObject, Qt, QEvent
from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class KeyboardEventHandler(QObject):
    """
    Handler centralizado para eventos de teclado.

    Responsabilidades:
        - Interceptar eventos de teclado via eventFilter
        - Mapear teclas direcionais para movimento CNC
        - Dispatch para MovementControlWidget
        - Gerenciar estado de keyboard_control_enabled

    Mapeamento de Teclas:
        ↑ (Up)      → Y negativo
        ↓ (Down)    → Y positivo
        ← (Left)    → X negativo
        → (Right)   → X positivo
        PageUp      → Z negativo
        PageDown    → Z positivo
    """

    # Signal emitido quando uma tecla de movimento é pressionada
    movement_key_pressed = None  # Será pyqtSignal se necessário

    def __init__(self, movement_widget=None, enable_control_callback=None):
        """
        Inicializa o handler de teclado.

        Args:
            movement_widget: MovementControlWidget para dispatch de comandos
            enable_control_callback: Callable que retorna bool (se keyboard está habilitado)
        """
        super().__init__()
        self.movement_widget = movement_widget
        self.enable_control_callback = enable_control_callback

        # Mapeamento de teclas para (eixo, direção)
        self.key_mapping = {
            Qt.Key.Key_Up: ("Y", -1),
            Qt.Key.Key_Down: ("Y", 1),
            Qt.Key.Key_Left: ("X", -1),
            Qt.Key.Key_Right: ("X", 1),
            Qt.Key.Key_PageUp: ("Z", -1),
            Qt.Key.Key_PageDown: ("Z", 1),
        }

    def set_movement_widget(self, widget):
        """
        Define o widget de movimento.

        Args:
            widget: MovementControlWidget
        """
        self.movement_widget = widget
        logger.debug("MovementWidget definido no KeyboardEventHandler")

    def set_enable_control_callback(self, callback: Callable[[], bool]):
        """
        Define callback para verificar se keyboard está habilitado.

        Args:
            callback: Função que retorna True se keyboard control está ativo
        """
        self.enable_control_callback = callback
        logger.debug("Callback de controle definido")

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """
        Intercepta eventos de teclado e dispara start/stop de movimento.

        Este método deve ser instalado no QApplication ou na janela principal:
            app.installEventFilter(keyboard_handler)
            # ou
            self.installEventFilter(keyboard_handler)

        Args:
            source: Objeto que gerou o evento
            event: Evento Qt (KeyPress ou KeyRelease)

        Returns:
            True se o evento foi processado, False caso contrário
        """
        # Verificar se keyboard control está habilitado
        if self.enable_control_callback and not self.enable_control_callback():
            return False

        # Apenas processar eventos de teclado
        if event.type() != QEvent.Type.KeyPress and event.type() != QEvent.Type.KeyRelease:
            return False

        # Ignorar eventos de repetição automática (tecla mantida pressionada)
        if event.isAutoRepeat():
            return False

        # Verificar se é uma tecla mapeada
        key = event.key()
        if key not in self.key_mapping:
            return False

        # Obter eixo e direção
        axis, direction = self.key_mapping[key]

        # Verificar se temos movement widget
        if not self.movement_widget:
            logger.warning("MovementWidget não definido, ignorando tecla")
            return False

        # KeyPress: Iniciar movimento
        if event.type() == QEvent.Type.KeyPress:
            logger.debug(f"KeyPress: {key.name} → {axis}{direction}")
            self._start_movement(axis, direction)
            return True

        # KeyRelease: Parar movimento
        elif event.type() == QEvent.Type.KeyRelease:
            logger.debug(f"KeyRelease: {key.name}")
            self._stop_movement()
            return True

        return False

    def _start_movement(self, axis: str, direction: int):
        """
        Inicia movimento no eixo especificado.

        Args:
            axis: Eixo ("X", "Y" ou "Z")
            direction: Direção (-1 ou +1)
        """
        try:
            if hasattr(self.movement_widget, 'start_movement'):
                self.movement_widget.start_movement(axis, direction)
                logger.debug(f"Movimento iniciado: {axis}{direction}")
            else:
                logger.error(f"MovementWidget não tem método start_movement()")
        except Exception as e:
            logger.error(f"Erro ao iniciar movimento: {e}")

    def _stop_movement(self):
        """
        Para movimento em andamento.
        """
        try:
            if hasattr(self.movement_widget, 'stop_movement'):
                self.movement_widget.stop_movement()
                logger.debug("Movimento parado")
            else:
                logger.error(f"MovementWidget não tem método stop_movement()")
        except Exception as e:
            logger.error(f"Erro ao parar movimento: {e}")

    def is_key_mapped(self, key: Qt.Key) -> bool:
        """
        Verifica se uma tecla está mapeada para movimento.

        Args:
            key: Tecla Qt

        Returns:
            True se a tecla está mapeada
        """
        return key in self.key_mapping

    def get_mapped_keys(self) -> list:
        """
        Retorna lista de teclas mapeadas.

        Returns:
            Lista de Qt.Key mapeados
        """
        return list(self.key_mapping.keys())
