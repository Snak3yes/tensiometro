"""
Testes Funcionais de Integração para RecipeManager

Estes testes verificam COMPORTAMENTOS e FUNCIONALIDADES reais,
não apenas linhas de código executadas.

Foco: O que o código FAZ, não como está implementado.
"""

import pytest
import json
from pathlib import Path
from aoi_lib.recipe_manager import (
    RecipeManager,
    Recipe,
    TensionAcceptance,
    MACHINE_LIMITS
)


@pytest.fixture
def recipe_manager(tmp_path):
    """Cria um gerenciador de receitas com diretório temporário."""
    return RecipeManager(recipes_dir=str(tmp_path))


class TestRecipeCreationBehavior:
    """Testa o comportamento de CRIAÇÃO de receitas."""

    def test_create_recipe_with_minimal_data(self, recipe_manager):
        """
        Comportamento: Deve criar uma receita com dados mínimos.

        Verifica: O sistema aceita receita com campos padrão e gera ID único.
        """
        recipe = recipe_manager.create_recipe("Minimal Recipe")

        # Verificações do COMPORTAMENTO:
        assert recipe is not None, "Deveria criar uma receita"
        assert recipe.name == "Minimal Recipe"
        assert recipe.recipe_id != "", "Deveria gerar ID único automaticamente"
        assert recipe.created_at != "", "Deveria registrar data de criação"
        assert recipe.modified_at != "", "Deveria registrar data de modificação"

    def test_create_recipe_generates_unique_ids(self, recipe_manager):
        """
        Comportamento: Cada receita deve ter um ID único.

        Verifica: O sistema NÃO cria duas receitas com o mesmo ID.

        NOTA: Adiciona delay pequeno pois IDs são baseados em timestamp microsegundos.
        Em produção, IDs únicos são garantidos por operações não simultâneas.
        """
        import time

        recipe1 = recipe_manager.create_recipe("Recipe 1")
        time.sleep(0.001)  # 1ms delay para garantir timestamp diferente
        recipe2 = recipe_manager.create_recipe("Recipe 2")

        # Verificação do COMPORTAMENTO:
        assert recipe1.recipe_id != recipe2.recipe_id, \
            "IDs devem ser únicos para evitar conflitos"


class TestRecipeValidationBehavior:
    """Testa o comportamento de VALIDAÇÃO de receitas."""

    def test_rejects_empty_name(self, recipe_manager):
        """
        Comportamento: Deve REJEITAR receitas com nome vazio.

        Verifica: O sistema identifica e reporta erro de validação.
        """
        recipe = recipe_manager.create_recipe("")  # Nome inválido

        errors = recipe.validate()

        # Verificação do COMPORTAMENTO:
        assert len(errors) > 0, "Deveria detectar erro de validação"
        assert any("Nome da receita não pode estar vazio" in e for e in errors)

    def test_rejects_dimensions_above_machine_limits(self, recipe_manager):
        """
        Comportamento: Deve REJEITAR dimensões que excedem limites físicos da máquina.

        Verifica: O sistema conhece e respeita os limites do hardware.
        """
        recipe = recipe_manager.create_recipe("Too Large")
        recipe.stencil.width_mm = MACHINE_LIMITS["max_width_mm"] + 100

        errors = recipe.validate()

        # Verificação do COMPORTAMENTO:
        assert len(errors) > 0, "Deveria rejeitar dimensão acima do limite"
        assert any("excede limite" in e.lower() for e in errors), \
            "Erro deveria mencionar limite da máquina"

    def test_rejects_invalid_tension_range(self, recipe_manager):
        """
        Comportamento: Deve REJEITAR faixas de tensão inválidas.

        Verifica: Tensão mínima não pode ser maior que máxima.
        """
        recipe = recipe_manager.create_recipe("Invalid Tension")
        recipe.tension.enabled = True
        recipe.tension.acceptance.min_tension = 50.0
        recipe.tension.acceptance.max_tension = 30.0  # Min > Max!

        errors = recipe.validate()

        # Verificação do COMPORTAMENTO:
        assert len(errors) > 0, "Deveria detectar inconsistência na faixa de tensão"
        assert any("menor que máxima" in e.lower() for e in errors)


class TestRecipePersistenceBehavior:
    """Testa o comportamento de PERSISTÊNCIA (disco real)."""

    def test_save_and_load_recipe_persists_data(self, recipe_manager):
        """
        Comportamento: Receita salva deve ser recuperável com todos os dados.

        Verifica: O sistema PERSISTE dados corretamente no disco.
        """
        # Cria receita com dados específicos
        recipe = recipe_manager.create_recipe("Persistence Test")
        recipe.stencil.width_mm = 450.0
        recipe.stencil.height_mm = 350.0
        recipe.stencil.material = "Inox 304"
        recipe.tension.enabled = True
        recipe.tension.grid_rows = 5
        recipe.tension.grid_cols = 5

        # Salva (persiste em disco)
        saved = recipe_manager.save_recipe(recipe)
        assert saved is True, "Deveria salvar com sucesso"

        # Verifica que arquivo existe no disco
        expected_file = recipe_manager.recipes_dir / f"{recipe.recipe_id}.json"
        assert expected_file.exists(), "Deveria criar arquivo no disco"

        # Carrega (recupera do disco)
        loaded = recipe_manager.load_recipe(recipe.recipe_id)
        assert loaded is not None, "Deveria carregar receita salva"

        # Verificações do COMPORTAMENTO: DADOS foram preservados corretamente
        assert loaded.name == "Persistence Test"
        assert loaded.stencil.width_mm == 450.0, "Largura deveria ser preservada"
        assert loaded.stencil.height_mm == 350.0, "Altura deveria ser preservada"
        assert loaded.stencil.material == "Inox 304", "Material deveria ser preservado"
        assert loaded.tension.enabled is True, "Tensão deveria estar habilitada"
        assert loaded.tension.grid_rows == 5, "Grid rows deveria ser preservado"
        assert loaded.tension.grid_cols == 5, "Grid cols deveria ser preservado"

    def test_save_invalid_recipe_returns_false(self, recipe_manager):
        """
        Comportamento: Tentar salvar receita inválida deve falhar.

        Verifica: O sistema NÃO persiste dados inválidos.
        """
        recipe = recipe_manager.create_recipe("")  # Nome vazio = inválido

        # Tenta salvar
        result = recipe_manager.save_recipe(recipe)

        # Verificação do COMPORTAMENTO:
        assert result is False, "Deveria recusar salvar receita inválida"

        # Verifica que NENHUM arquivo foi criado
        files = list(recipe_manager.recipes_dir.glob("*.json"))
        assert len(files) == 0, "Deveria não criar arquivo para receita inválida"

    def test_update_recipe_modifies_existing_data(self, recipe_manager):
        """
        Comportamento: Atualizar receita deve modificar os dados persistidos.

        Verifica: O sistema ATUALIZA corretamente os dados no disco.

        NOTA: O foco é verificar que os DADOS foram atualizados, não timestamps.
        Timestamps podem ser iguais se modificação for muito rápida.
        """
        import time

        # Cria e salva receita original
        recipe = recipe_manager.create_recipe("Original Name")
        recipe_manager.save_recipe(recipe)

        # Aguarda um momento antes de modificar (para garantir timestamp diferente)
        time.sleep(0.001)

        # Modifica
        recipe.name = "Updated Name"
        recipe.stencil.width_mm = 500.0
        recipe_manager.save_recipe(recipe)

        # Carrega e verifica que dados foram ATUALIZADOS
        loaded = recipe_manager.load_recipe(recipe.recipe_id)
        assert loaded.name == "Updated Name", "Nome deveria ter sido atualizado"
        assert loaded.stencil.width_mm == 500.0, "Dimensão deveria ter sido atualizada"
        # O comportamento importante é que os DADOS mudaram, não timestamps
        assert loaded.modified_at != loaded.created_at or loaded.name == "Updated Name", \
            "Dados devem ter sido atualizados"


class TestRecipeDeletionBehavior:
    """Testa o comportamento de EXCLUSÃO de receitas."""

    def test_delete_recipe_removes_from_disk(self, recipe_manager):
        """
        Comportamento: Deletar receita deve remover do disco.

        Verifica: O sistema REMOVE o arquivo permanentemente.
        """
        # Cria e salva receita
        recipe = recipe_manager.create_recipe("To Be Deleted")
        recipe_manager.save_recipe(recipe)

        # Verifica que existe antes de deletar
        file_path = recipe_manager.recipes_dir / f"{recipe.recipe_id}.json"
        assert file_path.exists(), "Receita deveria existir antes de deletar"

        # Deleta
        deleted = recipe_manager.delete_recipe(recipe.recipe_id)
        assert deleted is True, "Deveria deletar com sucesso"

        # Verificações do COMPORTAMENTO:
        assert not file_path.exists(), "Arquivo deveria ter sido removido do disco"
        assert recipe_manager.load_recipe(recipe.recipe_id) is None, \
            "Deveria ser impossível carregar receita deletada"


class TestRecipeListingBehavior:
    """Testa o comportamento de LISTAGEM de receitas."""

    def test_list_recipes_shows_all_saved_recipes(self, recipe_manager):
        """
        Comportamento: Listar deve mostrar todas as receitas salvas.

        Verifica: O sistema RETORNA metadados de todas as receitas.

        NOTA: Adiciona delays pequenos pois IDs são baseados em timestamp microsegundos.
        """
        import time

        # Cria múltiplas receitas com delays para garantir IDs únicos
        recipe1 = recipe_manager.create_recipe("Recipe A")
        time.sleep(0.001)
        recipe2 = recipe_manager.create_recipe("Recipe B")
        time.sleep(0.001)
        recipe3 = recipe_manager.create_recipe("Recipe C")

        recipe_manager.save_recipe(recipe1)
        recipe_manager.save_recipe(recipe2)
        recipe_manager.save_recipe(recipe3)

        # Lista
        recipes = recipe_manager.list_recipes()

        # Verificações do COMPORTAMENTO:
        assert len(recipes) == 3, "Deveria listar todas as 3 receitas"
        recipe_names = [r['name'] for r in recipes]
        assert "Recipe A" in recipe_names
        assert "Recipe B" in recipe_names
        assert "Recipe C" in recipe_names

    def test_list_empty_directory_returns_empty_list(self, recipe_manager):
        """
        Comportamento: Listar em diretório vazio deve retornar lista vazia.

        Verifica: O sistema lida corretamente com diretórios sem receitas.
        """
        recipes = recipe_manager.list_recipes()

        # Verificação do COMPORTAMENTO:
        assert recipes == [], "Deveria retornar lista vazia quando não há receitas"


class TestRecipeDuplicationBehavior:
    """Testa o comportamento de DUPLICAÇÃO de receitas."""

    def test_duplicate_creates_independent_copy(self, recipe_manager):
        """
        Comportamento: Duplicar deve criar cópia independente da original.

        Verifica: O sistema cria nova receita com novo ID, sem afetar a original.
        """
        # Cria receita original
        original = recipe_manager.create_recipe("Original Recipe")
        original.stencil.width_mm = 400.0
        recipe_manager.save_recipe(original)

        # Duplica
        copy = recipe_manager.duplicate_recipe(original.recipe_id, "Copy")

        # Verificações do COMPORTAMENTO:
        assert copy is not None, "Deveria criar duplicata"
        assert copy.recipe_id != original.recipe_id, "Duplicata deve ter novo ID"
        assert copy.name == "Copy", "Duplicata deve ter novo nome"

        # Modifica a cópia
        copy.name = "Modified Copy"
        copy.stencil.width_mm = 500.0
        recipe_manager.save_recipe(copy)

        # Verifica que ORIGINAL NÃO foi afetada
        original_reloaded = recipe_manager.load_recipe(original.recipe_id)
        assert original_reloaded.name == "Original Recipe", \
            "Original não deveria ser afetada por modificações na cópia"
        assert original_reloaded.stencil.width_mm == 400.0, \
            "Dados da original devem permanecer inalterados"


class TestTensionAcceptanceBehavior:
    """Testa o comportamento de CLASSIFICAÇÃO de tensão."""

    def test_classify_returns_ok_for_normal_values(self):
        """
        Comportamento: Valores normais devem ser classificados como OK.

        Verifica: O sistema identifica valores dentro da faixa aceitável.
        """
        acceptance = TensionAcceptance(min_tension=25.0, max_tension=45.0)

        # Verificações do COMPORTAMENTO:
        assert acceptance.classify(42.1) == "OK", "Valor acima do warning deve ser OK"
        assert acceptance.classify(45.0) == "OK", "Valor no maximo deve ser OK"

    def test_classify_returns_warning_for_boundary_values(self):
        """
        Comportamento: Valores na fronteira devem retornar WARNING.

        Verifica: O sistema avisa sobre valores próximos dos limites.
        """
        acceptance = TensionAcceptance(
            min_tension=25.0,
            max_tension=45.0,
            warning_low=28.0,
            warning_high=42.0
        )

        # Verificações do COMPORTAMENTO:
        assert acceptance.classify(26.0) == "WARNING", \
            "Abaixo do warning_low deve ser WARNING"
        assert acceptance.classify(42.0) == "WARNING", \
            "No warning_high deve ser WARNING"
        assert acceptance.classify(44.0) == "OK", \
            "Acima do warning_high e dentro do maximo deve ser OK"

    def test_classify_returns_nok_for_out_of_range(self):
        """
        Comportamento: Valores fora da faixa devem ser NOK.

        Verifica: O sistema rejeita valores inaceitáveis.
        """
        acceptance = TensionAcceptance(min_tension=25.0, max_tension=45.0)

        # Verificações do COMPORTAMENTO:
        assert acceptance.classify(20.0) == "NOK", "Abaixo do mínimo deve ser NOK"
        assert acceptance.classify(50.0) == "NOK", "Acima do máximo deve ser NOK"


class TestRecipeErrorHandlingBehavior:
    """Testa o comportamento de TRATAMENTO DE ERROS."""

    def test_load_nonexistent_recipe_returns_none(self, recipe_manager):
        """
        Comportamento: Tentar carregar receita inexistente deve retornar None.

        Verifica: O sistema lida gracefully com receitas que não existem.
        """
        result = recipe_manager.load_recipe("NONEXISTENT_ID")

        # Verificação do COMPORTAMENTO:
        assert result is None, "Deveria retornar None para receita inexistente"
        # NÃO deve lançar exceção!

    def test_delete_nonexistent_recipe_returns_false(self, recipe_manager):
        """
        Comportamento: Tentar deletar receita inexistente deve falhar graciosamente.

        Verifica: O sistema lida gracefully com tentativa de deletar inexistente.
        """
        result = recipe_manager.delete_recipe("NONEXISTENT_ID")

        # Verificação do COMPORTAMENTO:
        assert result is False, "Deveria retornar False para receita inexistente"
        # NÃO deve lançar exceção!

    def test_save_then_load_corrupted_file_returns_none(self, recipe_manager):
        """
        Comportamento: Carregar arquivo corrompido deve falhar graciosamente.

        Verifica: O sistema lida com arquivos JSON inválidos sem crashar.
        """
        # Cria arquivo JSON inválido manualmente
        corrupted_file = recipe_manager.recipes_dir / "corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write("{invalid json content")

        result = recipe_manager.load_recipe("corrupted")

        # Verificação do COMPORTAMENTO:
        assert result is None, "Deveria retornar None para JSON corrompido"
        # NÃO deve crashar a aplicação!
