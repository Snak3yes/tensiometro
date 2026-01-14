"""
EditCommands - Command Pattern para edição de objetos Gerber.

Este módulo implementa o padrão Command para operações de edição em objetos
Gerber, permitindo:

- Encapsular operações de edição como objetos
- Desfazer operações (undo/redo)
- Adicionar novos tipos de comandos sem modificar código existente (OCP)
- Reduzir complexidade ciclomática de métodos de edição

Seguindo princípios SOLID:
- SRP: Cada comando é responsável por um único tipo de objeto
- OCP: Fácil adicionar novos comandos sem modificar existentes
- DIP: Comandos dependem de abstração (GerberObject), não de PyQt6
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any
import copy
import logging

from aoi_lib.gerber_core.models.gerber_model import GerberObject

logger = logging.getLogger(__name__)


# ============================================================================
#  EXCEPTIONS
# ============================================================================

class CommandExecutionError(Exception):
    """Exceção levantada quando execução de comando falha."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


# ============================================================================
#  COMMAND ABSTRACTION
# ============================================================================

class EditObjectCommand(ABC):
    """
    Abstração base para comandos de edição de objetos Gerber.

    Responsabilidades:
    - Encapsular operação de edição
    - Armazenar estado original para undo
    - Executar edição de forma atômica
    - Desfazer edição (undo)

    NOTA: Cada comando concreto lida com um tipo específico de objeto.
    """

    def __init__(self, object: GerberObject, changes: Dict[str, Any]):
        """
        Inicializa comando com objeto e mudanças.

        Args:
            object: Objeto Gerber a ser editado
            changes: Dicionário de atributos a modificar
        """
        self.original = object
        self.changes = changes
        self._original_state = self._capture_state(object)

    def execute(self) -> GerberObject:
        """
        Executa a edição do objeto (Template Method).

        Este método implementa a lógica comum de edição, delegando
        apenas o nome do tipo de objeto para as subclasses.

        Returns:
            Novo objeto Gerber com modificações aplicadas
        """
        # Criar cópia para não modificar original
        modified = copy.copy(self.original)

        # Aplicar mudanças
        obj_type_name = self._get_object_type_name()
        for key, value in self.changes.items():
            if hasattr(modified, key):
                setattr(modified, key, value)
                logger.debug(f"{obj_type_name}: {key} = {value}")
            else:
                logger.warning(
                    f"Atributo '{key}' não existe em {obj_type_name}. "
                    f"Ignorando."
                )

        return modified

    @abstractmethod
    def _get_object_type_name(self) -> str:
        """
        Retorna o nome do tipo de objeto para logs.

        Returns:
            Nome do tipo de objeto (ex: "flash_circle", "flash_rect")
        """
        pass

    @abstractmethod
    def undo(self, modified: GerberObject) -> GerberObject:
        """
        Desfaz a edição, retornando ao estado original.

        Args:
            modified: Objeto modificado após execute()

        Returns:
            Objeto restaurado ao estado original
        """
        pass

    def _capture_state(self, obj: GerberObject) -> Dict[str, Any]:
        """
        Captura estado atual do objeto para posterior restauração.

        Args:
            obj: Objeto cujo estado será capturado

        Returns:
            Dicionário com estado copiado
        """
        return {
            "obj_type": obj.obj_type,
            "x": obj.x,
            "y": obj.y,
            "diameter": obj.diameter,
            "width": obj.width,
            "height": obj.height,
        }

    def _restore_state(self, obj: GerberObject, state: Dict[str, Any]) -> GerberObject:
        """
        Restaura estado em um objeto.

        Args:
            obj: Objeto a ser restaurado
            state: Estado anterior a ser aplicado

        Returns:
            Objeto com estado restaurado
        """
        obj.x = state["x"]
        obj.y = state["y"]
        obj.diameter = state.get("diameter")
        obj.width = state.get("width")
        obj.height = state.get("height")
        return obj


# ============================================================================
#  CONCRETE COMMANDS
# ============================================================================

class EditCircleCommand(EditObjectCommand):
    """
    Comando para editar objetos circulares (flash_circle).

    Atributos editáveis:
    - x: Posição X em mm
    - y: Posição Y em mm
    - diameter: Diâmetro em mm
    """

    def _get_object_type_name(self) -> str:
        """Retorna nome do tipo de objeto para logs."""
        return "flash_circle"

    def undo(self, modified: GerberObject) -> GerberObject:
        """
        Restaura objeto circular ao estado original.

        Args:
            modified: Objeto modificado

        Returns:
            Objeto restaurado
        """
        return self._restore_state(modified, self._original_state)


class EditRectangleCommand(EditObjectCommand):
    """
    Comando para editar objetos retangulares (flash_rect).

    Atributos editáveis:
    - x: Posição X em mm
    - y: Posição Y em mm
    - width: Largura em mm
    - height: Altura em mm
    """

    def _get_object_type_name(self) -> str:
        """Retorna nome do tipo de objeto para logs."""
        return "flash_rect"

    def undo(self, modified: GerberObject) -> GerberObject:
        """
        Restaura objeto retangular ao estado original.

        Args:
            modified: Objeto modificado

        Returns:
            Objeto restaurado
        """
        return self._restore_state(modified, self._original_state)


class EditObroundCommand(EditObjectCommand):
    """
    Comando para editar objetos obround (flash_oval).

    Obround = forma de pista de corrida (retângulo com semicírculos nas pontas).

    Atributos editáveis:
    - x: Posição X em mm
    - y: Posição Y em mm
    - width: Largura total em mm
    - height: Altura total em mm
    """

    def _get_object_type_name(self) -> str:
        """Retorna nome do tipo de objeto para logs."""
        return "flash_oval"

    def undo(self, modified: GerberObject) -> GerberObject:
        """
        Restaura objeto obround ao estado original.

        Args:
            modified: Objeto modificado

        Returns:
            Objeto restaurado
        """
        return self._restore_state(modified, self._original_state)


class EditRegionCommand(EditObjectCommand):
    """
    Comando para editar regiões (region).

    Regiões são áreas complexas formadas por múltiplos segmentos.

    Atributos editáveis:
    - x: Posição X em mm
    - y: Posição Y em mm
    """

    def _get_object_type_name(self) -> str:
        """Retorna nome do tipo de objeto para logs."""
        return "region"

    def undo(self, modified: GerberObject) -> GerberObject:
        """
        Restaura região ao estado original.

        Args:
            modified: Objeto modificado

        Returns:
            Objeto restaurado
        """
        return self._restore_state(modified, self._original_state)
