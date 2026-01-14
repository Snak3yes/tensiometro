"""
RecipeManagerController - Controller para Gerenciamento de Receitas

Este controller gerencia operações relacionadas a receitas (recipes):
- Gerenciar receitas de diferentes stencils
- Aplicar configurações de receitas a captura e tensão
- Carregar e criar receitas
- Atualizar UI com configurações aplicadas

Responsabilidade:
- Gerenciar toda lógica de aplicação de receitas
- Validar pré-condições (ex: receita carregada)
- Emitir signals quando eventos ocorrem

Signals Emitidos:
- recipe_loaded(recipe) - Receita carregada
- recipe_created(recipe_name) - Receita criada
- recipe_applied_to_capture(settings) - Configurações de captura aplicadas
- recipe_applied_to_tension(settings) - Configurações de tensão aplicadas
- recipe_error(error) - Erro em operação de receita
"""

import logging
from typing import Optional, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger("consumo_lib")


class RecipeManagerController(QObject):
    """
    Controller para gerenciamento de receitas.

    Responsável por gerenciar carregamento, criação e aplicação
    de configurações de receitas em diferentes contextos.
    """

    # Signals
    recipe_loaded = pyqtSignal(object)  # Recipe
    recipe_created = pyqtSignal(str)  # recipe_name
    recipe_applied_to_capture = pyqtSignal(dict)  # settings
    recipe_applied_to_tension = pyqtSignal(dict)  # settings
    recipe_error = pyqtSignal(str)  # error_message

    def __init__(self, recipe_manager, recipe_manager_wrapper, parent=None):
        """
        Inicializa o RecipeManagerController.

        Args:
            recipe_manager: Instância de RecipeManager
            recipe_manager_wrapper: Instância de RecipeManagerWrapper
            parent: Widget pai (geralmente main_window)
        """
        super().__init__(parent)
        self.recipe_manager = recipe_manager
        self.recipe_manager_wrapper = recipe_manager_wrapper
        self.parent_window = parent

        logger.debug("RecipeManagerController inicializado")

    def show_recipe_manager(self):
        """
        Abre o diálogo de gerenciamento de receitas.

        Emits:
            Nenhum signal específico
        """
        self.recipe_manager_wrapper.show_manager(self.parent_window)

    def show_new_recipe_dialog(self):
        """
        Abre o diálogo para criar uma nova receita.

        Emits:
            recipe_created se criada
        """
        success = self.recipe_manager_wrapper.create_new(self.parent_window)
        if success:
            QMessageBox.information(
                self.parent_window,
                "Sucesso",
                "Receita criada com sucesso!\n\n"
                "Acesse Receitas > Gerenciar Receitas para carregar."
            )
            self.recipe_created.emit("Nova Receita")  # Nome genérico, wrapper já trata

    def load_recipe(self, recipe_name: str):
        """
        Carrega uma receita pelo nome.

        Args:
            recipe_name: Nome da receita

        Emits:
            recipe_loaded se carregada
            recipe_error se erro
        """
        try:
            self.recipe_manager_wrapper.load_recipe(recipe_name)
            # O resto é tratado pelo signal do wrapper conectado ao _on_recipe_loaded
        except Exception as e:
            error_msg = f"Erro ao carregar receita '{recipe_name}': {e}"
            logger.error(error_msg)
            self.recipe_error.emit(error_msg)

    def apply_recipe_to_capture(self, current_recipe, map_widgets: Optional[Dict] = None):
        """
        Aplica as configurações de captura da receita atual.

        Args:
            current_recipe: Receita atual (ou None)
            map_widgets: Dict opcional com widgets de mapa {
                'map_step_x_edit', 'map_step_y_edit', 'spin_capture_delay'
            }

        Emits:
            recipe_applied_to_capture se aplicada
            recipe_error se sem receita
        """
        settings = self.recipe_manager_wrapper.apply_to_capture()
        if settings is None:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "Nenhuma receita carregada.\n\n"
                "Acesse Receitas > Gerenciar Receitas e carregue uma receita."
            )
            self.recipe_error.emit("Nenhuma receita carregada")
            return

        # Atualiza widgets de mapa se fornecidos
        if map_widgets:
            self._update_map_widgets(settings, map_widgets)

        # Emit signal
        self.recipe_applied_to_capture.emit(settings)

    def apply_recipe_to_tension(self, current_recipe):
        """
        Aplica as configurações de tensão da receita atual.

        Args:
            current_recipe: Receita atual (ou None)

        Emits:
            recipe_applied_to_tension se aplicada
            recipe_error se sem receita
        """
        settings = self.recipe_manager_wrapper.apply_to_tension()
        if settings is None:
            QMessageBox.warning(
                self.parent_window,
                "Aviso",
                "Nenhuma receita carregada.\n\n"
                "Acesse Receitas > Gerenciar Receitas e carregue uma receita."
            )
            self.recipe_error.emit("Nenhuma receita carregada")
            return

        # Emit signal
        self.recipe_applied_to_tension.emit(settings)

    def _update_map_widgets(self, settings: dict, widgets: Dict[str, Any]):
        """
        Atualiza widgets de mapa com configurações da receita.

        Args:
            settings: Configurações da receita
            widgets: Dict com widgets a atualizar
        """
        # Atualiza widgets de mapa se existirem
        if 'map_step_x_edit' in widgets and widgets['map_step_x_edit']:
            widgets['map_step_x_edit'].setText(str(settings['step_x']))
        if 'map_step_y_edit' in widgets and widgets['map_step_y_edit']:
            widgets['map_step_y_edit'].setText(str(settings['step_y']))
        if 'spin_capture_delay' in widgets and widgets['spin_capture_delay']:
            widgets['spin_capture_delay'].setValue(settings['capture_delay_ms'])

    def on_recipe_loaded(self, recipe, current_recipe_action=None):
        """
        Handler chamado quando uma receita é carregada.

        Args:
            recipe: Recipe carregada
            current_recipe_action: QAction opcional para atualizar

        Emits:
            recipe_loaded
        """
        # Atualiza menu se fornecido
        if current_recipe_action is not None:
            current_recipe_action.setText(f"📋 {recipe.name}")
            current_recipe_action.setEnabled(True)

        # Mostra na barra de status
        self.parent_window.statusBar().showMessage(f"Receita carregada: {recipe.name}")
        logger.info(f"Receita carregada: {recipe.name} ({recipe.recipe_id})")

        # Emit signal
        self.recipe_loaded.emit(recipe)

    def on_recipe_applied_to_capture(self, settings: dict, current_recipe, map_origin_ref=None, map_end_ref=None):
        """
        Handler chamado quando configurações de captura são aplicadas.

        Args:
            settings: Configurações aplicadas
            current_recipe: Receita atual
            map_origin_ref: Referência mutable para map_origin (opcional)
            map_end_ref: Referência mutable para map_end (opcional)

        Emits:
            Nenhum signal adicional (já emitido em apply_recipe_to_capture)
        """
        # Atualiza referências de mapa se fornecidas
        if map_origin_ref is not None:
            map_origin_ref[0] = settings['origin']
        if map_end_ref is not None:
            map_end_ref[0] = settings['end']

        # Mostra confirmação
        QMessageBox.information(
            self.parent_window,
            "Receita Aplicada",
            f"Configurações de captura aplicadas:\n\n"
            f"• Origem: ({settings['origin']['x']}, {settings['origin']['y']})\n"
            f"• Final: ({settings['end']['x']}, {settings['end']['y']})\n"
            f"• Step X: {settings['step_x']} mm\n"
            f"• Step Y: {settings['step_y']} mm\n"
            f"• Delay: {settings['capture_delay_ms']} ms\n"
            f"• Backlight: {'Sim' if settings['backlight_enabled'] else 'Não'}\n\n"
            "Abra 'Definir Mapa' para verificar ou ajustar."
        )

        logger.info(f"Configurações de captura aplicadas da receita '{current_recipe.name}'")

    def on_recipe_applied_to_tension(self, settings: dict, current_recipe):
        """
        Handler chamado quando configurações de tensão são aplicadas.

        Args:
            settings: Configurações aplicadas
            current_recipe: Receita atual

        Emits:
            Nenhum signal adicional (já emitido em apply_recipe_to_tension)
        """
        # Mostra informações dos critérios de aceitação
        acc = settings['acceptance']
        QMessageBox.information(
            self.parent_window,
            "Receita de Tensão",
            f"Configurações de tensão da receita '{current_recipe.name}':\n\n"
            f"📐 Grid: {settings['grid_rows']} x {settings['grid_cols']}\n"
            f"📍 Área: ({settings['start_point']['x']}, {settings['start_point']['y']}) → "
            f"({settings['end_point']['x']}, {settings['end_point']['y']})\n\n"
            f"📊 Critérios de Aceitação:\n"
            f"  • Mínimo: {acc['min_tension']} N/cm²\n"
            f"  • Máximo: {acc['max_tension']} N/cm²\n"
            f"  • Warning baixo: {acc['warning_low']} N/cm²\n"
            f"  • Warning alto: {acc['warning_high']} N/cm²\n\n"
            "ℹ️ Estes critérios serão usados para classificar as medições."
        )

        logger.info(f"Configurações de tensão aplicadas da receita '{current_recipe.name}'")

    def create_recipe_from_program(self, program):
        """
        Cria uma Recipe a partir de um ProgramConfig do Engineering Wizard.

        Este método permite que programas criados no Engineering Wizard
        sejam convertidos em Recipes para uso no sistema de inspeção.

        Args:
            program: ProgramConfig do Engineering Wizard

        Returns:
            Recipe se criada com sucesso, None se falhou

        Emits:
            recipe_created se bem-sucedido
            recipe_error se falhar
        """
        from consumo_lib.coordinators.engineering_recipe_coordinator import EngineeringRecipeCoordinator

        logger.info(f"Criando Recipe a partir de ProgramConfig: {program.program_name}")

        try:
            # Cria coordenador de conversão
            coordinator = EngineeringRecipeCoordinator()

            # Valida se pode converter
            can_convert, error_msg = coordinator.can_convert_to_recipe(program)
            if not can_convert:
                logger.error(f"Não foi possível converter ProgramConfig para Recipe: {error_msg}")
                self.recipe_error.emit(f"Erro na conversão: {error_msg}")
                return None

            # Converte ProgramConfig → Recipe
            recipe = coordinator.program_to_recipe(program)

            # Salva Recipe usando RecipeManager
            success = self.recipe_manager.save_recipe(recipe)

            if success:
                logger.info(f"✅ Recipe criada e salva: {recipe.name} ({recipe.recipe_id})")
                self.recipe_created.emit(recipe.name)
                return recipe
            else:
                logger.error("Erro ao salvar Recipe no RecipeManager")
                self.recipe_error.emit("Erro ao salvar Recipe")
                return None

        except Exception as e:
            error_msg = f"Erro ao criar Recipe do programa: {e}"
            logger.exception(error_msg)
            self.recipe_error.emit(error_msg)
            return None
