"""
Testes para InspectionRepository interface.

Testa a interface abstrata do repositório de registros de inspeção.
"""

import pytest
from abc import ABC


class TestInspectionRepository:
    """Testa a interface abstrata InspectionRepository."""

    def test_inspection_repository_is_abc(self):
        """Verifica se InspectionRepository é uma classe abstrata."""
        from aoi_lib.database.repositories.inspection_repository import InspectionRepository

        assert issubclass(InspectionRepository, ABC)

    def test_inspection_repository_has_required_abstract_methods(self):
        """Verifica se InspectionRepository tem todos os métodos abstratos exigidos."""
        from aoi_lib.database.repositories.inspection_repository import InspectionRepository

        abstract_methods = InspectionRepository.__abstractmethods__

        # Verifica se todos os métodos esperados são abstratos
        expected_methods = {
            'add',
            'get_history',
            'get_by_period',
            'get_stats',
            'get_combined_history',
        }

        assert expected_methods.issubset(abstract_methods)

    def test_inspection_repository_methods_have_correct_signatures(self):
        """Verifica se os métodos têm as assinaturas corretas."""
        from aoi_lib.database.repositories.inspection_repository import InspectionRepository
        from aoi_lib.stencil_tracker import InspectionRecord

        # Verifica assinatura do método add
        add_signature = InspectionRepository.add.__annotations__
        assert 'code' in add_signature
        assert 'record' in add_signature
        assert 'InspectionRecord' in str(add_signature.get('record', ''))

        # Verifica assinatura do método get_history
        get_history_signature = InspectionRepository.get_history.__annotations__
        assert 'code' in get_history_signature
        assert 'limit' in get_history_signature
        assert 'return' in get_history_signature

        # Verifica assinatura do método get_by_period
        get_by_period_signature = InspectionRepository.get_by_period.__annotations__
        assert 'start_date' in get_by_period_signature
        assert 'end_date' in get_by_period_signature
        assert 'code' in get_by_period_signature or 'code' in str(get_by_period_signature)
        assert 'return' in get_by_period_signature

        # Verifica assinatura do método get_stats
        get_stats_signature = InspectionRepository.get_stats.__annotations__
        assert 'code' in get_stats_signature
        assert 'return' in get_stats_signature

        # Verifica assinatura do método get_combined_history
        get_combined_history_signature = InspectionRepository.get_combined_history.__annotations__
        assert 'code' in get_combined_history_signature
        assert 'limit' in get_combined_history_signature
        assert 'return' in get_combined_history_signature

    def test_inspection_repository_cannot_be_instantiated(self):
        """Verifica se InspectionRepository não pode ser instanciada diretamente."""
        from aoi_lib.database.repositories.inspection_repository import InspectionRepository

        # Tentar instanciar deve levantar TypeError
        with pytest.raises(TypeError):
            InspectionRepository()

    def test_inspection_repository_has_docstring(self):
        """Verifica se InspectionRepository tem docstring."""
        from aoi_lib.database.repositories.inspection_repository import InspectionRepository

        assert InspectionRepository.__doc__ is not None
        assert len(InspectionRepository.__doc__) > 0

    def test_inspection_repository_methods_have_docstrings(self):
        """Verifica se os métodos de InspectionRepository têm docstrings."""
        from aoi_lib.database.repositories.inspection_repository import InspectionRepository

        methods_to_check = [
            'add',
            'get_history',
            'get_by_period',
            'get_stats',
            'get_combined_history',
        ]

        for method_name in methods_to_check:
            method = getattr(InspectionRepository, method_name)
            assert method.__doc__ is not None, f"{method_name} missing docstring"
            assert len(method.__doc__) > 0, f"{method_name} has empty docstring"
