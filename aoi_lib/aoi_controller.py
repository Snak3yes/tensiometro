import time
import os, cv2, time, math, json, logging
from .cnc_controller import GRBLCNCController
from .plc_axis_controller import PLCAxisController
from .camera_controller import CameraController
from .position_manager import InspectionPositionManager, InspectionPosition, InspectionSequence

class CNCAOIController:
    """
    Controlador principal que integra o movimento CNC e captura de imagem
    para aplicações de Inspeção Óptica Automatizada (AOI).
    """
    
    def __init__(self,
                 serial_port=None,
                 camera_interface=None,
                 use_plc=True,
                 plc_host='192.168.1.5',
                 plc_port=502):
        """
        Inicializa o controlador AOI.
        
        Args:
            serial_port: Porta serial para conexão com a CNC (opcional)
            camera_interface: Interface para a câmera (opcional)
        """
        # Seleciona backend de movimento: GRBL ou CLP via Modbus TCP
        if use_plc:
            # cria e conecta no CLP
            self.cnc = PLCAxisController(host=plc_host, port=plc_port)
            # ——— Carrega calibr. mecânica do config (igual ao AdhesiveApp) ———
            from .config_manager import AOIConfigManager
            cfg = AOIConfigManager()
            ppr   = float(cfg.get("calibration", "pulses_per_rev", default=1.0))
            pitch = float(cfg.get("calibration", "fuso_pitch",     default=1.0))
            # cálculo pulses/mm idêntico à das steps/mm:
            self.cnc.pulses_per_mm = ppr / pitch if pitch != 0 else 1.0
        else:
            self.cnc = GRBLCNCController()
        self.camera = CameraController(camera_interface)
        self.position_manager = InspectionPositionManager()
        self.is_running_sequence = False
        self.current_sequence: InspectionSequence | None = None
    
    def __getattr__(self, name):
        """
        Delegates movement methods (step_move, jog_start, move_absolute, etc.)
        to the underlying CNC backend so the UI can call them directly:
            controller.step_move(...), controller.jog_start(...), etc.
        """
        # intercepta chamadas típicas de controle manual
        if hasattr(self.cnc, name):
            return getattr(self.cnc, name)
        # fallback padrão
        raise AttributeError(f"{self.__class__.__name__!r} has no attribute {name!r}")
        
    def connect_cnc(self, port=None, baudrate=115200):
        """Conecta à máquina CNC."""
        return self.cnc.connect(port, baudrate)
    
    def run_gcode_file(self, filename, callback=None):
        """
        Executa um arquivo G-CODE diretamente
        
        Args:
            filename: Caminho do arquivo G-CODE
            callback: Função chamada após cada captura
        """
        from aoi_lib.gcode_manager import GCodeManager
        gcode_manager = GCodeManager()
        
        # Carrega o G-CODE para uma sequência temporária
        gcode_data = gcode_manager.read_gcode_file(filename)
        
        if not gcode_data:
            raise ValueError(f"Erro ao carregar arquivo G-CODE: {filename}")
        
        # Cria posições a partir dos dados do G-CODE
        positions = []
        for pos_data in gcode_data['positions']:
            position = InspectionPosition(
                pos_data['name'],
                pos_data.get('x', 0.0),
                pos_data.get('y', 0.0),
                pos_data.get('z', 0.0),
                pos_data.get('camera_params', {})
            )
            positions.append(position)
        
        # Cria sequência temporária
        temp_sequence = InspectionSequence(gcode_data['sequence_name'])
        for pos in positions:
            temp_sequence.add_position(pos)
        
        # Executa a sequência
        return self.run_sequence(temp_sequence.name, callback)
    
    def disconnect_cnc(self):
        """Desconecta da máquina CNC."""
        # CLP: fecha Modbus
        if isinstance(self.cnc, PLCAxisController):
            self.cnc.close()
            return True
        # GRBL: serial
        if getattr(self.cnc, 'is_connected', False):
            return self.cnc.disconnect()
        return True
        
    def connect_camera(self, camera_id=0):
        """Conecta à câmera."""
        return self.camera.connect(camera_id)
        
    def add_inspection_position(self, name, x, y, z=0.0, camera_params=None):
        """
        Adiciona uma posição de inspeção ao gerenciador.
        
        Args:
            name: Nome descritivo da posição
            x, y: Coordenadas
            camera_params: Parâmetros específicos da câmera (opcional)
        """
        position = InspectionPosition(name, x, y, z, camera_params)
        self.position_manager.add_position(position)
        return position
        
    def add_current_position(self, name, camera_params=None):
        """Adiciona a posição atual como uma posição de inspeção."""
        position = self.cnc.get_current_position()
        return self.add_inspection_position(
            name,
            position['x'],
            position['y'],
            position['z'],
            camera_params
        )
        
    def create_sequence(self, name, positions=None):
        """Cria uma nova sequência de inspeção."""
        sequence = InspectionSequence(name)
        if positions:
            for pos in positions:
                sequence.add_position(pos)
        self.position_manager.add_sequence(sequence)
        return sequence
        
    def run_sequence(self, sequence_name, callback=None):
        """
        Executa uma sequência de inspeção completa.
        
        Args:
            sequence_name: Nome da sequência a executar
            callback: Função chamada após cada captura com imagem e metadados
        """
        sequence = self.position_manager.get_sequence(sequence_name)
        if not sequence:
            raise ValueError(f"Sequência '{sequence_name}' não encontrada")
            
        self.is_running_sequence = True
        self.current_sequence = sequence

        results = []
        for idx, position in enumerate(sequence.positions):
            if not self.is_running_sequence:          # stop_sequence() pode ter sido chamado
                break

            # 1. Move para a posição (X, Y, Z) - despacha para CLP ou GRBL
            feed_rate = getattr(self, '_current_feed_rate', 1000)
            if isinstance(self.cnc, PLCAxisController):
                # Executa o movimento absoluto exato em mm, sem truncar
                # (move_to_absolute_position converte internamente usando pulses_per_mm)
                self.cnc.move_to_absolute_position(
                    x=position.x,
                    y=position.y,
                    z=position.z,
                    feed_rate=feed_rate
                )
                # Aguarda idle de todos os eixos
                self.cnc.wait_for_idle()
            else:
                # comportamento original GRBL
                self.cnc.move_to_absolute_position(
                    position.x, position.y, position.z,
                    feed_rate=feed_rate
                )
                self.cnc.wait_for_idle()

            # 2. Captura a imagem
            image = self.camera.capture(position.camera_params)

            # 3. Monta resultado
            result = {
                "position":   position,
                "image":      image,
                "timestamp":  time.time(),
                "sequence":   sequence.name,
                "index":      idx
            }

            results.append(result)
            if callback:
                callback(result)

        self.is_running_sequence = False
        return results        # opcional, mantido para retro-compat.
    
    def set_feed_rate(self, feed_rate):
        """Define a velocidade de movimentação para sequências"""
        self._current_feed_rate = feed_rate
        
    def stop_sequence(self):
        """Para a execução da sequência atual."""
        self.is_running_sequence = False
        
    def save_positions(self, filename):
        """Salva todas as posições e sequências em um arquivo."""
        return self.position_manager.save_to_file(filename)
        
    def load_positions(self, filename):
        """Carrega posições e sequências de um arquivo."""
        return self.position_manager.load_from_file(filename)
    
    def generate_map(self, origin, end, step_x, step_y, folder, program_name):
        """
        Gera um mapa de captura em grade entre dois cantos definidos.
        Usa math.ceil para garantir que não pule nenhum passo
        e captura exatamente 1 imagem por ponto.
        """
        
        logger = logging.getLogger("CNCAOIController.generate_map")

        # 1) validações básicas
        os.makedirs(folder, exist_ok=True)
        points = list(self._grid_points(origin, end, step_x, step_y))
        cols = max(p[1] for p in points) + 1
        rows = max(p[0] for p in points) + 1
        logger.info("Gerando mapa: %d colunas × %d linhas  (%d pts)",
                    cols, rows, len(points))

        # 4) vai para a origem
        self.cnc.move_to_absolute_position(origin['x'], origin['y'])
        self.cnc.wait_for_idle()

        # 5) percorre a grade
        capture_map = []          # para salvar JSON no final
        # Usar velocidade configurada se disponível
        feed_rate = getattr(self, '_current_feed_rate', 1000)
        for row_idx, col_idx, x, y in points:
            # move + espera
            self.cnc.move_to_absolute_position(x, y, feed_rate=feed_rate)
            self.cnc.wait_for_idle()

            # captura única
            img = self.camera.capture()
            if img is not None:
                fname = f"{program_name}_r{row_idx:03d}_c{col_idx:03d}.png"
                cv2.imwrite(os.path.join(folder, fname), img)
                capture_map.append(
                        {"row": row_idx, "col": col_idx,
                         "x": x, "y": y, "file": fname}
                        )
            else:
                logger.warning("Falha ao capturar em X=%.3f Y=%.3f", x, y)

            # curto delay para estabilizar
            time.sleep(0.05)

        # 6) salva metadados ------------------------------------------------
        try:
            with open(os.path.join(folder, f"{program_name}_map.json"), "w") as fp:
                json.dump(capture_map, fp, indent=2)
        except Exception as jerr:
            logger.error("Falha ao salvar JSON de mapa: %s", jerr)

        logger.info("generate_map: concluído com sucesso.")
    
    @staticmethod
    def _grid_points(origin, end, sx, sy, snake=True):
        """
        Gera tuplas (row, col, x, y) seguindo padrão “zig-zag” (snake) opcional.
        """
        dx = end['x'] - origin['x']
        dy = end['y'] - origin['y']
        if dx <= 0 or dy <= 0:
            raise ValueError("Cantos inválidos (dx/dy devem ser positivos)")
        if sx <= 0 or sy <= 0:
            raise ValueError("Passos sx/sy devem ser > 0")

        cols = int(math.ceil(dx / sx)) + 1
        rows = int(math.ceil(dy / sy)) + 1
        x_pos = [origin['x'] + min(i * sx, dx) for i in range(cols)]
        y_pos = [origin['y'] + min(j * sy, dy) for j in range(rows)]

        for r, y in enumerate(y_pos):
            scan = x_pos if (r % 2 == 0 or not snake) else list(reversed(x_pos))
            for c_idx, x in enumerate(scan):
                col = c_idx if (r % 2 == 0 or not snake) else cols - 1 - c_idx
                yield r, col, x, y

