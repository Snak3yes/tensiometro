"""
Testes unitários para PLCConnectionManager

Testa gerenciamento de conexão Modbus TCP.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from aoi_lib.plc.controllers.plc_connection_manager import PLCConnectionManager


class TestPLCConnectionManager:
    """Testes para PLCConnectionManager"""

    def test_init_default_params(self):
        """Testa inicialização com parâmetros padrão"""
        manager = PLCConnectionManager("192.168.1.5", 502)

        assert manager.host == "192.168.1.5"
        assert manager.port == 502
        assert manager.slave_id == 1
        assert manager.response_timeout == 5.0
        assert manager.is_connected() == False
        assert manager.client is not None

    def test_init_custom_params(self):
        """Testa inicialização com parâmetros customizados"""
        manager = PLCConnectionManager(
            host="192.168.1.10",
            port=503,
            slave_id=2,
            response_timeout=10.0
        )

        assert manager.host == "192.168.1.10"
        assert manager.port == 503
        assert manager.slave_id == 2
        assert manager.response_timeout == 10.0

    def test_connect_success(self):
        """Testa conexão bem-sucedida ao PLC"""
        manager = PLCConnectionManager("192.168.1.5", 502)

        # Mock do cliente Modbus
        manager.client.connect = Mock(return_value=True)

        result = manager.connect()

        assert result == True
        assert manager.is_connected() == True
        manager.client.connect.assert_called_once()

    def test_connect_failure(self):
        """Testa falha na conexão ao PLC"""
        manager = PLCConnectionManager("192.168.1.5", 502)

        # Mock do cliente Modbus retornando False
        manager.client.connect = Mock(return_value=False)

        result = manager.connect()

        assert result == False
        assert manager.is_connected() == False

    def test_disconnect_when_connected(self):
        """Testa desconexão quando está conectado"""
        manager = PLCConnectionManager("192.168.1.5", 502)
        manager._is_connected = True

        # Mock do cliente Modbus
        manager.client.close = Mock()

        manager.disconnect()

        assert manager.is_connected() == False
        manager.client.close.assert_called_once()

    def test_disconnect_when_not_connected(self):
        """Testa desconexão quando não está conectado"""
        manager = PLCConnectionManager("192.168.1.5", 502)
        manager._is_connected = False

        # Mock do cliente Modbus
        manager.client.close = Mock()

        manager.disconnect()

        # Não deve chamar close se não estiver conectado
        manager.client.close.assert_not_called()

    def test_set_connection_params_when_connected(self):
        """Testa mudança de parâmetros quando conectado (reconecta)"""
        manager = PLCConnectionManager("192.168.1.5", 502)
        manager._is_connected = True

        # Mock dos métodos
        manager.disconnect = Mock()
        manager.connect = Mock(return_value=True)

        manager.set_connection_params(slave_id=3, response_timeout=8.0)

        assert manager.slave_id == 3
        assert manager.response_timeout == 8.0
        manager.disconnect.assert_called_once()
        manager.connect.assert_called_once()

    def test_set_connection_params_when_disconnected(self):
        """Testa mudança de parâmetros quando desconectado"""
        manager = PLCConnectionManager("192.168.1.5", 502)
        manager._is_connected = False

        manager.set_connection_params(slave_id=5, response_timeout=12.0)

        assert manager.slave_id == 5
        assert manager.response_timeout == 12.0

    def test_get_connection_info(self):
        """Testa obtenção de informações de conexão"""
        manager = PLCConnectionManager(
            host="192.168.1.20",
            port=505,
            slave_id=4,
            response_timeout=15.0
        )
        manager._is_connected = True

        info = manager.get_connection_info()

        assert info['host'] == "192.168.1.20"
        assert info['port'] == 505
        assert info['slave_id'] == 4
        assert info['response_timeout'] == 15.0
        assert info['is_connected'] == True
