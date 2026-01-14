"""
GerberController - Controller Layer para Gerber Viewer.

Este módulo implementa o Controller do padrão MVC, responsável por:
- Orquestrar fluxos de importação/exportação
- Coordenar interações entre Model e View
- Gerenciar seleção de objetos
- Executar operações de edição (escala, translação, exclusão)
- Validar estados antes de operações

Seguindo princípios SOLID:
- SRP: Apenas coordenação (sem lógica de negócio específica)
- DIP: Depende de abstração (GerberModel), não de PyQt6
- OCP: Fácil estender com novas operações
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
import logging

from aoi_lib.gerber_core.models.gerber_model import (
    GerberModel,
    GerberObject,
    GerberLayer,
    ValidationError,
)

logger = logging.getLogger(__name__)


# ============================================================================
#  EXCEPTIONS
# ============================================================================

class ControllerError(Exception):
    """Exceção levantada quando operação do controller falha."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


# ============================================================================
#  CONTROLLER CLASS
# ============================================================================

class GerberController:
    """
    Controller principal para coordenar Model e View.

    Responsabilidades:
    - Orquestrar importação/exportação de arquivos Gerber
    - Gerenciar seleção de objetos
    - Executar operações de edição (escala, translação, exclusão)
    - Validar estados antes de operações
    - Coordenar comunicação Model ↔ View

    NOTA: Esta classe NÃO depende de PyQt6, sendo totalmente testável.
    """

    def __init__(self, model: GerberModel):
        """
        Inicializa controller com model.

        Args:
            model: Instância de GerberModel
        """
        self.model = model
        self.selected_object_indices: List[int] = []
        self.current_layer_name: Optional[str] = None

    # ========================================================================
    #  IMPORT/EXPORT
    # ========================================================================

    def import_gerber(
        self,
        lines: List[str],
        cfg: Any
    ) -> None:
        """
        Importa dados do arquivo Gerber para o model.

        Args:
            lines: Linhas do arquivo Gerber
            cfg: Configuração gerada pelo parser (GerberConfig)

        Raises:
            ValidationError: Se dados forem inválidos (propagada do model)
        """
        logger.info(f"Importando {len(lines)} linhas de arquivo Gerber")
        self.model.load_gerber(lines, cfg)

    def export_gerber(self) -> List[str]:
        """
        Exporta dados do model para formato Gerber.

        Returns:
            Lista de linhas em formato Gerber

        Raises:
            ControllerError: Se não houver dados para exportar
        """
        if self.model.gerber_lines is None:
            raise ControllerError("Nenhum arquivo Gerber carregado para exportar")

        logger.info("Exportando dados para formato Gerber")
        return self.model.gerber_lines

    # ========================================================================
    #  SELECTION
    # ========================================================================

    def select_object(
        self,
        index: int,
        layer_name: str
    ) -> None:
        """
        Seleciona um único objeto.

        Args:
            index: Índice do objeto na camada
            layer_name: Nome da camada
        """
        self.selected_object_indices = [index]
        self.current_layer_name = layer_name
        logger.debug(f"Objeto {index} selecionado na camada '{layer_name}'")

    def select_objects(
        self,
        indices: List[int],
        layer_name: str
    ) -> None:
        """
        Seleciona múltiplos objetos.

        Args:
            indices: Lista de índices dos objetos
            layer_name: Nome da camada
        """
        self.selected_object_indices = indices
        self.current_layer_name = layer_name
        logger.debug(f"{len(indices)} objetos selecionados na camada '{layer_name}'")

    def clear_selection(self) -> None:
        """Limpa seleção de objetos."""
        self.selected_object_indices = []
        self.current_layer_name = None
        logger.debug("Seleção limpa")

    # ========================================================================
    #  EDITING
    # ========================================================================

    def edit_selected_object(self, changes: Dict[str, Any]) -> None:
        """
        Edita o objeto selecionado com mudanças específicas.

        Args:
            changes: Dicionário com atributos a modificar
                    (ex: {"diameter": 10.0} ou {"width": 5.0, "height": 3.0})

        Raises:
            ControllerError: Se não houver seleção ou camada inválida
        """
        self._validate_selection()

        layer = self._get_current_layer()
        index = self.selected_object_indices[0]
        obj = layer.objects[index]

        # Aplicar mudanças
        for key, value in changes.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
            else:
                logger.warning(f"Atributo '{key}' não existe em {obj.obj_type}")

        logger.info(f"Objeto {index} editado: {changes}")

    def edit_selected_objects(
        self,
        scale_factor: float = 1.0,
        dx: float = 0.0,
        dy: float = 0.0
    ) -> None:
        """
        Edita múltiplos objetos selecionados com transformações.

        Args:
            scale_factor: Fator de escala (1.0 = sem mudança)
            dx: Translação em X (mm)
            dy: Translação em Y (mm)

        Raises:
            ControllerError: Se não houver seleção
        """
        self._validate_selection()

        layer = self._get_current_layer()

        # Transformar cada objeto selecionado
        for index in self.selected_object_indices:
            obj = layer.objects[index]
            transformed = self.model.transform_object(
                obj,
                scale_factor=scale_factor,
                dx=dx,
                dy=dy
            )

            # Substituir objeto pelo transformado
            layer.objects[index] = transformed

        logger.info(
            f"{len(self.selected_object_indices)} objetos transformados: "
            f"scale={scale_factor}, dx={dx}, dy={dy}"
        )

    def delete_selected_objects(self) -> None:
        """
        Exclui os objetos selecionados.

        Raises:
            ControllerError: Se não houver seleção
        """
        self._validate_selection()

        layer = self._get_current_layer()

        # Remover em ordem reversa para não invalidar índices
        for index in sorted(self.selected_object_indices, reverse=True):
            layer.remove_object(index)

        count = len(self.selected_object_indices)
        logger.info(f"{count} objetos excluídos")

        # Limpar seleção após exclusão
        self.clear_selection()

    # ========================================================================
    #  QUERIES
    # ========================================================================

    def get_selected_objects(self) -> List[GerberObject]:
        """
        Retorna lista de objetos selecionados.

        Returns:
            Lista de objetos GerberObject

        Raises:
            ControllerError: Se não houver seleção ou camada inválida
        """
        self._validate_selection()

        layer = self._get_current_layer()
        selected = [
            layer.objects[i]
            for i in self.selected_object_indices
        ]

        return selected

    def get_object_count(self) -> int:
        """
        Retorna o total de objetos no modelo.

        Returns:
            Número total de objetos
        """
        return self.model.get_object_count()

    # ========================================================================
    #  PRIVATE HELPERS
    # ========================================================================

    def _validate_selection(self) -> None:
        """
        Valida se há objetos selecionados.

        Raises:
            ControllerError: Se não houver seleção
        """
        if not self.selected_object_indices:
            raise ControllerError("Nenhum objeto selecionado")

        if self.current_layer_name is None:
            raise ControllerError("Nenhuma camada selecionada")

    def _get_current_layer(self) -> GerberLayer:
        """
        Retorna a camada atualmente selecionada.

        Returns:
            Instância de GerberLayer

        Raises:
            ControllerError: Se camada não existir
        """
        if self.current_layer_name is None:
            raise ControllerError("Nenhuma camada selecionada")

        # Buscar camada por nome
        for layer in self.model.layers:
            if layer.layer_name == self.current_layer_name:
                return layer

        raise ControllerError(
            f"Camada '{self.current_layer_name}' não encontrada"
        )
