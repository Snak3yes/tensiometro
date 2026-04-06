"""
managers/recipe_manager.py
----------------------------
Gerencia receitas (RecipeManager) e aplica configurações à UI.
"""
import logging
from PyQt6.QtCore import QObject, pyqtSignal
from aoi_lib.recipe_manager import RecipeManager

logger = logging.getLogger(__name__)


class RecipeManagerWrapper(QObject):
    """
    Gerencia receitas e sua aplicação na aplicação.

    Responsabilidades:
        - Gerenciar RecipeManager
        - Carregar/aplicar receitas
        - Criar novas receitas
        - Aplicar configurações de captura e tensão
        - Emitir signals de eventos
    """

    # Signals
    recipe_loaded = pyqtSignal(object)  # Recipe
    recipe_created = pyqtSignal(str)    # recipe_name
    recipe_applied_to_capture = pyqtSignal(dict)  # capture_settings
    recipe_applied_to_tension = pyqtSignal(dict)  # tension_settings
    recipe_error = pyqtSignal(str)       # error_message

    def __init__(self, parent=None):
        super().__init__(parent)
        config_manager = getattr(parent, "config_manager", None) or getattr(parent, "config", None)
        self.recipe_manager = RecipeManager(config_manager=config_manager)
        self.current_recipe = None

        logger.info(f"RecipeManager inicializado. Diretório: {self.recipe_manager.recipes_dir}")

    def show_manager(self, parent_widget):
        """
        Abre o diálogo de gerenciamento de receitas.

        Args:
            parent_widget: Widget pai para o diálogo
        """
        from consumo_lib.dialogs import RecipeManagerDialog

        dialog = RecipeManagerDialog(self.recipe_manager, parent_widget)
        # Conectar signal recipe_loaded do diálogo ao nosso método
        dialog.recipe_loaded.connect(self._on_dialog_recipe_loaded)
        dialog.exec()

    def create_new(self, parent_widget):
        """
        Abre o diálogo para criar uma nova receita.

        Args:
            parent_widget: Widget pai para o diálogo

        Returns:
            bool: True se criou com sucesso, False caso contrário
        """
        from consumo_lib.dialogs import RecipeEditorDialog
        from PyQt6.QtWidgets import QDialog

        dialog = RecipeEditorDialog(parent=parent_widget)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            recipe = dialog.recipe
            if self.recipe_manager.save_recipe(recipe):
                logger.info(f"Receita '{recipe.name}' criada com sucesso")
                self.recipe_created.emit(recipe.name)
                return True
            else:
                error_msg = f"Falha ao salvar receita '{recipe.name}'"
                logger.error(error_msg)
                self.recipe_error.emit(error_msg)
                return False
        return False

    def load_recipe(self, recipe_name: str):
        """
        Carrega uma receita por nome.

        Args:
            recipe_name: Nome da receita para carregar

        Returns:
            Recipe ou None se não encontrar
        """
        recipe = self.recipe_manager.load_recipe(recipe_name)
        if recipe:
            self._set_current_recipe(recipe)
            logger.info(f"Receita '{recipe_name}' carregada")
            return recipe
        else:
            logger.warning(f"Receita '{recipe_name}' não encontrada")
            self.recipe_error.emit(f"Receita '{recipe_name}' não encontrada")
            return None

    def apply_to_capture(self, map_settings: dict):
        """
        Aplica configurações de captura da receita atual.

        Args:
            map_settings: Dicionário com configurações atuais do mapa
                         (para atualização)

        Returns:
            dict: Configurações atualizadas ou None se falhar
        """
        if self.current_recipe is None:
            error_msg = "Nenhuma receita carregada"
            logger.warning(error_msg)
            self.recipe_error.emit(error_msg)
            return None

        r = self.current_recipe

        # Prepara configurações de captura da receita
        capture_settings = {
            'origin': {'x': r.capture.origin.x, 'y': r.capture.origin.y},
            'end': {'x': r.capture.end.x, 'y': r.capture.end.y},
            'step_x': r.capture.step_x,
            'step_y': r.capture.step_y,
            'capture_delay_ms': r.capture.capture_delay_ms,
            'backlight_enabled': r.capture.backlight_enabled
        }

        logger.info(f"Configurações de captura da receita '{r.name}' aplicadas")
        self.recipe_applied_to_capture.emit(capture_settings)
        return capture_settings

    def apply_to_tension(self):
        """
        Aplica configurações de tensão da receita atual.

        Returns:
            dict: Configurações de tensão ou None se falhar
        """
        if self.current_recipe is None:
            error_msg = "Nenhuma receita carregada"
            logger.warning(error_msg)
            self.recipe_error.emit(error_msg)
            return None

        r = self.current_recipe
        acceptance = self.recipe_manager.get_global_tension_acceptance()
        r.tension.acceptance = acceptance

        if not r.tension.enabled:
            error_msg = "Medição de tensão desabilitada nesta receita"
            logger.info(error_msg)
            self.recipe_error.emit(error_msg)
            return None

        # Prepara configurações de tensão da receita
        tension_settings = {
            'grid_rows': r.tension.grid_rows,
            'grid_cols': r.tension.grid_cols,
            'measurement_pattern_name': r.tension.measurement_pattern_name,
            'start_point': {
                'x': r.tension.start_point.x,
                'y': r.tension.start_point.y
            },
            'end_point': {
                'x': r.tension.end_point.x,
                'y': r.tension.end_point.y
            },
            'movement_height': r.tension.movement_height,
            'measurement_height': r.tension.measurement_height,
            'stabilization_time_ms': r.tension.stabilization_time_ms,
            'feed_rate': r.tension.feed_rate,
            'acceptance': {
                'min_tension': acceptance.min_tension,
                'max_tension': acceptance.max_tension,
                'warning_low': acceptance.warning_low,
                'warning_high': acceptance.warning_high
            }
        }

        logger.info(f"Configurações de tensão da receita '{r.name}' aplicadas")
        self.recipe_applied_to_tension.emit(tension_settings)
        return tension_settings

    def get_current_recipe(self):
        """
        Retorna a receita atualmente carregada.

        Returns:
            Recipe ou None
        """
        return self.current_recipe

    def is_loaded(self) -> bool:
        """
        Verifica se há uma receita carregada.

        Returns:
            bool: True se há receita carregada
        """
        return self.current_recipe is not None

    def _set_current_recipe(self, recipe):
        """
        Define a receita atual e emite signal.

        Args:
            recipe: Recipe para definir como atual
        """
        self.current_recipe = recipe
        self.recipe_manager.set_current_recipe(recipe)
        self.recipe_loaded.emit(recipe)

    def _on_dialog_recipe_loaded(self, recipe):
        """
        Handler interno para quando diálogo carrega receita.

        Este método conecta o signal do diálogo ao nosso método de
        definição de receita atual.

        Args:
            recipe: Recipe carregada
        """
        self._set_current_recipe(recipe)

    # =========================================================================
    #  COMPATIBILIDADE COM FLUXO DE ENGENHARIA DESCONTINUADO
    # =========================================================================

    def create_recipe_from_program(self, program):
        """
        Integração com ProgramConfig descontinuada.

        Args:
            program: Objeto legado do fluxo de engenharia (ignorado)

        Returns:
            Recipe criada ou None se falhar

        Raises:
            ValueError: Se conversão falhar
        """
        error_msg = (
            "A criação de receita a partir do Engineering Wizard "
            "não está disponível nesta versão."
        )
        logger.warning(error_msg)
        self.recipe_error.emit(error_msg)
        return None

    def load_from_engineering_program(self, program_name: str):
        """
        Integração com programas de engenharia descontinuada.

        Args:
            program_name: Nome do programa (com ou sem .json)

        Returns:
            Recipe carregada ou None se falhar
        """
        error_msg = (
            "O carregamento de programas do Engineering Wizard "
            "não está disponível nesta versão."
        )
        logger.warning("%s: %s", error_msg, program_name)
        self.recipe_error.emit(error_msg)
        return None

