from PyQt6.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger(__name__)
class SequenceRunnerThread(QThread):
    """Thread para executar uma sequência de inspeção"""
    image_captured = pyqtSignal(dict)  # Emite resultados da captura
    sequence_completed = pyqtSignal()  # Emite quando a sequência é concluída
    sequence_error = pyqtSignal(str)   # Emite quando ocorre um erro
    
    def __init__(self, controller, sequence_name):
        super().__init__()
        self.controller = controller
        self.sequence_name = sequence_name
        
    def run(self):
        try:
            # Execute a sequência e processe os resultados
            def process_result(result):
                self.image_captured.emit(result)
                
            self.controller.run_sequence(self.sequence_name, process_result)
            self.sequence_completed.emit()
            
        except Exception as e:
            self.sequence_error.emit(str(e))



