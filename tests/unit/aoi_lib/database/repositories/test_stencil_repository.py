"""
Testes para StencilRepository interface.

Testa a interface abstrata do repositório de stencils.
"""

import pytest
from abc import ABC, abstractmethod

# Import será criado após a implementação
# from aoi_lib.database.repositories.stencil_repository import StencilRepository
# from aoi_lib.stencil_tracker import Stencil


class TestStencilRepository:
    """Testa a interface abstrata StencilRepository."""

    def test_stencil_repository_is_abc(self):
        """Verifica se StencilRepository é uma classe abstrata."""
        from aoi_lib.database.repositories.stencil_repository import StencilRepository

        assert issubclass(StencilRepository, ABC)

    def test_stencil_repository_has_required_abstract_methods(self):
        """Verifica se StencilRepository tem todos os métodos abstratos exigidos."""
        from aoi_lib.database.repositories.stencil_repository import StencilRepository

        abstract_methods = StencilRepository.__abstractmethods__

        # Verifica se todos os métodos esperados são abstratos
        expected_methods = {
            'exists',
            'get',
            'create',
            'update',
            'delete',
            'list',
            'search',
            'get_by_recipe',
        }

        assert expected_methods.issubset(abstract_methods)

    def test_stencil_repository_methods_have_correct_signatures(self):
        """Verifica se os métodos têm as assinaturas corretas."""
        from aoi_lib.database.repositories.stencil_repository import StencilRepository
        from typing import get_type_hints
        from aoi_lib.stencil_tracker import Stencil

        # Verifica assinatura do método exists
        exists_signature = StencilRepository.exists.__annotations__
        assert 'code' in exists_signature
        assert 'return' in exists_signature

        # Verifica assinatura do método get
        get_signature = StencilRepository.get.__annotations__
        assert 'code' in get_signature
        assert 'return' in get_signature

        # Verifica assinatura do método create
        create_signature = StencilRepository.create.__annotations__
        assert 'code' in create_signature
        assert 'return' in create_signature
        assert 'Stencil' in str(create_signature.get('return', ''))

        # Verifica assinatura do método update
        update_signature = StencilRepository.update.__annotations__
        assert 'stencil' in update_signature
        assert 'stencil' in str(update_signature.get('stencil', ''))

        # Verifica assinatura do método delete
        delete_signature = StencilRepository.delete.__annotations__
        assert 'code' in delete_signature
        assert 'return' in delete_signature

        # Verifica assinatura do método list
        list_signature = StencilRepository.list.__annotations__
        assert 'return' in list_signature

        # Verifica assinatura do método search
        search_signature = StencilRepository.search.__annotations__
        assert 'query' in search_signature
        assert 'return' in search_signature

        # Verifica assinatura do método get_by_recipe
        get_by_recipe_signature = StencilRepository.get_by_recipe.__annotations__
        assert 'recipe_name' in get_by_recipe_signature
        assert 'return' in get_by_recipe_signature

    def test_stencil_repository_cannot_be_instantiated(self):
        """Verifica se StencilRepository não pode ser instanciada diretamente."""
        from aoi_lib.database.repositories.stencil_repository import StencilRepository

        # Tentar instanciar deve levantar TypeError
        with pytest.raises(TypeError):
            StencilRepository()

    def test_stencil_repository_has_docstring(self):
        """Verifica se StencilRepository tem docstring."""
        from aoi_lib.database.repositories.stencil_repository import StencilRepository

        assert StencilRepository.__doc__ is not None
        assert len(StencilRepository.__doc__) > 0

    def test_stencil_repository_methods_have_docstrings(self):
        """Verifica se os métodos de StencilRepository têm docstrings."""
        from aoi_lib.database.repositories.stencil_repository import StencilRepository

        methods_to_check = [
            'exists',
            'get',
            'create',
            'update',
            'delete',
            'list',
            'search',
            'get_by_recipe',
        ]

        for method_name in methods_to_check:
            method = getattr(StencilRepository, method_name)
            assert method.__doc__ is not None, f"{method_name} missing docstring"
            assert len(method.__doc__) > 0, f"{method_name} has empty docstring"
