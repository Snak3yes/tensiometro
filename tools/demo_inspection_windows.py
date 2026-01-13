"""
Demo script for Inspection Windows Widget.

This script demonstrates the integration between GerberParser and InspectionWindowsWidget.
Run with: python tools/demo_inspection_windows.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from PyQt6.QtCore import Qt

from consumo_lib.models.inspection_window import (
    InspectionWindow,
    WindowConfig,
    WindowGroup,
    create_groups_from_windows,
    create_default_config
)


class MockGerberObject:
    """Mock GerberObject for testing without actual Gerber files."""

    def __init__(self, obj_id, x, y, kind, **params):
        self.id = obj_id
        self.x_mm = x
        self.y_mm = y
        self.kind = kind
        self.params = params
        self.polygon_mm = []


def create_mock_gerber_objects():
    """Create mock Gerber objects for demonstration."""
    objects = []

    # 10 circles of 0.5mm
    for i in range(10):
        obj = MockGerberObject(
            obj_id=i,
            x_mm=float(i * 5),
            y_mm=10.0,
            kind="flash_circle",
            dia_mm=0.5
        )
        objects.append(obj)

    # 8 circles of 0.8mm
    for i in range(8):
        obj = MockGerberObject(
            obj_id=10 + i,
            x_mm=float(i * 6),
            y_mm=20.0,
            kind="flash_circle",
            dia_mm=0.8
        )
        objects.append(obj)

    # 6 rectangles of 1.0x0.5mm
    for i in range(6):
        obj = MockGerberObject(
            obj_id=18 + i,
            x_mm=float(i * 7),
            y_mm=30.0,
            kind="flash_rect",
            width_mm=1.0,
            height_mm=0.5
        )
        objects.append(obj)

    # 3 ovals of 0.8x1.2mm (exceptions candidates)
    for i in range(3):
        obj = MockGerberObject(
            obj_id=24 + i,
            x_mm=float(i * 8),
            y_mm=40.0,
            kind="flash_oval",
            width_mm=0.8,
            height_mm=1.2
        )
        objects.append(obj)

    return objects


def main():
    """Run demo application."""
    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Inspection Windows Widget - Demo")
    window.resize(1200, 800)

    # Create central widget
    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)

    # Info label
    info_label = QPushButton("ℹ️ Demo: Carregar dados mock do Gerber")
    info_label.clicked.connect(lambda: show_demo_info(layout))
    layout.addWidget(info_label)

    # Import widget
    from consumo_lib.widgets.engenharia.inspection_windows_widget import (
        InspectionWindowsWidget
    )

    # Create inspection windows widget
    inspector_widget = InspectionWindowsWidget()
    layout.addWidget(inspector_widget)

    # Load mock data
    gerber_objects = create_mock_gerber_objects()
    inspector_widget.load_from_gerber(gerber_objects)

    # Status bar
    window.statusBar().showMessage(
        f"✅ Carregadas {len(gerber_objects)} janelas do Gerber (mock)"
    )

    window.show()

    print("🚀 Inspection Windows Widget Demo")
    print("=" * 60)
    print(f"Mock objects created: {len(gerber_objects)}")
    print(f"Groups created: {len(inspector_widget.get_groups())}")
    print(f"Validation status: {inspector_widget.validate()}")
    print("=" * 60)

    return app.exec()


def show_demo_info(layout):
    """Show demo information."""
    info_text = """
    <h2>🎯 Inspection Windows Widget - Demo</h2>

    <p><b>Dados Carregados (Mock):</b></p>
    <ul>
        <li>10 círculos de 0.5mm</li>
        <li>8 círculos de 0.8mm</li>
        <li>6 retângulos de 1.0x0.5mm</li>
        <li>3 ovals de 0.8x1.2mm</li>
        <li><b>Total: 27 janelas</b></li>
    </ul>

    <p><b>Funcionalidades Disponíveis:</b></p>
    <ul>
        <li>📦 Visualização de grupos hierárquica</li>
        <li>⚙️ Configuração de thresholds (OK, PARTIAL, BLOQUEADO)</li>
        <li>🔄 Binarização (Otsu, Adaptativo, Fixed)</li>
        <li>👁️ Preview visual de 3 exemplos por grupo</li>
        <li>💾 Biblioteca de configurações</li>
        <li>✅ Confirmação de grupos</li>
    </ul>

    <p><b>Fluxo Sugerido:</b></p>
    <ol>
        <li>Selecione um grupo na árvore (esquerda)</li>
        <li>Ajuste configuração no painel direito</li>
        <li>Clique "Confirmar Grupo" para aplicar</li>
        <li>Clique "Salvar na Biblioteca" para reuso</li>
        <li>Repita para outros grupos</li>
    </ol>

    <p><b>Status Icons:</b></p>
    <ul>
        <li>⚪ = Não configurado</li>
        <li>🟢 = Configurado (aguardando confirmação)</li>
        <li>✅ = Confirmado (pronto para inspeção)</li>
    </ul>
    """

    from PyQt6.QtWidgets import QMessageBox
    QMessageBox.information(
        None,
        "Demo Info",
        info_text
    )


if __name__ == "__main__":
    sys.exit(main())
