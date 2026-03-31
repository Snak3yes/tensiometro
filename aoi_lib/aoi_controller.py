"""
Controlador principal para Inspeção Óptica Automatizada (AOI).
Versão Industrial - Exclusivamente via CLP (Modbus TCP).

Removido suporte a GRBL/Arduino (versão anterior).
"""
import time
import os, cv2, math, json, logging
from .plc_axis_controller import PLCAxisController
from .camera_controller import CameraController
from .position_manager import InspectionPositionManager, InspectionPosition, InspectionSequence


class CNCAOIController:
    """
    Controlador principal que integra o movimento CNC (via CLP) e captura de imagem
    para aplicações de Inspeção Óptica Automatizada (AOI).
    
    Esta versão utiliza exclusivamente comunicação Modbus TCP com CLP industrial.
    """
    
    def __init__(self,
                 camera_interface=None,
                 plc_host='192.168.1.5',
                 plc_port=502,
                 auto_connect=True):
        """
        Inicializa o controlador AOI.
        
        Args:
            camera_interface: Interface para a câmera (opcional)
            plc_host: Endereço IP do CLP (padrão: 192.168.1.5)
            plc_port: Porta Modbus TCP (padrão: 502)
            auto_connect: Se True, conecta automaticamente ao CLP. Se False,
                          a conexão deve ser feita manualmente.
        """
        # Backend de movimento via CLP (Modbus TCP)
        self.cnc = PLCAxisController(host=plc_host, port=plc_port, auto_connect=auto_connect)
        
        # Carrega calibração mecânica do config
        from .config_manager import AOIConfigManager
        cfg = AOIConfigManager()
        ppr   = float(cfg.get("calibration", "pulses_per_rev", default=1.0))
        pitch = float(cfg.get("calibration", "fuso_pitch",     default=1.0))
        # Cálculo pulses/mm: valores não positivos são inválidos e causam inversão indevida.
        if ppr > 0 and pitch > 0:
            self.cnc.pulses_per_mm = ppr / pitch
        else:
            logging.warning(
                "Calibracao invalida para PLC (pulses_per_rev=%s, fuso_pitch=%s). "
                "Usando fallback pulses_per_mm=1.0",
                ppr,
                pitch,
            )
            self.cnc.pulses_per_mm = 1.0
        
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
    
    def connect(self):
        """
        Conecta ao CLP.
        Nota: A conexão é feita automaticamente no __init__.
        Este método existe para compatibilidade de API.
        """
        return self.cnc.is_connected
    
    def disconnect(self):
        """Desconecta do CLP."""
        self.cnc.close()
        return True
    
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

            # Move para a posição (X, Y, Z) via CLP
            feed_rate = getattr(self, '_current_feed_rate', None)
            self.cnc.move_to_absolute_position(
                x=position.x,
                y=position.y,
                z=position.z,
                feed_rate=feed_rate
            )
            # Aguarda idle de todos os eixos
            self.cnc.wait_for_idle()

            # Captura a imagem
            image = self.camera.capture(position.camera_params)

            # Monta resultado
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
        return results
    
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

        # Validações básicas
        os.makedirs(folder, exist_ok=True)
        points = list(self._grid_points(origin, end, step_x, step_y))
        cols = max(p[1] for p in points) + 1
        rows = max(p[0] for p in points) + 1
        logger.info("Gerando mapa: %d colunas × %d linhas  (%d pts)",
                    cols, rows, len(points))

        # Vai para a origem
        self.cnc.move_to_absolute_position(origin['x'], origin['y'])
        self.cnc.wait_for_idle()

        # Percorre a grade
        capture_map = []
        feed_rate = getattr(self, '_current_feed_rate', None)
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

        # Salva metadados
        try:
            with open(os.path.join(folder, f"{program_name}_map.json"), "w") as fp:
                json.dump(capture_map, fp, indent=2)
        except Exception as jerr:
            logger.error("Falha ao salvar JSON de mapa: %s", jerr)

        logger.info("generate_map: concluído com sucesso.")
    
    @staticmethod
    def calculate_adjusted_steps(origin: dict, end: dict, step_x: float, step_y: float) -> dict:
        """
        Calcula os passos ajustados para dividir a distância igualmente.
        
        Quando a distância total (dx ou dy) não é múltiplo exato do passo,
        recalcula o passo para que todas as imagens tenham sobreposição uniforme.
        
        Args:
            origin: {'x': float, 'y': float} - Ponto de origem
            end: {'x': float, 'y': float} - Ponto final
            step_x: Passo desejado em X (mm)
            step_y: Passo desejado em Y (mm)
            
        Returns:
            {
                'step_x': float,           # Passo X ajustado
                'step_y': float,           # Passo Y ajustado
                'cols': int,               # Número de colunas
                'rows': int,               # Número de linhas
                'total_images': int,       # Total de imagens
                'dx': float,               # Distância total X
                'dy': float,               # Distância total Y
                'adjusted_x': bool,        # Se X foi ajustado
                'adjusted_y': bool         # Se Y foi ajustado
            }
        """
        dx = end['x'] - origin['x']
        dy = end['y'] - origin['y']

        # Usa valor absoluto para permitir qualquer direção de medição
        dx_abs = abs(dx)
        dy_abs = abs(dy)

        if dx_abs <= 0 or dy_abs <= 0:
            raise ValueError("Cantos inválidos (dx/dy devem ser não-zero)")
        if step_x <= 0 or step_y <= 0:
            raise ValueError("Passos devem ser > 0")

        # Calcula número de passos necessários (arredonda para cima)
        n_steps_x = int(math.ceil(dx_abs / step_x))
        n_steps_y = int(math.ceil(dy_abs / step_y))
        
        # Garante pelo menos 1 passo
        n_steps_x = max(n_steps_x, 1)
        n_steps_y = max(n_steps_y, 1)
        
        # Recalcula o passo para dividir igualmente
        adjusted_step_x = dx / n_steps_x
        adjusted_step_y = dy / n_steps_y
        
        # Número de imagens = passos + 1 (inclui origem e fim)
        cols = n_steps_x + 1
        rows = n_steps_y + 1
        
        return {
            'step_x': adjusted_step_x,
            'step_y': adjusted_step_y,
            'cols': cols,
            'rows': rows,
            'total_images': cols * rows,
            'dx': dx,
            'dy': dy,
            'adjusted_x': abs(adjusted_step_x - step_x) > 0.001,
            'adjusted_y': abs(adjusted_step_y - step_y) > 0.001,
            'original_step_x': step_x,
            'original_step_y': step_y
        }

    @staticmethod
    def _grid_points(origin, end, sx, sy, snake=True, auto_adjust=True):
        """
        Gera tuplas (row, col, x, y) seguindo padrão "zig-zag" (snake) opcional.
        
        Args:
            origin: {'x': float, 'y': float} - Ponto de origem
            end: {'x': float, 'y': float} - Ponto final
            sx: Passo em X (mm)
            sy: Passo em Y (mm)
            snake: Se True, usa padrão zig-zag para otimizar movimento
            auto_adjust: Se True, ajusta passos para divisão uniforme
        """
        dx = end['x'] - origin['x']
        dy = end['y'] - origin['y']

        # Usa valor absoluto para permitir qualquer direção de medição
        dx_abs = abs(dx)
        dy_abs = abs(dy)

        if dx_abs <= 0 or dy_abs <= 0:
            raise ValueError("Cantos inválidos (dx/dy devem ser não-zero)")
        if sx <= 0 or sy <= 0:
            raise ValueError("Passos sx/sy devem ser > 0")

        if auto_adjust:
            # Usa cálculo ajustado para divisão uniforme
            adjusted = CNCAOIController.calculate_adjusted_steps(origin, end, sx, sy)
            sx = adjusted['step_x']
            sy = adjusted['step_y']
            cols = adjusted['cols']
            rows = adjusted['rows']
        else:
            # Comportamento antigo (mantido para compatibilidade)
            # Usa dx_abs/dy_abs para permitir medição em qualquer direção
            cols = int(math.ceil(dx_abs / sx)) + 1
            rows = int(math.ceil(dy_abs / sy)) + 1
        
        # Gera posições com espaçamento uniforme
        x_pos = [origin['x'] + i * sx for i in range(cols)]
        y_pos = [origin['y'] + j * sy for j in range(rows)]
        
        # Garante que o último ponto seja exatamente o end
        x_pos[-1] = end['x']
        y_pos[-1] = end['y']

        for r, y in enumerate(y_pos):
            scan = x_pos if (r % 2 == 0 or not snake) else list(reversed(x_pos))
            for c_idx, x in enumerate(scan):
                col = c_idx if (r % 2 == 0 or not snake) else cols - 1 - c_idx
                yield r, col, x, y
