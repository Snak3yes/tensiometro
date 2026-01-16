"""
Position Manager Facade - Interface simplificada para gerenciamento de posições

Facade que proporciona uma interface simplificada para gerenciar
posições de inspeção.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class PositionManagerFacade:
    """
    Facade para gerenciar posições de inspeção.

    Esta classe encapsula a complexidade de gerenciar posições,
    proporcionando uma interface simplificada para a MainWindow.

    Responsabilidades:
    - Adicionar posição atual
    - Remover posição selecionada
    - Selecionar posição
    - Atualizar display de posição

    A facade delega para PositionManagerController, mas proporciona
    métodos com nomes mais simples.
    """

    def __init__(self, position_controller, main_window):
        """
        Inicializa a facade.

        Args:
            position_controller: Controller de posições existente
            main_window: Janela principal (para atualizar UI)
        """
        self.position_controller = position_controller
        self.main_window = main_window

        logger.debug("PositionManagerFacade inicializada")

    def add_current_position(self, x: Optional[float] = None,
                            y: Optional[float] = None,
                            z: Optional[float] = None) -> bool:
        """
        Adiciona posição atual à lista.

        Args:
            x: Coordenada X (opcional, usa posição atual se None)
            y: Coordenada Y (opcional, usa posição atual se None)
            z: Coordenada Z (opcional, usa posição atual se None)

        Returns:
            True se adicionado com sucesso, False caso contrário
        """
        try:
            # Se não fornecido, lê posição atual do hardware
            if x is None or y is None or z is None:
                x, y, z = self._read_current_position()

            success = self.position_controller.add_position(x, y, z)

            if success:
                logger.info(f"Posição adicionada: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
                self.main_window.statusBar().showMessage(
                    f"Posição adicionada: ({x:.2f}, {y:.2f}, {z:.2f})", 3000
                )
            else:
                logger.warning("Falha ao adicionar posição")
                self.main_window.statusBar().showMessage(
                    "Falha ao adicionar posição", 3000
                )

            return success
        except Exception as e:
            logger.error(f"Erro ao adicionar posição: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao adicionar posição: {e}", 3000
            )
            return False

    def remove_position(self, index: int) -> bool:
        """
        Remove posição pelo índice.

        Args:
            index: Índice da posição a remover

        Returns:
            True se removida com sucesso, False caso contrário
        """
        try:
            success = self.position_controller.remove_position(index)

            if success:
                logger.info(f"Posição removida: índice {index}")
                self.main_window.statusBar().showMessage(
                    f"Posição {index} removida", 3000
                )
            else:
                logger.warning(f"Falha ao remover posição: índice {index}")
                self.main_window.statusBar().showMessage(
                    "Falha ao remover posição", 3000
                )

            return success
        except Exception as e:
            logger.error(f"Erro ao remover posição: {e}")
            self.main_window.statusBar().showMessage(
                f"Erro ao remover posição: {e}", 3000
            )
            return False

    def select_position(self, index: int) -> bool:
        """
        Seleciona uma posição da lista.

        Args:
            index: Índice da posição a selecionar

        Returns:
            True se selecionada com sucesso, False caso contrário
        """
        try:
            success = self.position_controller.select_position(index)

            if success:
                position = self.position_controller.get_position(index)
                if position:
                    logger.info(f"Posição selecionada: índice {index}, {position}")
            else:
                logger.warning(f"Falha ao selecionar posição: índice {index}")

            return success
        except Exception as e:
            logger.error(f"Erro ao selecionar posição: {e}")
            return False

    def update_position_display(self, x: float, y: float, z: float):
        """
        Atualiza display de posição na UI.

        Args:
            x: Coordenada X
            y: Coordenada Y
            z: Coordenada Z
        """
        try:
            if hasattr(self.main_window, 'movement_widget'):
                self.main_window.movement_widget.update_position_display(x, y, z)
                logger.debug(f"Display de posição atualizado: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
        except Exception as e:
            logger.error(f"Erro ao atualizar display de posição: {e}")

    def _read_current_position(self) -> Tuple[float, float, float]:
        """
        Lê posição atual do hardware.

        Returns:
            Tupla (x, y, z) com coordenadas atuais
        """
        try:
            controller = self.position_controller.controller
            x = controller.read_position('X')
            y = controller.read_position('Y')
            z = controller.read_position('Z')
            return (x, y, z)
        except Exception as e:
            logger.error(f"Erro ao ler posição atual: {e}")
            return (0.0, 0.0, 0.0)
