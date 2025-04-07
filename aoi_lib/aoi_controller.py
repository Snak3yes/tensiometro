import time
from .cnc_controller import GRBLCNCController
from .camera_controller import CameraController
from .position_manager import InspectionPositionManager, InspectionPosition, InspectionSequence

class CNCAOIController:
    """
    Controlador principal que integra o movimento CNC e captura de imagem
    para aplicações de Inspeção Óptica Automatizada (AOI).
    """
    
    def __init__(self, serial_port=None, camera_interface=None):
        """
        Inicializa o controlador AOI.
        
        Args:
            serial_port: Porta serial para conexão com a CNC (opcional)
            camera_interface: Interface para a câmera (opcional)
        """
        self.cnc = GRBLCNCController()
        self.camera = CameraController(camera_interface)
        self.position_manager = InspectionPositionManager()
        self.is_running_sequence = False
        self.current_sequence = None
        self.current_position_index = -1
        
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
                pos_data['x'], 
                pos_data['y'],
                pos_data['camera_params']
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
        if self.cnc.is_connected:
            return self.cnc.disconnect()
        return True
        
    def connect_camera(self, camera_id=0):
        """Conecta à câmera."""
        return self.camera.connect(camera_id)
        
    def add_inspection_position(self, name, x, y, camera_params=None):
        """
        Adiciona uma posição de inspeção ao gerenciador.
        
        Args:
            name: Nome descritivo da posição
            x, y: Coordenadas
            camera_params: Parâmetros específicos da câmera (opcional)
        """
        position = InspectionPosition(name, x, y, camera_params)
        self.position_manager.add_position(position)
        return position
        
    def add_current_position(self, name, camera_params=None):
        """Adiciona a posição atual como uma posição de inspeção."""
        position = self.cnc.get_current_position()
        return self.add_inspection_position(name, position['x'], position['y'], camera_params)
        
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
        self.current_position_index = 0
        
        # Iniciar execução da sequência
        return self._process_next_position(callback)
        
    def _process_next_position(self, callback=None):
        """Processa a próxima posição na sequência."""
        if not self.is_running_sequence or self.current_position_index >= len(self.current_sequence.positions):
            self.is_running_sequence = False
            return None
            
        # Obtém a próxima posição
        position = self.current_sequence.positions[self.current_position_index]
        
        # Move para a posição
        self.cnc.move_to_absolute_position(position.x, position.y)
        
        # Verifica se chegou na posição
        while self.cnc.is_moving():
            time.sleep(0.1)
            
        # Captura a imagem
        image = self.camera.capture(position.camera_params)
        
        # Prepara dados para callback
        result = {
            "position": position,
            "image": image,
            "timestamp": time.time(),
            "sequence": self.current_sequence.name,
            "index": self.current_position_index
        }
        
        # Avança para a próxima posição
        self.current_position_index += 1
        
        # Chama o callback se fornecido
        if callback:
            callback(result)
            
        return result
        
    def stop_sequence(self):
        """Para a execução da sequência atual."""
        self.is_running_sequence = False
        
    def save_positions(self, filename):
        """Salva todas as posições e sequências em um arquivo."""
        return self.position_manager.save_to_file(filename)
        
    def load_positions(self, filename):
        """Carrega posições e sequências de um arquivo."""
        return self.position_manager.load_from_file(filename)