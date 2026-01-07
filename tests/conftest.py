"""
Fixtures globais para testes do projeto Tensiometro.

Este arquivo é automaticamente carregado pelo pytest e disponibiliza
fixtures para todos os testes do projeto.
"""

import sys
import os
from pathlib import Path
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

# Adicionar diretório raiz ao path para importar aoi_lib
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# FIXTURES: Caminhos e Diretórios
# =============================================================================

@pytest.fixture(scope="session")
def project_root_dir():
    """Retorna o diretório raiz do projeto."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def fixtures_dir():
    """Retorna o diretório de fixtures de teste."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def gerber_fixtures_dir(fixtures_dir):
    """Retorna o diretório de arquivos Gerber de teste."""
    gerber_dir = fixtures_dir / "gerber"
    gerber_dir.mkdir(parents=True, exist_ok=True)
    return gerber_dir


@pytest.fixture(scope="session")
def image_fixtures_dir(fixtures_dir):
    """Retorna o diretório de imagens de teste."""
    img_dir = fixtures_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    return img_dir


# =============================================================================
# FIXTURES: Mock de Hardware
# =============================================================================

@pytest.fixture
def mock_plc_client():
    """
    Mock de cliente Modbus TCP para o PLC.

    Simula respostas do PLC Delta sem necessidade de hardware físico.
    """
    mock = MagicMock()
    mock.connect.return_value = True
    mock.is_socket_open.return_value = True

    # Mock de leitura de registradores
    def read_holding_registers(address, count):
        # Simula posição dos eixos
        if address == 1100:  # Eixo X
            return [1000]  # 1000 pulsos
        elif address == 600:  # Eixo Y
            return [500]
        elif address == 1600:  # Eixo Z
            return [0]
        return [0]

    mock.read_holding_registers.side_effect = read_holding_registers
    mock.write_registers.return_value = True
    mock.read_coils.return_value = [False]
    mock.write_coil.return_value = True

    return mock


@pytest.fixture
def mock_serial_connection():
    """
    Mock de conexão serial para o tensiômetro.

    Simula leitura do protocolo AS-120N sem hardware físico.
    """
    mock = MagicMock()
    mock.is_open = True
    mock.port = 'COM3'
    mock.baudrate = 2400

    # Mock de leitura de frame de tensão (9 bytes)
    # Frame válido: 0x10 0x19 0x02 0x26 0x1A 0x2B 0x3C 0x00 0x00
    # Valor decodificado: 12.3 N/cm²
    valid_frame = bytes([0x10, 0x19, 0x02, 0x26, 0x1A, 0x2B, 0x3C, 0x00, 0x00])
    mock.read.return_value = valid_frame
    mock.write.return_value = 0
    mock.reset_input_buffer.return_value = None
    mock.reset_output_buffer.return_value = None

    return mock


@pytest.fixture
def mock_camera():
    """
    Mock de câmera OpenCV.

    Simula captura de imagens sem câmera física.
    """
    mock = MagicMock()
    mock.isOpened.return_value = True
    mock.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock.get.return_value = 30.0  # FPS padrão
    mock.set.return_value = True

    return mock


# =============================================================================
# FIXTURES: Imagens Sintéticas
# =============================================================================

@pytest.fixture
def blank_image():
    """Retorna imagem em branco (640x480x3)."""
    return np.ones((480, 640, 3), dtype=np.uint8) * 255


@pytest.fixture
def black_image():
    """Retorna imagem preta (640x480x3)."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def gray_image():
    """Retorna imagem cinza (640x480x3)."""
    return np.ones((480, 640, 3), dtype=np.uint8) * 128


# =============================================================================
# FIXTURES: Dados de Teste
# =============================================================================

@pytest.fixture
def sample_stencil_data():
    """Retorna dados de stencil de exemplo."""
    return {
        "code": "TEST-001",
        "description": "Stencil de teste",
        "recipe_name": "SAMPLE_001",
        "status": "active",
        "creation_date": "2026-01-07T10:00:00"
    }


@pytest.fixture
def sample_recipe_data():
    """Retorna dados de receita de exemplo."""
    return {
        "name": "SAMPLE_001",
        "description": "Receita de teste",
        "dimensions": {
            "width_mm": 500.0,
            "height_mm": 500.0,
            "thickness_mm": 0.127
        },
        "tension_acceptance": {
            "ok_min": 35.0,
            "warning_min": 30.0,
            "nok_max": 25.0
        },
        "inspection_thresholds": {
            "ok_threshold": 90.0,
            "partial_threshold": 70.0
        }
    }


@pytest.fixture
def sample_tension_measurements():
    """
    Retorna medições de tensão de exemplo (grid 3x3).

    Valores em N/cm.
    """
    return [
        [38.5, 39.2, 38.8],
        [37.9, 38.1, 39.0],
        [38.3, 38.7, 38.4]
    ]


@pytest.fixture
def temp_config_file(tmp_path):
    """
    Cria um arquivo de configuração temporário.

    Útil para testes que modificam configurações.
    """
    config_file = tmp_path / "test_config.json"

    # Config padrão de teste
    import json
    default_config = {
        "cnc": {
            "max_feed": 3000.0,
            "max_acc": 500.0
        },
        "connections": {
            "plc_host": "192.168.1.5",
            "plc_port": 502
        }
    }

    config_file.write_text(json.dumps(default_config, indent=2))
    return config_file


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def assert_valid_gerber_bounds(bounds):
    """
    Helper para validar bounds de Gerber.

    Args:
        bounds: Objeto com atributos min_x, max_x, min_y, max_y
    """
    assert bounds.min_x < bounds.max_x, "min_x deve ser menor que max_x"
    assert bounds.min_y < bounds.max_y, "min_y deve ser menor que max_y"
    assert bounds.min_x >= 0, "min_x deve ser não-negativo"
    assert bounds.min_y >= 0, "min_y deve ser não-negativo"


def assert_classification(classification, expected_range):
    """
    Helper para validar classificação de inspeção.

    Args:
        classification: String ("OK", "PARTIAL", "BLOCKED")
        expected_range: Tuple de valores (min, max) aceitáveis
    """
    assert classification in ["OK", "PARTIAL", "BLOCKED"]
