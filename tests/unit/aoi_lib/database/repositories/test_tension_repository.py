"""
Testes para TensionRepository interface.

Testa a interface abstrata do repositório de registros de tensão.
"""

import pytest
from abc import ABC


class TestTensionRepository:
    """Testa a interface abstrata TensionRepository."""

    def test_tension_repository_is_abc(self):
        """Verifica se TensionRepository é uma classe abstrata."""
        from aoi_lib.database.repositories.tension_repository import TensionRepository

        assert issubclass(TensionRepository, ABC)

    def test_tension_repository_has_required_abstract_methods(self):
        """Verifica se TensionRepository tem todos os métodos abstratos exigidos."""
        from aoi_lib.database.repositories.tension_repository import TensionRepository

        abstract_methods = TensionRepository.__abstractmethods__

        # Verifica se todos os métodos esperados são abstratos
        expected_methods = {
            'add',
            'get_history',
            'get_by_period',
            'get_latest',
        }

        assert expected_methods.issubset(abstract_methods)

    def test_tension_repository_methods_have_correct_signatures(self):
        """Verifica se os métodos têm as assinaturas corretas."""
        from aoi_lib.database.repositories.tension_repository import TensionRepository
        from aoi_lib.stencil_tracker import TensionRecord

        # Verifica assinatura do método add
        add_signature = TensionRepository.add.__annotations__
        assert 'code' in add_signature
        assert 'record' in add_signature
        assert 'TensionRecord' in str(add_signature.get('record', ''))

        # Verifica assinatura do método get_history
        get_history_signature = TensionRepository.get_history.__annotations__
        assert 'code' in get_history_signature
        assert 'limit' in get_history_signature
        assert 'return' in get_history_signature

        # Verifica assinatura do método get_by_period
        get_by_period_signature = TensionRepository.get_by_period.__annotations__
        assert 'start_date' in get_by_period_signature
        assert 'end_date' in get_by_period_signature
        assert 'code' in get_by_period_signature or 'code' in str(get_by_period_signature)
        assert 'return' in get_by_period_signature

        # Verifica assinatura do método get_latest
        get_latest_signature = TensionRepository.get_latest.__annotations__
        assert 'code' in get_latest_signature
        assert 'return' in get_latest_signature

    def test_tension_repository_cannot_be_instantiated(self):
        """Verifica se TensionRepository não pode ser instanciada diretamente."""
        from aoi_lib.database.repositories.tension_repository import TensionRepository

        # Tentar instanciar deve levantar TypeError
        with pytest.raises(TypeError):
            TensionRepository()

    def test_tension_repository_has_docstring(self):
        """Verifica se TensionRepository tem docstring."""
        from aoi_lib.database.repositories.tension_repository import TensionRepository

        assert TensionRepository.__doc__ is not None
        assert len(TensionRepository.__doc__) > 0

    def test_tension_repository_methods_have_docstrings(self):
        """Verifica se os métodos de TensionRepository têm docstrings."""
        from aoi_lib.database.repositories.tension_repository import TensionRepository

        methods_to_check = [
            'add',
            'get_history',
            'get_by_period',
            'get_latest',
        ]

        for method_name in methods_to_check:
            method = getattr(TensionRepository, method_name)
            assert method.__doc__ is not None, f"{method_name} missing docstring"
            assert len(method.__doc__) > 0, f"{method_name} has empty docstring"
