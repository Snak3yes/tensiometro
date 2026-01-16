"""
Interface PLC Jog Movement - Contrato para movimento Jog

Define contrato para movimento Jog (contínuo) do PLC.
"""

from abc import ABC, abstractmethod


class PLCJogMovement(ABC):
    """
    Interface para movimento Jog do PLC.

    Responsabilidades:
    - Iniciar movimento Jog contínuo
    - Parar movimento Jog
    - Verificar status do Jog
    """

    @abstractmethod
    def jog_start(self, axis: str, speed: float) -> None:
        """
        Inicia movimento Jog no eixo especificado.

        Args:
            axis: Eixo para jog ('X', 'Y', ou 'Z')
            speed: Velocidade em pulsos/minuto
        """
        pass

    @abstractmethod
    def jog_stop(self, axis: str) -> None:
        """
        Para movimento Jog no eixo especificado.

        Args:
            axis: Eixo a ser parado ('X', 'Y', ou 'Z')
        """
        pass

    @abstractmethod
    def is_jogging(self, axis: str) -> bool:
        """
        Verifica se eixo está em movimento Jog.

        Args:
            axis: Eixo a ser verificado ('X', 'Y', ou 'Z')

        Returns:
            True se jog ativo, False caso contrário
        """
        pass
