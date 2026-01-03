from contextlib import contextmanager
from PyQt6.QtCore import QSignalBlocker
class _PreviewSuspender:
    """
    Context-manager que pausa o preview da câmera e garante reativação
    mesmo em caso de exceções.
    """
    def __init__(self, preview_widget):
        self.preview_widget = preview_widget
        self.was_running   = preview_widget and preview_widget.preview_timer.isActive()

    def __enter__(self):
        if self.was_running:
            self.preview_widget.stop_preview()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.was_running:
            self.preview_widget.start_preview()



