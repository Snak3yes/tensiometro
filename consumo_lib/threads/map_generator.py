from PyQt6.QtCore import QThread, pyqtSignal
from pathlib import Path
import logging

from aoi_lib.config_manager import AOIConfigManager
logger = logging.getLogger(__name__)
class MapGeneratorThread(QThread):
    """
    Thread responsável por percorrer a grade, movimentar a CNC e capturar
    as imagens sem travar a GUI.
    
    Otimizações de velocidade:
    - Movimento direto sem espera inicial desnecessária
    - Delay mínimo de estabilização configurável
    - Usa velocidade já programada no CLP (não sobrescreve registradores)
    """
    progress = pyqtSignal(int, int)       # imagens_capturadas, total
    image_captured = pyqtSignal(object)   # cv2 image (opcional para preview)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, controller, origin, end, sx, sy, folder, prog_name, feed_rate=None, capture_delay_ms=100):
        super().__init__()
        self.ctrl = controller
        self.origin = origin
        self.end = end
        self.sx = sx
        self.sy = sy
        self.folder = folder
        self.prog_name = prog_name
        # Se None, usa a velocidade que já está gravada no CLP sem sobrescrever
        self.feed_rate = feed_rate
        # Delay mínimo de 50ms para estabilização
        self.capture_delay_ms = max(capture_delay_ms, 50)

    def run(self):
        log = logging.getLogger("MapGeneratorThread")
        backlight_was_on = False  # Para restaurar estado original ao final
        
        try:
            points = list(self.ctrl._grid_points(self.origin, self.end,
                                             self.sx, self.sy))
            total = len(points)
            os.makedirs(self.folder, exist_ok=True)

            # Converte delay de ms para segundos
            delay_sec = self.capture_delay_ms / 1000.0
            feed_desc = f"{self.feed_rate}mm/min" if self.feed_rate is not None else "CLP (valor em memórias)"
            log.info(f"MapGeneratorThread: Delay={self.capture_delay_ms}ms, FeedRate={feed_desc}, Total={total} pontos")

            # ========== CONTROLE DO BACKLIGHT - INÍCIO ==========
            # Liga o backlight 2 segundos antes de iniciar as capturas
            if hasattr(self.ctrl.cnc, 'backlight_set'):
                # Salva estado anterior para restaurar depois
                backlight_was_on = getattr(self.ctrl.cnc, 'backlight_on', False)
                
                log.info("MapGeneratorThread: Ligando backlight (Y0.7)")
                self.ctrl.cnc.backlight_turn_on()
                
                # Aguarda 2 segundos para estabilização da iluminação
                log.info("MapGeneratorThread: Aguardando 2s para estabilização do backlight")
                time.sleep(2.0)
            # ========== CONTROLE DO BACKLIGHT - FIM ==========

            # Descarta frames antigos do buffer da câmera antes de iniciar
            for _ in range(3):
                self.ctrl.camera.capture()

            captured = 0
            last_x, last_y = None, None
            
            for r, col, x, y in points:
                if self.isInterruptionRequested():
                    log.warning("Mapa cancelado pelo usuário")
                    # Desliga backlight antes de sair
                    self._turn_off_backlight(log, backlight_was_on)
                    self.error.emit("Operação cancelada")
                    return
                
                # Move apenas se a posição mudou
                need_move = (last_x is None or last_y is None or 
                            abs(x - last_x) > 0.01 or abs(y - last_y) > 0.01)
                
                if need_move:
                    self.ctrl.cnc.move_to_absolute_position(x, y, feed_rate=self.feed_rate)
                    self.ctrl.cnc.wait_for_idle(tolerance=2, timeout=15)
                    last_x, last_y = x, y
                    
                    # Aguarda estabilização apenas se houve movimento
                    if delay_sec > 0:
                        time.sleep(delay_sec)

                # Captura imagem
                img = self.ctrl.camera.capture()
                if img is not None:
                    fname = f"{self.prog_name}_r{r:03d}_c{col:03d}.png"
                    cv2.imwrite(os.path.join(self.folder, fname), img)
                    self.image_captured.emit(img)
                else:
                    log.warning(f"Falha ao capturar imagem em r={r}, c={col}")
                    
                captured += 1
                self.progress.emit(captured, total)

            log.info(f"MapGeneratorThread: Finalizado - {captured} imagens capturadas")
            
            # ========== DESLIGA BACKLIGHT APÓS 2 SEGUNDOS ==========
            self._turn_off_backlight(log, backlight_was_on)
            
            self.finished.emit()
        except Exception as exc:
            log.exception("Erro na geração do mapa")
            # Garante que o backlight seja desligado em caso de erro
            self._turn_off_backlight(log, backlight_was_on)
            self.error.emit(str(exc))
    
    def _turn_off_backlight(self, log, restore_previous_state: bool):
        """
        Desliga o backlight após aguardar 2 segundos.
        
        Args:
            log: Logger para registrar mensagens
            restore_previous_state: Se True, restaura o estado anterior do backlight
        """
        if not hasattr(self.ctrl.cnc, 'backlight_set'):
            return
        
        try:
            # Aguarda 2 segundos antes de desligar
            log.info("MapGeneratorThread: Aguardando 2s antes de desligar backlight")
            time.sleep(2.0)
            
            if restore_previous_state:
                # Restaura estado anterior
                log.info(f"MapGeneratorThread: Restaurando backlight para estado anterior: {'ON' if restore_previous_state else 'OFF'}")
                self.ctrl.cnc.backlight_set(restore_previous_state)
            else:
                # Desliga
                log.info("MapGeneratorThread: Desligando backlight (Y0.7)")
                self.ctrl.cnc.backlight_turn_off()
        except Exception as e:
            log.error(f"MapGeneratorThread: Erro ao controlar backlight: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AOIControllerApp()
    window.show()
    sys.exit(app.exec())


