"""
 safety_check.py
 Checklist de Segurança – Interface PyQt6 para verificar acionamento de cortinas.
 Memórias do CLP:
  - M23: Cortina Mesa 2
  - M24: Cortina Mesa 1

 Ao abrir:
  • Indicadores iniciam em OFF.
  • Usuário aciona manualmente as cortinas.
  • A cada poll, lê-se M23/M24 via Modbus e atualiza-se o indicador.
  • Botão 'Resetar' volta ambos para OFF.
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMessageBox, QFrame
)
from PyQt6.QtCore import QTimer, Qt
from pymodbus.client import ModbusTcpClient


class SafetyCheckApp(QWidget):
    def __init__(self,
                 plc_host: str = "192.168.1.5",
                 plc_port: int = 502,
                 poll_interval: int = 500  # ms
                 ):
        super().__init__()
        self.setWindowTitle("Checklist de Segurança")
        self.resize(320, 150)

        # Conecta ao CLP via Modbus TCP
        self.plc = ModbusTcpClient(plc_host, port=plc_port)
        if not self.plc.connect():
            QMessageBox.critical(
                self, "Erro de Conexão",
                f"Não foi possível conectar ao CLP em {plc_host}:{plc_port}"
            )

        # Monta UI com LEDs e descrições
        vbox = QVBoxLayout(self)

        # M23 – Cortina Mesa 2
        h_m23 = QHBoxLayout()
        self.led_m23 = QFrame(self)
        self.led_m23.setFixedSize(16, 16)
        self.led_m23.setStyleSheet(self._led_off_style())
        h_m23.addWidget(self.led_m23)
        self.lbl_m23 = QLabel("Cortina Mesa 2 (M23)", self)
        h_m23.addWidget(self.lbl_m23)
        # Indicador em tempo real M23
        self.rt_led_m23 = QFrame(self)
        self.rt_led_m23.setFixedSize(16, 16)
        self.rt_led_m23.setStyleSheet(self._led_off_style())
        h_m23.addWidget(self.rt_led_m23)
        vbox.addLayout(h_m23)

        # M24 – Cortina Mesa 1
        h_m24 = QHBoxLayout()
        self.led_m24 = QFrame(self)
        self.led_m24.setFixedSize(16, 16)
        self.led_m24.setStyleSheet(self._led_off_style())
        h_m24.addWidget(self.led_m24)
        self.lbl_m24 = QLabel("Cortina Mesa 1 (M24)", self)
        h_m24.addWidget(self.lbl_m24)
        # Indicador em tempo real M24
        self.rt_led_m24 = QFrame(self)
        self.rt_led_m24.setFixedSize(16, 16)
        self.rt_led_m24.setStyleSheet(self._led_off_style())
        h_m24.addWidget(self.rt_led_m24)
        vbox.addLayout(h_m24)

        # M25 – Porta de Segurança / E-Stop
        h_m25 = QHBoxLayout()
        self.led_m25 = QFrame(self)
        self.led_m25.setFixedSize(16, 16)
        self.led_m25.setStyleSheet(self._led_off_style())
        h_m25.addWidget(self.led_m25)
        self.lbl_m25 = QLabel("Porta de Segurança/E-Stop (M25)", self)
        h_m25.addWidget(self.lbl_m25)
        # Indicador em tempo real M25
        self.rt_led_m25 = QFrame(self)
        self.rt_led_m25.setFixedSize(16, 16)
        self.rt_led_m25.setStyleSheet(self._led_off_style())
        h_m25.addWidget(self.rt_led_m25)
        vbox.addLayout(h_m25)
        # Flags para manter indicador acionado após primeiro disparo
        self.m23_ok = False
        self.m24_ok = False
        self.m25_ok = False

        # Botões de controle
        hbox = QHBoxLayout()
        btn_reset = QPushButton("Resetar", self)
        btn_reset.clicked.connect(self.reset_indicators)
        btn_quit = QPushButton("Sair", self)
        btn_quit.clicked.connect(self.close)
        hbox.addWidget(btn_reset)
        hbox.addWidget(btn_quit)
        vbox.addLayout(hbox)

        # Timer para polling periódico
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_states)
        self.timer.start(poll_interval)

    def _on_style(self) -> str:
        # não utilizado para LEDs
        return ""

    def _off_style(self) -> str:
        # não utilizado para LEDs
        return ""

    def _led_on_style(self) -> str:
        return "QFrame { background-color: green; border-radius: 8px; }"

    def _led_off_style(self) -> str:
       return "QFrame { background-color: red; border-radius: 8px; }"

    def update_states(self):
        """
        Lê M23 e M24 (coils 23/24) do CLP e atualiza os indicadores.
        """
        for mem, label, nome in (
                (23, self.lbl_m23, "Cortina Mesa 2"),
                (24, self.lbl_m24, "Cortina Mesa 1"),
                (25, self.lbl_m25, "Porta de Segurança/E-Stop"),
        ):
            try:
                res = self.plc.read_coils(mem, count=1)
                # atualiza indicador em tempo real
                rt_led = getattr(self, f"rt_led_m{mem}")
                if not res.isError() and res.bits[0]:
                    rt_led.setStyleSheet(self._led_on_style())
                else:
                    rt_led.setStyleSheet(self._led_off_style())
                # se disparou ao menos uma vez, fixa OK
                if not res.isError() and res.bits[0]:
                    if mem == 23:
                        self.m23_ok = True
                    elif mem == 24:
                        self.m24_ok = True
                    else:  # mem == 25
                        self.m25_ok = True

                # exibe conforme flag persistente
                if mem == 23:
                    flag = self.m23_ok
                elif mem == 24:
                    flag = self.m24_ok
                else:
                    flag = self.m25_ok
                # atualiza cor do LED permanente conforme flag
                led = getattr(self, f"led_m{mem}")
                if flag:
                    led.setStyleSheet(self._led_on_style())
                else:
                    led.setStyleSheet(self._led_off_style())
            except Exception:
                # em caso de erro, zera indicador em tempo real
                getattr(self, f"rt_led_m{mem}").setStyleSheet(self._led_off_style())
                label.setText(f"{nome} (M{mem}): ERRO")
                label.setStyleSheet(self._off_style())

    def reset_indicators(self):
        """
        Volta ambos os indicadores para estado OFF.
        """
        # reseta flags e mostra todos em OFF
        self.m23_ok = False
        self.m24_ok = False
        self.m25_ok = False
        # reseta LEDs para estado OFF (vermelho)
        self.led_m23.setStyleSheet(self._led_off_style())
        self.led_m24.setStyleSheet(self._led_off_style())
        self.led_m25.setStyleSheet(self._led_off_style())

    def closeEvent(self, event):
        # Fecha conexão Modbus ao sair
        try:
            self.plc.close()
        except Exception as e:
            print(f'Erro ao fechar conexão Modbus: {e}')
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = SafetyCheckApp()
    win.show()
    sys.exit(app.exec())
