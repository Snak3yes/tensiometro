"""
Interface PLC Absolute Movement - Contrato para movimento absoluto

Define contrato para movimento de eixo em coordenadas absolutas.
"""

from abc import ABC, abstractmethod


class IPLCAbsoluteMovement(ABC):
    """
    Interface para movimento absoluto do PLC.

    Responsabilidades:
    - Mover para posição absoluta em coordenadas
    - Definir zero da máquina
    - Mover para posição XYZ absoluta
    - Configurar taxa de avanço (feed rate)
    """

    @abstractmethod
    def move_absolute(self, axis: str, position: float, speed: float = 0.0) -> bool:
        """
        Move eixo para posição absoluta.

        Args:
            axis: Eixo a ser movido ('X', 'Y', ou 'Z')
            position: Posição absoluta em pulsos
            speed: Taxa de avanço em pulses/minuto

        Returns:
            True se movimento bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def move_to_absolute_position(self, x: float, y: float, z: float,
                                 speed_x: float = 0.0, speed_y: float = 0.0, speed_z: float = 0.0) -> bool:
        """
        Move para posição XYZ absoluta.

        Args:
            x: Posição X em pulsos
            y: Posição Y em pulsos
            z: Posição Z em pulsos
            speed_x: Velocidade X em pulsos/minuto
            speed_y: Velocidade Y em pulsos/minuto
            speed_z: Velocidade Z em pulsos/minuto

        Returns:
            True se movimento bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def set_zero(self) -> None:
        """
        Define posição atual da máquina como zero (zero absoluto).
        """
        pass

    @abstractmethod
    def set_feed_rate(self, feed_rate: float) -> None:
        """
        Configura taxa de avanço padrão.

        Args:
            feed_rate: Taxa de avanço em pulsos/minuto
        """
        pass

    @abstractmethod
    def apply_motion_pulses(self, axis: str, pulses: int) -> bool:
        """
        Aplica pulsos de movimento (método interno de baixo nível).

        Args:
            axis: Eixo a ser movido
            pulses: Número de pulsos a aplicar

        Returns:
            True se aplicado com sucesso, False caso contrário
        """
        pass
