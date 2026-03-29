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
        logger.info("🟢 KeyboardEventHandler.__init__() chamado - CRIANDO handler")
        self.movement_widget = movement_widget
        self.enable_control_callback = enable_control_callback
        logger.info(f"🟢 movement_widget: {movement_widget}")
        logger.info(f"🟢 enable_control_callback: {enable_control_callback}")

        # Mapeamento de teclas para (eixo, direção)
        self.key_mapping = {
            Qt.Key.Key_Up: ("Y", -1),
            Qt.Key.Key_Down: ("Y", 1),
            Qt.Key.Key_Left: ("X", -1),
            Qt.Key.Key_Right: ("X", 1),
            Qt.Key.Key_PageUp: ("Z", -1),
            Qt.Key.Key_PageDown: ("Z", 1),
        }
        logger.info(f"🟢 Mapeamento de teclas configurado: {len(self.key_mapping)} teclas")

    def set_movement_widget(self, widget):
        """
        Define o widget de movimento.

        Args:
            widget: MovementControlWidget
        """
        logger.info(f"🔧 set_movement_widget() chamado com widget: {widget}")
        logger.info(f"🔧 widget type: {type(widget)}")
        self.movement_widget = widget
        logger.info("✅ MovementWidget definido no KeyboardEventHandler")

    def set_enable_control_callback(self, callback: Callable[[], bool]):
        """
        Define callback para verificar se keyboard está habilitado.

        Args:
            callback: Função que retorna True se keyboard control está ativo
        """
        logger.info(f"🔧 set_enable_control_callback() chamado com callback: {callback}")
        self.enable_control_callback = callback
        logger.info("✅ Callback de controle definido")

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
        # PROTEÇÃO contra KeyboardInterrupt causado por Windows Defender
        # O antivírus pode bloquear .pyc files durante primeira execução
        # causando KeyboardInterrupt no event loop do Qt
        try:
            # 🔴 LOG GLOBAL: Capturar TODOS os eventos para verificar se eventFilter está sendo chamado
            event_type = event.type()
            if event_type in [QEvent.Type.KeyPress, QEvent.Type.KeyRelease]:
                logger.warning(f"⚡️ EVENT FILTER CHAMADO: type={event_type}, source={source.__class__.__name__}")

            # Apenas processar eventos de teclado
            if event.type() != QEvent.Type.KeyPress and event.type() != QEvent.Type.KeyRelease:
                return False

            # Log inicial para depuração
            key = event.key()
            # Converter key (int) para Qt.Key para poder acessar métodos
            qt_key = Qt.Key(key)
            key_name = qt_key.name if hasattr(qt_key, 'name') else f"Key_{key}"
            logger.debug(f"🔑 KeyboardEventHandler: event.type={event.type()}, key={key}, key_name={key_name}")

            # Verificar se keyboard control está habilitado
            if self.enable_control_callback:
                enabled = self.enable_control_callback()
                logger.debug(f"🔑 Keyboard control habilitado: {enabled}")
                if not enabled:
                    logger.debug("🔑 Keyboard control desabilitado, ignorando evento")
                    return False
            else:
                logger.warning("🔑 enable_control_callback não definido!")
                return False

            # Ignorar eventos de repetição automática (tecla mantida pressionada)
            if event.isAutoRepeat():
                logger.debug("🔑 Auto-repeat detectado, ignorando")
                return False

            # Verificar se é uma tecla mapeada
            if key not in self.key_mapping:
                logger.debug(f"🔑 Tecla {key_name} não está mapeada, ignorando")
                return False

            # Obter eixo e direção
            axis, direction = self.key_mapping[key]
            logger.debug(f"🔑 Tecla mapeada: {key_name} → {axis}{direction}")

            # Verificar se temos movement widget
            if not self.movement_widget:
                logger.warning("MovementWidget não definido, ignorando tecla")
                return False

            # KeyPress: Iniciar movimento
            if event.type() == QEvent.Type.KeyPress:
                logger.info(f"🎮 KeyPress: {key_name} → Iniciando movimento {axis}{direction}")
                self._start_movement(axis, direction)
                return True

            # KeyRelease: Parar movimento
            elif event.type() == QEvent.Type.KeyRelease:
                logger.info(f"🎮 KeyRelease: {key_name} → Parando movimento")
                self._stop_movement()
                return True

            return False

        except KeyboardInterrupt:
            # Windows Defender bloqueou .pyc durante execução
            # Ignorar evento e continuar normalmente
            logger.warning("⚠️ KeyboardInterrupt capturado no eventFilter - Windows Defender interferência")
            return False
        except Exception as e:
            # Qualquer outro erro - log e continuar
            logger.error(f"❌ Erro no eventFilter: {e}")
            return False

    def _start_movement(self, axis: str, direction: int):
        """
        Inicia movimento no eixo especificado.

        Args:
            axis: Eixo ("X", "Y" ou "Z")
            direction: Direção (-1 ou +1)
        """
        try:
            logger.debug(f"🔧 _start_movement chamado: axis={axis}, direction={direction}")
            logger.debug(f"🔧 movement_widget type: {type(self.movement_widget)}")
            logger.debug(f"🔧 movement_widget tem start_movement: {hasattr(self.movement_widget, 'start_movement')}")

            if hasattr(self.movement_widget, 'start_movement'):
                logger.info(f"🎯 Chamando movement_widget.start_movement({axis}, {direction})")
                self.movement_widget.start_movement(axis, direction)
                logger.info(f"✅ Movimento iniciado: {axis}{direction}")
            else:
                logger.error(f"❌ MovementWidget não tem método start_movement()")
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar movimento: {e}", exc_info=True)

    def _stop_movement(self):
        """
        Para movimento em andamento.
        """
        try:
            logger.debug(f"🛑 _stop_movement chamado")
            logger.debug(f"🛑 movement_widget tem stop_movement: {hasattr(self.movement_widget, 'stop_movement')}")

            if hasattr(self.movement_widget, 'stop_movement'):
                logger.info(f"🎯 Chamando movement_widget.stop_movement()")
                self.movement_widget.stop_movement()
                logger.info(f"✅ Movimento parado")
            else:
                logger.error(f"❌ MovementWidget não tem método stop_movement()")
        except Exception as e:
            logger.error(f"❌ Erro ao parar movimento: {e}", exc_info=True)

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
