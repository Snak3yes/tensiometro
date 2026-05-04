from aoi_lib.tensiometer.serial_protocol import TensiometerSerialManager
from aoi_lib.tensiometer import serial_protocol


class _FakeSerialConnection:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.dtr = True
        self.rts = True
        self.is_open = True
        self.written = []
        self.read_data = b""
        self.reset_input_buffer_called = False
        self.flush_called = False

    def reset_input_buffer(self):
        self.reset_input_buffer_called = True

    def write(self, data):
        self.written.append(data)

    def flush(self):
        self.flush_called = True

    def read(self, size):
        return self.read_data

    def close(self):
        self.is_open = False


def _build_frame(decimal_places, digits):
    return bytes([
        0x10,
        0x00,
        0x19,
        decimal_places << 4,
        0x00,
        0x00,
        digits[0],
        digits[1],
        digits[2],
    ])


def test_decode_frame_returns_float_from_valid_as120n_payload():
    manager = TensiometerSerialManager()
    frame = _build_frame(decimal_places=1, digits=(1, 2, 3))

    assert manager._decode_frame(frame) == 12.3


def test_decode_frame_rejects_invalid_header():
    manager = TensiometerSerialManager()
    frame = b"\x00\x00\x00\x10\x00\x00\x01\x02\x03"

    assert manager._decode_frame(frame) is None


def test_get_available_ports_returns_detected_devices(monkeypatch):
    class _Port:
        def __init__(self, device):
            self.device = device

    monkeypatch.setattr(
        serial_protocol.serial.tools.list_ports,
        "comports",
        lambda: [_Port("COM3"), _Port("COM7")],
    )

    manager = TensiometerSerialManager()

    assert manager.get_available_ports() == ["COM3", "COM7"]


def test_connect_and_disconnect_manage_serial_state(monkeypatch):
    created = []

    def _serial_factory(*args, **kwargs):
        connection = _FakeSerialConnection(*args, **kwargs)
        created.append(connection)
        return connection

    monkeypatch.setattr(serial_protocol.serial, "Serial", _serial_factory)

    manager = TensiometerSerialManager()

    assert manager.connect("COM5", baudrate=2400, timeout=2.5) is True
    assert manager.is_connected is True
    assert manager.port == "COM5"
    assert created[0].dtr is False
    assert created[0].rts is False

    manager.disconnect()

    assert manager.is_connected is False
    assert manager.port is None
    assert created[0].is_open is False


def test_read_tension_value_returns_empty_when_not_connected():
    manager = TensiometerSerialManager()

    assert manager.read_tension_value() == ""
    assert manager.last_error == "Nao conectado"


def test_read_tension_value_reads_and_formats_sensor_response(monkeypatch):
    created = []

    def _serial_factory(*args, **kwargs):
        connection = _FakeSerialConnection(*args, **kwargs)
        connection.read_data = _build_frame(decimal_places=2, digits=(1, 2, 3))
        created.append(connection)
        return connection

    monkeypatch.setattr(serial_protocol.serial, "Serial", _serial_factory)
    monkeypatch.setattr(serial_protocol.time, "sleep", lambda _: None)

    manager = TensiometerSerialManager()
    assert manager.connect("COM9") is True

    value = manager.read_tension_value()

    assert value == "1.23"
    assert created[0].reset_input_buffer_called is True
    assert created[0].flush_called is True
    assert created[0].written == [manager.REQ_COMMAND]


def test_read_tension_value_returns_empty_for_incomplete_frame(monkeypatch):
    created = []

    def _serial_factory(*args, **kwargs):
        connection = _FakeSerialConnection(*args, **kwargs)
        connection.read_data = b"\x10\x00"
        created.append(connection)
        return connection

    monkeypatch.setattr(serial_protocol.serial, "Serial", _serial_factory)
    monkeypatch.setattr(serial_protocol.time, "sleep", lambda _: None)

    manager = TensiometerSerialManager()
    assert manager.connect("COM4") is True

    assert manager.read_tension_value() == ""
    assert manager.last_error == "Frame incompleto"
