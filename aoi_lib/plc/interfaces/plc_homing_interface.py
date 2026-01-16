"""
Interface PLC Homing - Contrato para homing de eixos

Define contrato para operações de homing (referência zero) do PLC.
"""

from abc import ABC, abstractmethod


class IPLCHoming(ABC):
    """
    Interface para homing de eixos da máquina.

    Responsabilidades:
    - Realizar homing de todos os eixos
    - Realizar homing de eixo único
    - Desbloquear eixos
    """

    @abstractmethod
    def home_all(self) -> bool:
        """
        Realiza homing de todos os eixos (X, Y, Z).

        Returns:
            True se homing bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def home_axis(self, axis: str) -> bool:
        """
        Realiza homing de eixo único.

        Args:
            axis: Eixo para homing ('X', 'Y', ou 'Z')

        Returns:
            True se homing bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def unlock(self) -> None:
        """
        Desbloqueia eixos após erro ou parada de emergência.
        """
        pass
