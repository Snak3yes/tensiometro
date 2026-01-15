"""
Testes Unitários para FiducialMatchingService

Este módulo contém testes unitários para o serviço de template matching
de fiduciais, validando toda a lógica de matching sem dependência de PyQt6.

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
import numpy as np
import cv2

from aoi_lib.fiducial_matching_service import (
    FiducialMatchingService,
    MatchingError
)
from aoi_lib.fiducial_models import (
    FiducialPoint,
    FiducialConfig,
    FiducialType,
    MatchingMethod
)


class TestFiducialMatchingService:
    """Testes para FiducialMatchingService"""

    def test_init_default_config(self):
        """Testa inicialização com config padrão"""
        service = FiducialMatchingService()
        assert service.config is not None
        assert service.config.matching_method == MatchingMethod.CCOEFF_NORMED
        assert service.config.matching_threshold == 0.7

    def test_init_custom_config(self):
        """Testa inicialização com config customizada"""
        config = FiducialConfig(
            matching_method=MatchingMethod.SQDIFF_NORMED,
            matching_threshold=0.8,
            search_radius=150
        )
        service = FiducialMatchingService(config)
        assert service.config.matching_method == MatchingMethod.SQDIFF_NORMED
        assert service.config.matching_threshold == 0.8
        assert service.config.search_radius == 150

    def test_match_template_success(self):
        """Testa matching bem-sucedido"""
        service = FiducialMatchingService()

        # Criar imagem com padrão distinto
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(image, (50, 50), 20, 255, -1)  # Círculo branco sólido

        # Template é o mesmo círculo
        template = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(template, (20, 20), 18, 255, -1)

        # Buscar template
        result, correlation = service.match_template(
            image=image,
            template=template,
            search_center=(50, 50),
            search_radius=30
        )

        assert result is not None
        assert len(result) == 2
        assert correlation > 0.7  # Deve encontrar com boa correlação

    def test_match_template_below_threshold(self):
        """Testa matching com correlação abaixo do threshold"""
        config = FiducialConfig(matching_threshold=0.99)
        service = FiducialMatchingService(config)

        # Criar imagem e template muito diferentes
        image = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(image, (50, 50), 20, 255, -1)  # Círculo

        template = np.zeros((40, 40), dtype=np.uint8)
        cv2.rectangle(template, (5, 5), (35, 35), 255, -1)  # Quadrado (diferente!)

        # Buscar template - deve ter baixa correlação
        result, correlation = service.match_template(
            image=image,
            template=template,
            search_center=(50, 50),
            search_radius=30
        )

        # Não deve encontrar (correlação muito baixa para o threshold alto)
        assert result is None or correlation < 0.99

    def test_match_template_none_image(self):
        """Testa matching com imagem None"""
        service = FiducialMatchingService()

        template = np.zeros((20, 20), dtype=np.uint8)

        result, correlation = service.match_template(
            image=None,
            template=template,
            search_center=(50, 50),
            search_radius=30
        )

        assert result is None
        assert correlation == 0.0

    def test_match_template_none_template(self):
        """Testa matching com template None"""
        service = FiducialMatchingService()

        image = np.zeros((100, 100), dtype=np.uint8)

        result, correlation = service.match_template(
            image=image,
            template=None,
            search_center=(50, 50),
            search_radius=30
        )

        assert result is None
        assert correlation == 0.0

    def test_match_template_larger_than_image(self):
        """Testa matching com template maior que imagem"""
        service = FiducialMatchingService()

        image = np.zeros((50, 50), dtype=np.uint8)
        template = np.zeros((100, 100), dtype=np.uint8)  # Maior que imagem

        result, correlation = service.match_template(
            image=image,
            template=template,
            search_center=(25, 25),
            search_radius=30
        )

        assert result is None
        assert correlation == 0.0

    def test_match_template_outside_search_radius(self):
        """Testa matching com template fora do raio de busca"""
        service = FiducialMatchingService()

        image = np.zeros((100, 100), dtype=np.uint8)
        image[10:30, 10:30] = 255  # Quadrado em (10,10)

        template = np.zeros((20, 20), dtype=np.uint8)
        template[5:15, 5:15] = 255

        # Buscar no centro (50,50) com raio pequeno
        result, correlation = service.match_template(
            image=image,
            template=template,
            search_center=(50, 50),
            search_radius=10  # Raio muito pequeno
        )

        # Não deve encontrar porque template está fora do raio
        assert result is None

    def test_locate_fiducials_empty_list(self):
        """Testa localização com lista vazia"""
        service = FiducialMatchingService()
        image = np.zeros((100, 100), dtype=np.uint8)

        result = service.locate_fiducials(image, [])

        assert result == []

    def test_locate_fiducials_all_matched(self):
        """Testa localização com todos fiduciais encontrados"""
        service = FiducialMatchingService()

        # Criar imagem com 2 círculos
        image = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(image, (50, 50), 20, 255, -1)  # Marcador 1
        cv2.circle(image, (150, 150), 20, 255, -1)  # Marcador 2

        # Criar template (círculo)
        template = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(template, (20, 20), 18, 255, -1)

        # Criar fiduciais
        fiducials = [
            FiducialPoint(
                gerber_x=0, gerber_y=0,
                fiducial_type=FiducialType.TEMPLATE,
                template=template.copy(),
                template_x=50, template_y=50,
                search_radius=30
            ),
            FiducialPoint(
                gerber_x=100, gerber_y=100,
                fiducial_type=FiducialType.TEMPLATE,
                template=template.copy(),
                template_x=150, template_y=150,
                search_radius=30
            )
        ]

        result = service.locate_fiducials(image, fiducials)

        assert len(result) == 2
        assert result[0].is_matched
        assert result[1].is_matched
        assert result[0].correlation > 0.7
        assert result[1].correlation > 0.7

    def test_locate_fiducials_partial_match(self):
        """Testa localização com apenas alguns fiduciais encontrados"""
        service = FiducialMatchingService()

        # Criar imagem com apenas 1 círculo
        image = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(image, (50, 50), 20, 255, -1)  # Apenas 1 marcador

        # Criar template (círculo)
        template = np.zeros((40, 40), dtype=np.uint8)
        cv2.circle(template, (20, 20), 18, 255, -1)

        # Criar fiduciais (segundo não vai encontrar)
        fiducials = [
            FiducialPoint(
                gerber_x=0, gerber_y=0,
                fiducial_type=FiducialType.TEMPLATE,
                template=template.copy(),
                template_x=50, template_y=50,
                search_radius=30
            ),
            FiducialPoint(
                gerber_x=100, gerber_y=100,
                fiducial_type=FiducialType.TEMPLATE,
                template=template.copy(),
                template_x=150, template_y=150,
                search_radius=30
            )
        ]

        result = service.locate_fiducials(image, fiducials)

        assert len(result) == 2
        assert result[0].is_matched
        assert not result[1].is_matched  # Segundo não encontrado

    def test_locate_fiducials_without_template(self):
        """Testa localização com fiduciais sem template"""
        service = FiducialMatchingService()
        image = np.zeros((100, 100), dtype=np.uint8)

        # Criar fiduciais sem template
        fiducials = [
            FiducialPoint(gerber_x=0, gerber_y=0),
            FiducialPoint(gerber_x=10, gerber_y=10)
        ]

        result = service.locate_fiducials(image, fiducials)

        assert len(result) == 2
        assert not result[0].is_matched
        assert not result[1].is_matched

    def test_validate_match_good_correlation(self):
        """Testa validação de correlação boa"""
        service = FiducialMatchingService()

        is_valid, message = service.validate_match(0.85)

        assert is_valid
        assert "aceitável" in message.lower()

    def test_validate_match_below_threshold(self):
        """Testa validação de correlação abaixo do threshold"""
        service = FiducialMatchingService()

        is_valid, message = service.validate_match(0.5)

        assert not is_valid
        assert "abaixo do threshold" in message.lower()

    def test_validate_match_negative(self):
        """Testa validação de correlação negativa"""
        service = FiducialMatchingService()

        is_valid, message = service.validate_match(-0.1)

        assert not is_valid
        assert "negativa" in message.lower()

    def test_validate_match_above_one(self):
        """Testa validação de correlação acima de 1"""
        service = FiducialMatchingService()

        is_valid, message = service.validate_match(1.5)

        assert not is_valid
        assert "> 1" in message  # Mensagem é "Correlação > 1"

    def test_calculate_correlation_variance_all_matched(self):
        """Testa cálculo de variância com todos fiduciais matched"""
        service = FiducialMatchingService()

        fiducials = [
            FiducialPoint(0, 0, correlation=0.8, is_matched=True),
            FiducialPoint(10, 10, correlation=0.85, is_matched=True),
            FiducialPoint(20, 20, correlation=0.9, is_matched=True)
        ]

        variance = service.calculate_correlation_variance(fiducials)

        assert variance >= 0
        assert variance < 0.1  # Variância deve ser baixa

    def test_calculate_correlation_variance_unmatched(self):
        """Testa cálculo de variância com fiduciais unmatched"""
        service = FiducialMatchingService()

        fiducials = [
            FiducialPoint(0, 0, is_matched=False),
            FiducialPoint(10, 10, is_matched=False)
        ]

        variance = service.calculate_correlation_variance(fiducials)

        assert variance == 0.0  # Sem matched = variância zero

    def test_calculate_correlation_variance_single_match(self):
        """Testa cálculo de variância com apenas 1 matched"""
        service = FiducialMatchingService()

        fiducials = [
            FiducialPoint(0, 0, correlation=0.85, is_matched=True),
            FiducialPoint(10, 10, is_matched=False)
        ]

        variance = service.calculate_correlation_variance(fiducials)

        assert variance == 0.0  # 1 matched = variância zero

    def test_validate_correlation_variance_good(self):
        """Testa validação de variância de correlação boa"""
        service = FiducialMatchingService()

        fiducials = [
            FiducialPoint(0, 0, correlation=0.8, is_matched=True),
            FiducialPoint(10, 10, correlation=0.85, is_matched=True),
            FiducialPoint(20, 20, correlation=0.9, is_matched=True)
        ]

        is_valid, message = service.validate_correlation_variance(fiducials)

        assert is_valid
        assert "aceitável" in message.lower()

    def test_validate_correlation_variance_too_high(self):
        """Testa validação de variância muito alta"""
        config = FiducialConfig(max_correlation_variance=0.01)  # Limite muito baixo
        service = FiducialMatchingService(config)

        fiducials = [
            FiducialPoint(0, 0, correlation=0.5, is_matched=True),
            FiducialPoint(10, 10, correlation=0.95, is_matched=True)  # Variação grande!
        ]

        is_valid, message = service.validate_correlation_variance(fiducials)

        # Variância de [0.5, 0.95] é muito maior que 0.01
        assert not is_valid
        assert "muito alta" in message.lower() or "muito elevada" in message.lower()

    def test_get_matching_summary_complete(self):
        """Testa resumo de matching com todos dados"""
        service = FiducialMatchingService()

        fiducials = [
            FiducialPoint(0, 0, correlation=0.8, is_matched=True),
            FiducialPoint(10, 10, correlation=0.9, is_matched=True),
            FiducialPoint(20, 20, is_matched=False)
        ]

        summary = service.get_matching_summary(fiducials)

        assert summary['total_fiducials'] == 3
        assert summary['matched_fiducials'] == 2
        assert summary['unmatched_fiducials'] == 1
        assert summary['match_rate'] == 2/3
        assert 'min_correlation' in summary
        assert 'max_correlation' in summary
        assert 'mean_correlation' in summary

    def test_get_matching_summary_no_matches(self):
        """Testa resumo de matching sem matches"""
        service = FiducialMatchingService()

        fiducials = [
            FiducialPoint(0, 0, is_matched=False),
            FiducialPoint(10, 10, is_matched=False)
        ]

        summary = service.get_matching_summary(fiducials)

        assert summary['total_fiducials'] == 2
        assert summary['matched_fiducials'] == 0
        assert summary['unmatched_fiducials'] == 2
        assert summary['match_rate'] == 0.0
        assert 'min_correlation' not in summary


if __name__ == '__main__':
    # Executar testes
    pytest.main([__file__, '-v', '--tb=short'])
