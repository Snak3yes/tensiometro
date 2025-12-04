from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from gerber_viewer.gui.mainwindow import GerberMacroViewer


def main():
    app = QApplication(sys.argv)
    window = GerberMacroViewer()
    window.resize(900, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
