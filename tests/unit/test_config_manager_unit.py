
import pytest
import json
from unittest.mock import patch, mock_open
from aoi_lib.config_manager import AOIConfigManager

def test_load_failure_uses_defaults():
    """Testa que falha no carregamento (ex: permissão negada) usa a config padrão."""
    with patch("builtins.open", side_effect=PermissionError("Acesso Negado")):
        with patch("pathlib.Path.exists", return_value=True):
            manager = AOIConfigManager(cfg_path="/dummy/path.json")
            # Deve ter carregado o default
            assert manager.get("cnc", "system_type") == "cartesian"
            assert manager.data == AOIConfigManager._DEFAULT_CFG

def test_save_failure_logs_error(caplog):
    """Testa que falha no salvamento loga o erro mas não explode."""
    manager = AOIConfigManager(cfg_path="/dummy/path.json")
    with patch("builtins.open", side_effect=IOError("Disco Cheio")):
        manager.save()
        assert "Erro salvando config: Disco Cheio" in caplog.text

def test_default_path_is_correct():

    """Testa que o caminho padrão é resolvido corretamente para config/aoi_config.json."""

    manager = AOIConfigManager()

    assert manager.cfg_path.name == "aoi_config.json"

    assert manager.cfg_path.parent.name == "config"



def test_modification_does_not_affect_default_cfg():

    """Testa que a modificação da instância não altera o dicionário _DEFAULT_CFG original (deep copy test)."""

    manager = AOIConfigManager(cfg_path="/non/existent/path.json")

    # Modifica um valor aninhado

    manager.set("cnc", "system_type", value="MODIFIED")

    

    # Cria novo manager (que deve usar o default novamente)

    manager2 = AOIConfigManager(cfg_path="/another/non/existent/path.json")

    assert manager2.get("cnc", "system_type") == "cartesian"

    assert AOIConfigManager._DEFAULT_CFG["cnc"]["system_type"] == "cartesian"





