"""
Módulo: serial_protocol.py
Descrição: Gerencia conexão serial com tensiômetro AS-120N
Protocolo: 2400 baud, 9-byte binary frame, 8N1
"""

import serial
import serial.tools.list_ports
import logging
import time

logger = logging.getLogger(__name__)


class TensiometerSerialManager:
    """
    Gerencia conexão serial dedicada para o tensiômetro.
    Permite configurar porta, baudrate e parâmetros de comunicação.

    Protocolo AS-120N:
    - Request: Single byte 0x20
    - Response: 9 bytes starting with 0x10, byte[2] = 0x19
    - Encoding: Binary with shifted nibbles (+0x0A)
    """

    def __init__(self):
        self.serial_connection = None
        self.is_connected = False
        self.port = None
        self.baudrate = 2400  # Padrão para tensiômetros AS-120N
        self.timeout = 1.0
        self.last_error = ""

        # Parâmetros específicos do AS-120N
        self.REQ_COMMAND = b'\x20'  # Comando de requisição
        self.FRAME_LEN = 9          # Tamanho do frame de resposta
        self.UNIT_MAP = {0x05: "N/cm²", 0x04: "kg/cm²", 0x06: "lb/cm²"}

    def _real_dig(self, b: int) -> int:
        """
        Converte nibble baixo deslocado (+0x0A) em dígito 0–9.

        O protocolo AS-120N usa codificação especial onde os dígitos
        são deslocados por +0x0A. Esta função reverte essa codificação.

        Args:
            b: Byte com nibble codificado

        Returns:
            Dígito decimal 0-9
        """
        return ((b & 0x0F) + 10) % 10

    def _decode_frame(self, frame: bytes) -> float | None:
        """
        Decodifica um frame de 9 bytes do AS-120N.

        Formato do frame:
        - Byte[0]: 0x10 (header)
        - Byte[1]: Unidade (0x05=N/cm², 0x04=kg/cm², 0x06=lb/cm²)
        - Byte[2]: 0x19 (marker)
        - Byte[3]: Flags (bits 4-6 = casas decimais)
        - Byte[6]: Dígito 3 (centenas)
        - Byte[7]: Dígito 2 (dezenas)
        - Byte[8]: Dígito 1 (unidades)

        Args:
            frame: 9 bytes recebidos do tensiômetro

        Returns:
            Valor em float (N/cm²) ou None se frame inválido
        """
        if len(frame) < self.FRAME_LEN or frame[0] != 0x10 or frame[2] != 0x19:
            return None

        # Extrair número de casas decimais dos bits 4-6 do byte 3
        casas = (frame[3] >> 4) & 0x07

        # Extrair dígitos (codificados com offset +0x0A)
        d3 = self._real_dig(frame[6])
        d2 = self._real_dig(frame[7])
        d1 = self._real_dig(frame[8])

        # Montar valor bruto
        raw = d3 * 100 + d2 * 10 + d1

        # Aplicar casas decimais
        return raw / (10 ** casas)

    def get_available_ports(self):
        """
        Retorna lista de portas seriais disponíveis.

        Returns:
            Lista de strings com nomes das portas (ex: ['COM3', 'COM4'])
        """
        try:
            ports = [port.device for port in serial.tools.list_ports.comports()]
            return ports
        except Exception as e:
            logger.error(f"Erro ao listar portas: {e}")
            return []

    def connect(self, port, baudrate=2400, timeout=1.0):
        """
        Conecta ao tensiômetro em uma porta específica.

        Args:
            port: Porta COM (ex: 'COM3', '/dev/ttyUSB0')
            baudrate: Taxa de transmissão (padrão: 2400)
            timeout: Timeout para leitura em segundos

        Returns:
            True se conexão bem-sucedida, False caso contrário
        """
        try:
            # Desconecta se já estiver conectado
            if self.is_connected:
                self.disconnect()

            # Cria nova conexão
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=timeout
            )

            # Configuração específica para AS-120N
            self.serial_connection.dtr = False
            self.serial_connection.rts = False

            self.port = port
            self.baudrate = baudrate
            self.timeout = timeout
            self.is_connected = True
            self.last_error = ""

            logger.info(f"Tensiômetro conectado em {port} @ {baudrate} baud")
            return True

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erro ao conectar tensiômetro: {e}")
            return False

    def disconnect(self):
        """Desconecta do tensiômetro."""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                logger.info("Tensiômetro desconectado")
        except Exception as e:
            logger.error(f"Erro ao desconectar tensiômetro: {e}")
        finally:
            self.serial_connection = None
            self.is_connected = False
            self.port = None

    def read_tension_value(self):
        """
        Lê valor do tensiômetro AS-120N usando protocolo binário.

        Workflow:
        1. Limpa buffer de entrada
        2. Envia comando de requisição (0x20)
        3. Aguarda 50ms
        4. Lê frame de 9 bytes
        5. Decodifica e retorna valor

        Returns:
            str: Valor formatado com 2 casas decimais ou "0" em caso de erro
        """
        if not self.is_connected or not self.serial_connection:
            self.last_error = "Tensiômetro não conectado"
            return "0"

        try:
            # Limpa buffer de entrada
            self.serial_connection.reset_input_buffer()

            # Envia comando de requisição
            self.serial_connection.write(self.REQ_COMMAND)
            self.serial_connection.flush()

            # Aguarda resposta (50ms conforme especificação)
            time.sleep(0.05)

            # Lê frame de resposta (9 bytes exatos)
            raw_data = self.serial_connection.read(self.FRAME_LEN)

            if not raw_data:
                self.last_error = "Sem resposta do tensiômetro"
                return "0"

            if len(raw_data) != self.FRAME_LEN:
                self.last_error = f"Frame incompleto: {len(raw_data)} bytes (esperado: {self.FRAME_LEN})"
                return "0"

            # Decodifica o frame binário
            value = self._decode_frame(raw_data)

            if value is None:
                self.last_error = f"Frame inválido: {raw_data.hex(' ')}"
                return "0"

            # Retorna valor formatado
            return f"{value:.2f}"

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erro ao ler tensiômetro: {e}")
            return "0"

    def send_command(self, command):
        """
        Envia comando ASCII para o tensiômetro (se suportado).

        Args:
            command: Comando ASCII a ser enviado

        Returns:
            True se enviado com sucesso, False caso contrário
        """
        if not self.is_connected or not self.serial_connection:
            return False

        try:
            cmd_bytes = (command + '\r\n').encode('ascii')
            self.serial_connection.write(cmd_bytes)
            self.serial_connection.flush()
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Erro ao enviar comando: {e}")
            return False
