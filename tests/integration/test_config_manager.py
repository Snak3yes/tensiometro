"""
test_config_manager.py
-----------------------
Testes de integração para config_manager.py.

Cobertura:
- AOIConfigManager - gerenciamento de configuração JSON
- Carregamento e salvamento
- API get/set
- Métodos de atalho (remember_*)
- Presets de câmera
- apply_to_cnc
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from aoi_lib.config_manager import AOIConfigManager


# ============================================================================
#  FIXTURES
# ============================================================================

@pytest.fixture
def temp_config_file(tmp_path):
    """Cria um arquivo de configuração temporário com valores padrão limpos."""
    import uuid
    # Usa UUID para garantir que cada teste tenha um arquivo único
    config_file = tmp_path / f"test_config_{uuid.uuid4().hex}.json"

    # Garante que o arquivo não existe (força criação do zero)
    if config_file.exists():
        config_file.unlink()

    # Pré-cria o arquivo com config padrão vazia para garantir isolamento total
    default_config = {
        "cnc": {
            "system_type": "cartesian",
            "max_feed": {"x": 2500.0, "y": 2500.0, "z": 800.0},
            "max_acc": {"x": 120.0, "y": 120.0, "z": 60.0},
            "invert_y": True,
            "invert_z": False,
            "motor_hold_enabled": True,
            "corexy_config": {
                "motor_a_invert": False,
                "motor_b_invert": False,
                "steps_per_unit": 80.0
            }
        },
        "connections": {
            "last_cnc_port": "",
            "plc_host": "192.168.1.5",
            "plc_port": 502,
            "auto_connect_cnc": True,
            "last_camera_id": 0,
            "auto_connect_camera": True,
            "backlight_coil": 1
        },
        "ui": {
            "theme": "light"
        },
        "movement": {
            "step_size": 10.0,
            "feed_rate": 1000.0
        },
        "calibration": {
            "pulses_per_rev": 400.0,
            "fuso_pitch": 5.0
        },
        "camera": {
            "mirror_x": False,
            "mirror_y": False,
            "brightness": 128,
            "contrast": 128,
            "saturation": 128,
            "exposure": -6,
            "gain": 128,
            "focus": 0,
            "auto_focus": True,
            "auto_exposure": True,
            "auto_white_balance": True,
            "presets": {},
            "calibration_file": "",
            "crosshair": {
                "color_r": 0,
                "color_g": 0,
                "color_b": 255,
                "thickness": 2,
                "length_percent": 5
            }
        },
        "mosaic": {
            "auto_build": True,
            "margin": 50,
            "blend_size": 20,
            "use_multiband": False,
            "capture_delay_ms": 200,
            "delta_x": 0,
            "delta_y": 0,
            "invert_rows": True,
            "last_folder": "",
            "last_program_name": ""
        },
        "map": {
            "step_x": 50.0,
            "step_y": 50.0
        }
    }

    # Escreve o config padrão no arquivo temporário
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2)

    return config_file


@pytest.fixture
def nonexistent_config_file(tmp_path):
    """Cria um caminho de arquivo que não existe (para teste de criação automática)."""
    import uuid
    config_file = tmp_path / f"test_config_{uuid.uuid4().hex}.json"
    # Garante que o arquivo não existe
    if config_file.exists():
        config_file.unlink()
    return config_file


@pytest.fixture
def sample_config_data():
    """Dados de configuração de exemplo."""
    return {
        "cnc": {
            "system_type": "cartesian",
            "max_feed": {"x": 2500.0, "y": 2500.0, "z": 800.0},
            "invert_y": True
        },
        "connections": {
            "plc_host": "192.168.1.5",
            "plc_port": 502,
            "auto_connect_camera": True
        },
        "movement": {
            "step_size": 10.0,
            "feed_rate": 1000.0
        },
        "camera": {
            "brightness": 128,
            "presets": {}
        }
    }


@pytest.fixture
def mock_cnc():
    """Mock de controlador CNC."""
    cnc = Mock()
    cnc.is_connected = True
    cnc.max_feed = {"x": 5000, "y": 5000, "z": 800}
    cnc.pulses_per_mm = 80.0
    cnc.backlight_coil_address = 1
    return cnc


# ============================================================================
#  TESTES: AOIConfigManager - Inicialização
# ============================================================================

class TestAOIConfigManagerInitialization:
    """Testes para inicialização do AOIConfigManager."""

    def test_initialization_with_path(self, temp_config_file):
        """Testa inicialização com caminho específico."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        assert manager.cfg_path == temp_config_file
        assert isinstance(manager.data, dict)

    def test_initialization_without_path(self, temp_config_file):
        """Testa inicialização sem caminho (usa padrão)."""
        # Usa arquivo temporário para evitar poluir o config real
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # Deve usar o caminho fornecido
        assert manager.cfg_path == temp_config_file
        assert isinstance(manager.cfg_path, Path)

    def test_default_config_structure(self, temp_config_file):
        """Testa que configuração padrão tem estrutura esperada."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # Verifica seções principais existem
        assert "cnc" in manager.data
        assert "connections" in manager.data
        assert "movement" in manager.data
        assert "calibration" in manager.data
        assert "camera" in manager.data
        assert "mosaic" in manager.data
        assert "map" in manager.data

    def test_default_cnc_config(self, temp_config_file):
        """Testa valores padrão de configuração CNC."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        cnc_cfg = manager.data["cnc"]
        assert cnc_cfg["system_type"] == "cartesian"
        assert cnc_cfg["invert_y"] is True
        assert cnc_cfg["invert_z"] is False

    def test_default_connections_config(self, temp_config_file):
        """Testa valores padrão de conexões."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        conn_cfg = manager.data["connections"]
        assert conn_cfg["plc_host"] == "192.168.1.5"
        assert conn_cfg["plc_port"] == 502
        assert conn_cfg["auto_connect_cnc"] is True
        assert conn_cfg["auto_connect_camera"] is True


# ============================================================================
#  TESTES: AOIConfigManager - Load/Save
# ============================================================================

class TestAOIConfigManagerLoadSave:
    """Testes para carregamento e salvamento."""

    def test_load_from_existing_file(self, temp_config_file, sample_config_data):
        """Testa carregamento de arquivo existente."""
        # Cria arquivo de configuração
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_config_data, f)

        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        assert manager.data == sample_config_data

    def test_load_from_nonexistent_file(self, nonexistent_config_file):
        """Testa carregamento de arquivo inexistente (cria padrão)."""
        # Arquivo não existe
        assert not nonexistent_config_file.exists()

        manager = AOIConfigManager(cfg_path=str(nonexistent_config_file))

        # Deve criar com configuração padrão
        assert manager.data is not None
        assert "cnc" in manager.data
        # E salvar o arquivo
        assert nonexistent_config_file.exists()

    def test_load_from_invalid_json(self, temp_config_file):
        """Testa carregamento de JSON inválido (usa padrão)."""
        # Cria arquivo com JSON inválido
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            f.write("{invalid json}")

        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # Deve fallback para configuração padrão
        assert manager.data is not None
        assert "cnc" in manager.data

    def test_save_creates_file(self, temp_config_file):
        """Testa que salvamento cria arquivo."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # Modifica um valor
        manager.set("movement", "step_size", value=5.0)

        # Verifica que arquivo foi criado/salvo
        assert temp_config_file.exists()

        # Verifica conteúdo
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            assert data["movement"]["step_size"] == 5.0


# ============================================================================
#  TESTES: AOIConfigManager - API Get/Set
# ============================================================================

class TestAOIConfigManagerGetSet:
    """Testes para API get/set."""

    def test_get_simple_value(self, temp_config_file):
        """Testa get de valor simples."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        step = manager.get("movement", "step_size")

        assert step == 10.0

    def test_get_nested_value(self, temp_config_file):
        """Testa get de valor aninhado."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        max_feed_x = manager.get("cnc", "max_feed", "x")

        assert max_feed_x == 2500.0

    def test_get_with_default(self, temp_config_file):
        """Testa get com valor padrão para chave inexistente."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        value = manager.get("inexistente", "chave", default=42)

        assert value == 42

    def test_get_without_default_returns_none(self, temp_config_file):
        """Testa get sem default retorna None para chave inexistente."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        value = manager.get("inexistente", "chave")

        assert value is None

    def test_set_simple_value(self, temp_config_file):
        """Testa set de valor simples."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.set("test_section", "test_key", value=123)

        assert manager.get("test_section", "test_key") == 123

    def test_set_nested_value(self, temp_config_file):
        """Testa set de valor aninhado."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.set("movement", "step_size", value=5.0)

        assert manager.get("movement", "step_size") == 5.0

    def test_set_deep_nested_value(self, temp_config_file):
        """Testa set de valor profundamente aninhado."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.set("cnc", "max_feed", "x", value=3000.0)

        assert manager.get("cnc", "max_feed", "x") == 3000.0

    def test_set_creates_intermediate_dicts(self, temp_config_file):
        """Testa que set cria dicionários intermediários."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # Seção e chave não existem
        manager.set("nova_secao", "nova_chave", value="teste")

        assert manager.get("nova_secao", "nova_chave") == "teste"
        assert "nova_secao" in manager.data

    def test_set_and_get_persistence(self, temp_config_file):
        """Testa que valores persistem via save."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.set("test", "value", value=999)

        # Recarrega
        manager2 = AOIConfigManager(cfg_path=str(temp_config_file))

        assert manager2.get("test", "value") == 999


# ============================================================================
#  TESTES: AOIConfigManager - Atalhos (remember_*)
# ============================================================================

class TestAOIConfigManagerShortcuts:
    """Testes para métodos de atalho remember_*."""

    def test_remember_cnc_port(self, temp_config_file):
        """Testa lembrar porta CNC."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_cnc_port("COM3")

        assert manager.get("connections", "last_cnc_port") == "COM3"

    def test_remember_camera_id_int(self, temp_config_file):
        """Testa lembrar ID de câmera (int)."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_camera_id(0)

        assert manager.get("connections", "last_camera_id") == 0

    def test_remember_camera_id_str(self, temp_config_file):
        """Testa lembrar ID de câmera (string/http)."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_camera_id("http://192.168.1.100:8080")

        assert manager.get("connections", "last_camera_id") == "http://192.168.1.100:8080"

    def test_remember_step_feed(self, temp_config_file):
        """Testa lembrar passo e feed."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_step_feed(5.0, 800.0)

        assert manager.get("movement", "step_size") == 5.0
        assert manager.get("movement", "feed_rate") == 800.0

    def test_remember_calibration(self, temp_config_file):
        """Testa lembrar calibração."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_calibration(400.0, 5.0)

        assert manager.get("calibration", "pulses_per_rev") == 400.0
        assert manager.get("calibration", "fuso_pitch") == 5.0

    def test_remember_system_type(self, temp_config_file):
        """Testa lembrar tipo de sistema."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_system_type("corexy")

        assert manager.get("cnc", "system_type") == "corexy"

    def test_remember_camera_settings(self, temp_config_file):
        """Testa lembrar configurações completas de câmera."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_camera_settings(
            mirror_x=True,
            mirror_y=False,
            brightness=200,
            contrast=130,
            exposure=-5
        )

        assert manager.get("camera", "mirror_x") is True
        assert manager.get("camera", "mirror_y") is False
        assert manager.get("camera", "brightness") == 200
        assert manager.get("camera", "contrast") == 130
        assert manager.get("camera", "exposure") == -5

    def test_remember_mosaic_settings(self, temp_config_file):
        """Testa lembrar configurações de mosaico."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_mosaic_settings(
            auto_build=True,
            margin=50,
            blend_size=20,
            capture_delay_ms=200,
            use_multiband=False
        )

        assert manager.get("mosaic", "auto_build") is True
        assert manager.get("mosaic", "margin") == 50
        assert manager.get("mosaic", "blend_size") == 20
        assert manager.get("mosaic", "capture_delay_ms") == 200
        assert manager.get("mosaic", "use_multiband") is False

    def test_remember_mosaic_adjustments(self, temp_config_file):
        """Testa lembrar ajustes de mosaico."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_mosaic_adjustments(delta_x=5, delta_y=-3, invert_rows=True)

        assert manager.get("mosaic", "delta_x") == 5
        assert manager.get("mosaic", "delta_y") == -3
        assert manager.get("mosaic", "invert_rows") is True

    def test_remember_map_params(self, temp_config_file):
        """Testa lembrar parâmetros de mapa."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_map_params(
            step_x=50.0,
            step_y=50.0,
            folder="/path/to/folder",
            program_name="test_program"
        )

        assert manager.get("map", "step_x") == 50.0
        assert manager.get("map", "step_y") == 50.0
        assert manager.get("mosaic", "last_folder") == "/path/to/folder"
        assert manager.get("mosaic", "last_program_name") == "test_program"

    def test_remember_camera_calibration(self, temp_config_file):
        """Testa lembrar arquivo de calibração de câmera."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.remember_camera_calibration("/path/to/calibration.json")

        assert manager.get("camera", "calibration_file") == "/path/to/calibration.json"


# ============================================================================
#  TESTES: AOIConfigManager - Presets de Câmera
# ============================================================================

class TestAOIConfigManagerPresets:
    """Testes para gerenciamento de presets de câmera."""

    def test_save_camera_preset(self, temp_config_file):
        """Testa salvar preset de câmera."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        preset_data = {
            "brightness": 200,
            "contrast": 130,
            "exposure": -5
        }

        manager.save_camera_preset("bright", preset_data)

        retrieved = manager.get_camera_preset("bright")
        assert retrieved is not None
        assert retrieved["brightness"] == 200

    def test_get_camera_preset_exists(self, temp_config_file):
        """Testa recuperar preset existente."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        preset_data = {"brightness": 150}
        manager.save_camera_preset("dim", preset_data)

        retrieved = manager.get_camera_preset("dim")

        assert retrieved == preset_data

    def test_get_camera_preset_not_exists(self, temp_config_file):
        """Testa recuperar preset inexistente."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        retrieved = manager.get_camera_preset("inexistente")

        assert retrieved is None

    def test_list_camera_presets_empty(self, temp_config_file):
        """Testa listar presets quando não há nenhum."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        presets = manager.list_camera_presets()

        assert presets == []

    def test_list_camera_presets_multiple(self, temp_config_file):
        """Testa listar múltiplos presets."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.save_camera_preset("preset1", {"brightness": 100})
        manager.save_camera_preset("preset2", {"brightness": 200})
        manager.save_camera_preset("preset3", {"brightness": 150})

        presets = manager.list_camera_presets()

        assert len(presets) == 3
        assert "preset1" in presets
        assert "preset2" in presets
        assert "preset3" in presets

    def test_camera_preset_persistence(self, temp_config_file):
        """Testa que presets persistem entre instâncias."""
        manager1 = AOIConfigManager(cfg_path=str(temp_config_file))

        manager1.save_camera_preset("test_preset", {"brightness": 180})

        # Nova instância
        manager2 = AOIConfigManager(cfg_path=str(temp_config_file))

        retrieved = manager2.get_camera_preset("test_preset")
        assert retrieved is not None
        assert retrieved["brightness"] == 180


# ============================================================================
#  TESTES: AOIConfigManager - apply_to_cnc
# ============================================================================

class TestAOIConfigManagerApplyToCNC:
    """Testes para aplicação de configurações ao CNC."""

    def test_apply_to_cnc_connected(self, mock_cnc, temp_config_file):
        """Testa aplicação quando CNC está conectado."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.apply_to_cnc(mock_cnc)

        # Verifica que max_feed foi aplicado
        assert mock_cnc.max_feed["x"] == 2500.0
        assert mock_cnc.max_feed["y"] == 2500.0
        assert mock_cnc.max_feed["z"] == 800.0

        # Verifica pulses_per_mm
        # ppr=400, pitch=5 -> 400/5 = 80
        assert mock_cnc.pulses_per_mm == pytest.approx(80.0, rel=0.1)

    def test_apply_to_cnc_disconnected(self, mock_cnc, temp_config_file):
        """Testa aplicação quando CNC está desconectado."""
        mock_cnc.is_connected = False
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.apply_to_cnc(mock_cnc)

        # Não deve aplicar nada (retorna early)
        # Valores devem permanecer inalterados
        assert mock_cnc.max_feed["x"] == 5000  # Valor original do mock

    def test_apply_to_cnc_none(self, temp_config_file):
        """Testa aplicação com CNC None."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # Não deve lançar exceção
        manager.apply_to_cnc(None)

    def test_apply_to_cnc_custom_calibration(self, mock_cnc, temp_config_file):
        """Testa aplicação com calibração customizada."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # Configura calibração customizada
        manager.set("calibration", "pulses_per_rev", value=800.0)
        manager.set("calibration", "fuso_pitch", value=10.0)

        manager.apply_to_cnc(mock_cnc)

        # ppr=800, pitch=10 -> 800/10 = 80
        assert mock_cnc.pulses_per_mm == pytest.approx(80.0, rel=0.1)

    def test_apply_to_cnc_backlight_coil(self, mock_cnc, temp_config_file):
        """Testa aplicação de endereço do backlight."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.set("connections", "backlight_coil", value=5)

        manager.apply_to_cnc(mock_cnc)

        assert mock_cnc.backlight_coil_address == 5

    def test_apply_to_cnc_no_backlight_attr(self, temp_config_file):
        """Testa aplicação quando CNC não tem atributo backlight."""
        cnc = Mock()
        cnc.is_connected = True
        cnc.max_feed = {"x": 5000, "y": 5000, "z": 800}
        cnc.pulses_per_mm = 80.0
        # Não tem backlight_coil_address

        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # Não deve lançar exceção
        manager.apply_to_cnc(cnc)

    def test_apply_to_cnc_zero_pitch(self, mock_cnc, temp_config_file):
        """Testa aplicação com pitch zero (não divide)."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # Configura pitch inválido
        manager.set("calibration", "fuso_pitch", value=0.0)

        manager.apply_to_cnc(mock_cnc)

        # Não deve aplicar pulses_per_mm (evita divisão por zero)
        # Mantém valor original


# ============================================================================
#  TESTES: AOIConfigManager - Edge Cases
# ============================================================================

class TestAOIConfigManagerEdgeCases:
    """Testes para casos extremos."""

    def test_get_empty_path(self, temp_config_file):
        """Testa get sem nenhum argumento de caminho."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        # get sem argumentos retorna data inteiro
        result = manager.get()

        assert result == manager.data

    def test_set_empty_value(self, temp_config_file):
        """Testa set com valor vazio/None."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.set("test", "key", value=None)

        assert manager.get("test", "key") is None

    def test_overwrite_existing_value(self, temp_config_file):
        """Testa sobrescrever valor existente."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.set("test", "key", value="original")
        assert manager.get("test", "key") == "original"

        manager.set("test", "key", value="novo")
        assert manager.get("test", "key") == "novo"

    def test_special_characters_in_values(self, temp_config_file):
        """Testa valores com caracteres especiais."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        special_value = "Teste com acentuação: çãé"

        manager.set("test", "special", value=special_value)

        assert manager.get("test", "special") == special_value

    def test_numeric_types(self, temp_config_file):
        """Testa tipos numéricos diversos."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.set("test", "int_val", value=42)
        manager.set("test", "float_val", value=3.14159)
        manager.set("test", "neg_val", value=-100)

        assert manager.get("test", "int_val") == 42
        assert manager.get("test", "float_val") == pytest.approx(3.14159)
        assert manager.get("test", "neg_val") == -100

    def test_boolean_types(self, temp_config_file):
        """Testa tipos booleanos."""
        manager = AOIConfigManager(cfg_path=str(temp_config_file))

        manager.set("test", "bool_true", value=True)
        manager.set("test", "bool_false", value=False)

        assert manager.get("test", "bool_true") is True
        assert manager.get("test", "bool_false") is False
