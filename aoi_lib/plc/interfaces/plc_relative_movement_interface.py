"""
Interface PLC Relative Movement - Contrato para movimento relativo

Define contrato para movimento de eixo em coordenadas relativas.
"""

from abc import ABC, abstractmethod


class PLCRelativeMovement(ABC):
    """
    Interface para movimento relativo do PLC.

    Responsabilidades:
    - Mover eixo por distância relativa
    - Mover eixo único em coordenadas relativas
    - Executar passo a passo (step) de movimento
    """

    @abstractmethod
    def move_relative(self, axis: str, distance: float, speed: float = 0.0) -> bool:
        """
        Move eixo por distância relativa.

        Args:
            axis: Eixo a ser movido ('X', 'Y', ou 'Z')
            distance: Distância relativa em pulsos
            speed: Taxa de avanço em pulsos/minuto

        Returns:
            True se movimento bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def move_relative_single_axis(self, axis: str, distance: float) -> bool:
        """
        Move único eixo em coordenadas relativas.

        Args:
            axis: Eixo a ser movido ('X', 'Y', ou 'Z')
            distance: Distância relativa em pulsos

        Returns:
            True se movimento bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def step_move(self, axis: str, steps: int, direction: str) -> bool:
        """
        Executa movimento passo a passo (step) do eixo.

        Args:
            axis: Eixo a ser movido ('X', 'Y', ou 'Z')
            steps: Número de passos
            direction: Direção ('forward' ou 'backward')

        Returns:
            True se movimento bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def get_position(self, axis: str) -> float:
        """
        Lê posição atual do eixo.

        Args:
            axis: Eixo a ser lido ('X', 'Y', ou 'Z')

        Returns:
            Posição atual em pulsos
        """
        pass
