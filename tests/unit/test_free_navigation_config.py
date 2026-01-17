"""
Testes unitários para configuração de navegação livre do Engineering Wizard.

Este módulo testa os métodos de configuração para habilitar/desabilitar
o modo de navegação livre no Engineering Wizard.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-17
"""

import pytest
import json
import tempfile
from pathlib import Path
from aoi_lib.config_manager import AOIConfigManager


class TestFreeNavigationConfig:
    """Testes para configuração de navegação livre."""

    def test_get_free_navigation_enabled_when_true(self):
        """
        Testa get_free_navigation_enabled() quando configurado como True.
        """
        # Arrange: Criar config com free_navigation_enabled=True
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "engineering_wizard": {
                    "free_navigation_enabled": True
                }
            }
            json.dump(config_data, f)
            temp_path = f.name

        try:
            # Act: Carregar config e consultar valor
            cfg = AOIConfigManager(cfg_path=temp_path)
            result = cfg.get_free_navigation_enabled()

            # Assert: Deve retornar True
            assert result is True, "Deve retornar True quando configurado como True"
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

    def test_get_free_navigation_enabled_when_false(self):
        """
        Testa get_free_navigation_enabled() quando configurado como False.
        """
        # Arrange: Criar config com free_navigation_enabled=False
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "engineering_wizard": {
                    "free_navigation_enabled": False
                }
            }
            json.dump(config_data, f)
            temp_path = f.name

        try:
            # Act: Carregar config e consultar valor
            cfg = AOIConfigManager(cfg_path=temp_path)
            result = cfg.get_free_navigation_enabled()

            # Assert: Deve retornar False
            assert result is False, "Deve retornar False quando configurado como False"
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

    def test_get_free_navigation_enabled_when_key_missing(self):
        """
        Testa get_free_navigation_enabled() quando chave não existe (default: False).
        """
        # Arrange: Criar config sem a seção engineering_wizard
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "authentication": {
                    "require_login_on_startup": False
                }
            }
            json.dump(config_data, f)
            temp_path = f.name

        try:
            # Act: Carregar config e consultar valor
            cfg = AOIConfigManager(cfg_path=temp_path)
            result = cfg.get_free_navigation_enabled()

            # Assert: Deve retornar False (default)
            assert result is False, "Deve retornar False (default) quando chave não existe"
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

    def test_set_free_navigation_enabled_and_persistence(self):
        """
        Testa set_free_navigation_enabled() e persistência da configuração.
        """
        # Arrange: Criar config temporária
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {}
            json.dump(config_data, f)
            temp_path = f.name

        try:
            # Act: Habilitar free navigation
            cfg = AOIConfigManager(cfg_path=temp_path)
            cfg.set_free_navigation_enabled(True)

            # Assert: Verificar que foi salvo
            # Recarregar do arquivo
            cfg2 = AOIConfigManager(cfg_path=temp_path)
            result = cfg2.get_free_navigation_enabled()
            assert result is True, "Deve persistir valor True após recarregar"

            # Act: Desabilitar
            cfg2.set_free_navigation_enabled(False)

            # Assert: Verificar que foi salvo
            cfg3 = AOIConfigManager(cfg_path=temp_path)
            result2 = cfg3.get_free_navigation_enabled()
            assert result2 is False, "Deve persistir valor False após recarregar"

            # Verificar que arquivo foi modificado
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            assert "engineering_wizard" in saved_data, "Seção engineering_wizard deve existir"
            assert "free_navigation_enabled" in saved_data["engineering_wizard"], "Chave free_navigation_enabled deve existir"
            assert saved_data["engineering_wizard"]["free_navigation_enabled"] is False, "Valor no arquivo deve ser False"
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)

    def test_set_free_navigation_enabled_with_existing_config(self):
        """
        Testa set_free_navigation_enabled() quando já existe a seção engineering_wizard.
        """
        # Arrange: Criar config com engineering_wizard já existente
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "engineering_wizard": {
                    "free_navigation_enabled": False,
                    "last_used_mode": "normal"
                },
                "authentication": {
                    "require_login_on_startup": True
                }
            }
            json.dump(config_data, f)
            temp_path = f.name

        try:
            # Act: Alterar free_navigation_enabled
            cfg = AOIConfigManager(cfg_path=temp_path)
            cfg.set_free_navigation_enabled(True)

            # Assert: Verificar que outras chaves foram preservadas
            cfg2 = AOIConfigManager(cfg_path=temp_path)
            assert cfg2.get_free_navigation_enabled() is True, "free_navigation_enabled deve ser True"
            assert cfg2.get("engineering_wizard", "last_used_mode") == "normal", "last_used_mode deve ser preservado"
            assert cfg2.get("authentication", "require_login_on_startup") is True, "Outras seções devem ser preservadas"
        finally:
            # Cleanup
            Path(temp_path).unlink(missing_ok=True)
