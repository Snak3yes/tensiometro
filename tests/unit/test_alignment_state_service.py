"""
Testes Unitários para AlignmentStateService

Este módulo contém testes unitários para o serviço de gerenciamento
de estado de alinhamento, validando CRUD, serialização e validação.

Author: Claude Code (Sonnet 4.5)
Created: 2026-01-15
Phase: SOLID Refactoring Phase 5B.2
"""

import sys
from pathlib import Path

# Adiciona diretório raiz ao sys.path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pytest
import tempfile
import os

from aoi_lib.alignment_state_service import (
    AlignmentStateService,
    StateError
)
from aoi_lib.fiducial_models import (
    FiducialPoint,
    AlignmentTransform,
    AlignmentState,
    FiducialConfig,
    FiducialType
)


class TestAlignmentStateService:
    """Testes para AlignmentStateService"""

    def test_init(self):
        """Testa inicialização do serviço"""
        service = AlignmentStateService()
        assert service is not None

    def test_create_state_empty(self):
        """Testa criação de estado vazio"""
        service = AlignmentStateService()

        state = service.create_state()

        assert state is not None
        assert len(state.fiducials) == 0
        assert state.transform is None
        assert isinstance(state.config, FiducialConfig)

    def test_create_state_with_fiducials(self):
        """Testa criação de estado com fiduciais"""
        service = AlignmentStateService()

        fiducials = [
            FiducialPoint(gerber_x=0, gerber_y=0),
            FiducialPoint(gerber_x=10, gerber_y=10)
        ]

        state = service.create_state(fiducials=fiducials)

        assert len(state.fiducials) == 2
        assert state.fiducials[0].gerber_x == 0
        assert state.fiducials[1].gerber_x == 10

    def test_create_state_with_config(self):
        """Testa criação de estado com config customizada"""
        service = AlignmentStateService()

        config = FiducialConfig(
            matching_threshold=0.8,
            search_radius=150
        )

        state = service.create_state(config=config)

        assert state.config.matching_threshold == 0.8
        assert state.config.search_radius == 150

    def test_add_fiducial_default_params(self):
        """Testa adição de fiducial com parâmetros padrão"""
        service = AlignmentStateService()
        state = service.create_state()

        fiducial = service.add_fiducial(
            state=state,
            gerber_x=10.0,
            gerber_y=20.0
        )

        assert len(state.fiducials) == 1
        assert fiducial.gerber_x == 10.0
        assert fiducial.gerber_y == 20.0
        assert fiducial.fiducial_type.value == "gerber"

    def test_add_fiducial_custom_params(self):
        """Testa adição de fiducial com parâmetros customizados"""
        service = AlignmentStateService()
        state = service.create_state()

        fiducial = service.add_fiducial(
            state=state,
            gerber_x=10.0,
            gerber_y=20.0,
            fiducial_type="template",
            window_size=60,
            search_radius=120
        )

        assert fiducial.window_size == 60
        assert fiducial.search_radius == 120
        assert fiducial.fiducial_type.value == "template"

    def test_add_multiple_fiducials(self):
        """Testa adição de múltiplos fiduciais"""
        service = AlignmentStateService()
        state = service.create_state()

        service.add_fiducial(state, 0, 0)
        service.add_fiducial(state, 10, 10)
        service.add_fiducial(state, 20, 20)

        assert len(state.fiducials) == 3

    def test_remove_fiducial_first(self):
        """Testa remoção do primeiro fiducial"""
        service = AlignmentStateService()
        state = service.create_state()

        service.add_fiducial(state, 0, 0)
        service.add_fiducial(state, 10, 10)
        service.add_fiducial(state, 20, 20)

        service.remove_fiducial(state, 0)

        assert len(state.fiducials) == 2
        assert state.fiducials[0].gerber_x == 10  # Agora o segundo é o primeiro

    def test_remove_fiducial_last(self):
        """Testa remoção do último fiducial"""
        service = AlignmentStateService()
        state = service.create_state()

        service.add_fiducial(state, 0, 0)
        service.add_fiducial(state, 10, 10)
        service.add_fiducial(state, 20, 20)

        service.remove_fiducial(state, 2)

        assert len(state.fiducials) == 2

    def test_remove_fiducial_invalid_index(self):
        """Testa que índice inválido lança exceção"""
        service = AlignmentStateService()
        state = service.create_state()

        service.add_fiducial(state, 0, 0)

        with pytest.raises(StateError, match="Índice 5 inválido"):
            service.remove_fiducial(state, 5)

    def test_remove_fiducial_negative_index(self):
        """Testa que índice negativo lança exceção"""
        service = AlignmentStateService()
        state = service.create_state()

        service.add_fiducial(state, 0, 0)

        with pytest.raises(StateError, match="Índice -1 inválido"):
            service.remove_fiducial(state, -1)

    def test_update_fiducial_coordinates(self):
        """Testa atualização de coordenadas de fiducial"""
        service = AlignmentStateService()
        state = service.create_state()

        service.add_fiducial(state, 0, 0)
        service.update_fiducial(
            state,
            index=0,
            gerber_x=50,
            gerber_y=100
        )

        assert state.fiducials[0].gerber_x == 50
        assert state.fiducials[0].gerber_y == 100

    def test_update_fiducial_template(self):
        """Testa atualização de template de fiducial"""
        service = AlignmentStateService()
        state = service.create_state()

        service.add_fiducial(state, 0, 0)

        import numpy as np
        template = np.zeros((20, 20), dtype=np.uint8)

        service.update_fiducial(
            state,
            index=0,
            template=template,
            template_x=100,
            template_y=200
        )

        assert state.fiducials[0].template is not None
        assert state.fiducials[0].template_x == 100
        assert state.fiducials[0].template_y == 200

    def test_update_fiducial_invalid_index(self):
        """Testa que atualizar índice inválido lança exceção"""
        service = AlignmentStateService()
        state = service.create_state()

        with pytest.raises(StateError, match="Índice 0 inválido"):
            service.update_fiducial(state, 0, gerber_x=50)

    def test_validate_state_insufficient_fiducials(self):
        """Testa validação com fiduciais insuficientes"""
        service = AlignmentStateService()
        state = service.create_state()

        service.add_fiducial(state, 0, 0)

        is_valid, message = service.validate_state(state)

        assert not is_valid
        assert "pelo menos 2" in message.lower()

    def test_validate_state_without_templates(self):
        """Testa validação sem templates capturados"""
        service = AlignmentStateService()
        state = service.create_state()

        service.add_fiducial(state, 0, 0)
        service.add_fiducial(state, 10, 10)

        is_valid, message = service.validate_state(state)

        assert not is_valid
        assert "sem template" in message.lower()

    def test_validate_state_without_matches(self):
        """Testa validação sem matches"""
        service = AlignmentStateService()
        state = service.create_state()

        import numpy as np
        template = np.zeros((20, 20), dtype=np.uint8)

        f1 = service.add_fiducial(state, 0, 0, template=template, template_x=0, template_y=0)
        f2 = service.add_fiducial(state, 10, 10, template=template, template_x=10, template_y=10)

        is_valid, message = service.validate_state(state)

        assert not is_valid
        assert "match" in message.lower()

    def test_validate_state_success(self):
        """Testa validação bem-sucedida"""
        service = AlignmentStateService()
        state = service.create_state()

        import numpy as np
        template = np.zeros((20, 20), dtype=np.uint8)

        f1 = service.add_fiducial(state, 0, 0, template=template, template_x=0, template_y=0)
        f1.is_matched = True
        f1.matched_x = 100
        f1.matched_y = 100
        f1.correlation = 0.85

        f2 = service.add_fiducial(state, 10, 10, template=template, template_x=10, template_y=10)
        f2.is_matched = True
        f2.matched_x = 110
        f2.matched_y = 110
        f2.correlation = 0.9

        is_valid, message = service.validate_state(state)

        assert is_valid
        assert "válido" in message.lower()

    def test_serialize_state_empty(self):
        """Testa serialização de estado vazio"""
        service = AlignmentStateService()
        state = service.create_state()

        json_str = service.serialize_state(state)

        assert json_str is not None
        assert len(json_str) > 0
        assert "fiducials" in json_str

    def test_serialize_deserialize_roundtrip(self):
        """Testa roundtrip de serialização/desserialização"""
        service = AlignmentStateService()

        import numpy as np
        template = np.zeros((20, 20), dtype=np.uint8)

        # Criar estado com dados
        original_state = service.create_state()
        service.add_fiducial(
            original_state, 0, 0,
            fiducial_type="template",
            template=template,
            template_x=100, template_y=200
        )
        service.add_fiducial(original_state, 10, 10)

        transform = AlignmentTransform(tx=5, ty=10, angle=2.5, scale_x=1.0)
        original_state.transform = transform

        # Serializar
        json_str = service.serialize_state(original_state)

        # Desserializar
        restored_state = service.deserialize_state(json_str)

        # Validar
        assert len(restored_state.fiducials) == len(original_state.fiducials)
        assert restored_state.transform.tx == original_state.transform.tx
        assert restored_state.transform.ty == original_state.transform.ty

    def test_serialize_deserialize_with_transform(self):
        """Testa serialização com transformação"""
        service = AlignmentStateService()

        state = service.create_state()
        state.transform = AlignmentTransform(
            tx=100.5,
            ty=200.3,
            angle=45.7,
            scale_x=1.5,
            scale_y=1.2
        )

        json_str = service.serialize_state(state)
        restored = service.deserialize_state(json_str)

        assert abs(restored.transform.tx - 100.5) < 0.01
        assert abs(restored.transform.ty - 200.3) < 0.01
        assert abs(restored.transform.angle - 45.7) < 0.01

    def test_save_load_state_file(self):
        """Testa salvamento/carregamento de arquivo"""
        service = AlignmentStateService()

        # Criar estado temporário
        state = service.create_state()
        service.add_fiducial(state, 10, 20)
        service.add_fiducial(state, 30, 40)

        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            # Salvar
            service.save_state(state, temp_path)

            # Carregar
            loaded_state = service.load_state(temp_path)

            # Validar
            assert len(loaded_state.fiducials) == 2
            assert loaded_state.fiducials[0].gerber_x == 10
            assert loaded_state.fiducials[1].gerber_x == 30

        finally:
            # Limpar
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_get_state_summary_empty(self):
        """Testa resumo de estado vazio"""
        service = AlignmentStateService()
        state = service.create_state()

        summary = service.get_state_summary(state)

        assert summary['total_fiducials'] == 0
        assert summary['matched_fiducials'] == 0
        assert summary['match_rate'] == 0.0
        assert summary['has_transform'] is False

    def test_get_state_summary_with_transform(self):
        """Testa resumo de estado com transformação"""
        service = AlignmentStateService()
        state = service.create_state()

        state.transform = AlignmentTransform(
            tx=10, ty=20, angle=5, scale_x=1.5
        )

        summary = service.get_state_summary(state)

        assert summary['has_transform'] is True
        assert 'transform' in summary
        assert summary['transform']['tx'] == 10

    def test_get_state_summary_with_correlations(self):
        """Testa resumo com correlações"""
        service = AlignmentStateService()
        state = service.create_state()

        import numpy as np
        template = np.zeros((20, 20), dtype=np.uint8)

        f1 = service.add_fiducial(state, 0, 0, template=template, template_x=0, template_y=0)
        f1.is_matched = True
        f1.matched_x = 100
        f1.matched_y = 100
        f1.correlation = 0.8

        f2 = service.add_fiducial(state, 10, 10, template=template, template_x=10, template_y=10)
        f2.is_matched = True
        f2.matched_x = 110
        f2.matched_y = 110
        f2.correlation = 0.9

        summary = service.get_state_summary(state)

        assert summary['total_fiducials'] == 2
        assert summary['matched_fiducials'] == 2
        assert 'min_correlation' in summary
        assert 'max_correlation' in summary
        assert abs(summary['min_correlation'] - 0.8) < 0.01
        assert abs(summary['max_correlation'] - 0.9) < 0.01

    def test_clone_state(self):
        """Testa clonagem de estado"""
        service = AlignmentStateService()

        import numpy as np
        template = np.zeros((20, 20), dtype=np.uint8)

        original = service.create_state()
        service.add_fiducial(original, 0, 0, template=template, template_x=10, template_y=20)
        original.transform = AlignmentTransform(tx=5, ty=10, angle=2, scale_x=1)

        cloned = service.clone_state(original)

        # Validar que é uma cópia
        assert len(cloned.fiducials) == len(original.fiducials)
        assert cloned.transform.tx == original.transform.tx

        # Modificar original
        original.fiducials[0].gerber_x = 999

        # Clonado não deve ser afetado
        assert cloned.fiducials[0].gerber_x == 0


if __name__ == '__main__':
    # Executar testes
    pytest.main([__file__, '-v', '--tb=short'])
