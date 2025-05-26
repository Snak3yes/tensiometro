"""
Módulo para gerenciamento de G-CODE na aplicação de inspeção AOI.
Permite criar, ler e manipular arquivos G-CODE para controle de percursos de inspeção.
"""

import os
import re
import time
import logging
from datetime import datetime

logger = logging.getLogger("GCodeManager")

class GCodeManager:
    """
    Gerencia operações de G-CODE para o sistema AOI, incluindo:
    - Geração de G-CODE a partir de posições de inspeção
    - Leitura de arquivos G-CODE para criar sequências de inspeção
    - Inclusão de comandos especiais para captura de imagens
    """
    
    # Definição de comandos especiais como comentários em G-CODE
    CAPTURE_IMAGE_CMD = ";AOI_CAPTURE_IMAGE"
    POSITION_NAME_CMD = ";AOI_POSITION_NAME:"
    SEQUENCE_NAME_CMD = ";AOI_SEQUENCE_NAME:"
    CAMERA_PARAMS_CMD = ";AOI_CAMERA_PARAMS:"
    
    def __init__(self):
        """Inicializa o gerenciador de G-CODE"""
        self.feed_rate = 1000  # Taxa de avanço padrão (mm/min)
        self.safe_z_height = 5  # Altura Z para movimentos seguros
        self.use_z_axis = False  # Se verdadeiro, inclui movimentos no eixo Z
        
    def generate_gcode_from_sequence(self, sequence, include_header=True):
        """
        Gera G-CODE a partir de uma sequência de inspeção
        
        Args:
            sequence: Objeto InspectionSequence contendo as posições
            include_header: Se True, inclui cabeçalho com informações da sequência
            
        Returns:
            Uma string contendo o G-CODE completo
        """
        gcode_lines = []
        
        # Adiciona cabeçalho com informações
        if include_header:
            gcode_lines.extend([
                f"; AOI Inspection Sequence Generated G-CODE",
                f"; Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"{self.SEQUENCE_NAME_CMD} {sequence.name}",
                f"; Total positions: {len(sequence.positions)}",
                f"; Feed rate: {self.feed_rate} mm/min",
                ";"
            ])
        
        # Configurações iniciais
        gcode_lines.extend([
            "G21 ; Set units to mm",
            "G90 ; Set absolute positioning",
            f"F{self.feed_rate} ; Set feed rate"
        ])
        
        # Para cada posição na sequência
        for i, position in enumerate(sequence.positions):
            # Adiciona comentário com o nome da posição
            gcode_lines.append(f"\n; Position {i+1}: {position.name}")
            gcode_lines.append(f"{self.POSITION_NAME_CMD} {position.name}")
            
            # Adiciona parâmetros da câmera se existirem
            if position.camera_params:
                params_str = ",".join([f"{k}:{v}" for k, v in position.camera_params.items()])
                gcode_lines.append(f"{self.CAMERA_PARAMS_CMD} {params_str}")
            
            # Adiciona movimento para a posição
            gcode_lines.append(f"G0 X{position.x:.3f} Y{position.y:.3f} ; Move to position")
            
            # Adiciona comando para captura de imagem
            gcode_lines.append(f"{self.CAPTURE_IMAGE_CMD} ; Capture image at this position")
            
        # Finaliza o programa
        gcode_lines.append("\nM2 ; End program")
        
        return "\n".join(gcode_lines)
    
    def read_gcode_file(self, filename):
        """
        Lê um arquivo G-CODE e cria uma sequência de posições de inspeção
        
        Args:
            filename: Caminho do arquivo G-CODE
            
        Returns:
            Um dicionário contendo:
            - 'sequence_name': Nome da sequência extraída do arquivo
            - 'positions': Lista de dicionários com informações das posições
        """
        if not os.path.exists(filename):
            logger.error(f"Arquivo G-CODE não encontrado: {filename}")
            return None
            
        try:
            with open(filename, 'r') as f:
                gcode_content = f.read()
                
            return self.parse_gcode(gcode_content)
            
        except Exception as e:
            logger.error(f"Erro ao ler arquivo G-CODE: {str(e)}")
            return None
    
    def parse_gcode(self, gcode_content):
        """
        Analisa o conteúdo G-CODE e extrai sequência e posições
        
        Args:
            gcode_content: String contendo o G-CODE a ser analisado
            
        Returns:
            Dicionário com dados da sequência e posições
        """
        lines = gcode_content.split('\n')
        sequence_name = "Sequência Importada"
        positions = []
        
        current_position = None
        
        # Extrai nome da sequência
        for line in lines:
            if self.SEQUENCE_NAME_CMD in line:
                sequence_name = line.split(self.SEQUENCE_NAME_CMD, 1)[1].strip()
                break
        
        # Extrai as posições
        for line in lines:
            # Nova posição
            if self.POSITION_NAME_CMD in line:
                # Finaliza posição anterior se existir
                if current_position:
                    positions.append(current_position)
                
                # Inicia nova posição
                position_name = line.split(self.POSITION_NAME_CMD, 1)[1].strip()
                current_position = {
                    'name': position_name,
                    'x': 0.0,
                    'y': 0.0,
                    'z': 0.0,
                    'camera_params': {}
                }
            
            # Parâmetros da câmera
            elif self.CAMERA_PARAMS_CMD in line and current_position:
                params_str = line.split(self.CAMERA_PARAMS_CMD, 1)[1].strip()
                params_pairs = params_str.split(',')
                
                for pair in params_pairs:
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        # Tenta converter para número se possível
                        try:
                            if '.' in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            pass  # Mantém como string
                        
                        current_position['camera_params'][key] = value
            
            # Movimento G0/G1
            elif (line.strip().startswith('G0') or line.strip().startswith('G1')) and current_position:
                # Extrai coordenadas X e Y
                x_match = re.search(r'X([-\d.]+)', line)
                y_match = re.search(r'Y([-\d.]+)', line)
                
                if x_match:
                    current_position['x'] = float(x_match.group(1))
                if y_match:
                    current_position['y'] = float(y_match.group(1))
                # Z (opcional)
                z_match = re.search(r'Z([-\d.]+)', line)
                if z_match:
                    current_position['z'] = float(z_match.group(1))
        
        # Adiciona a última posição se existir
        if current_position:
            positions.append(current_position)
            
        return {
            'sequence_name': sequence_name,
            'positions': positions
        }
    
    def save_gcode_to_file(self, sequence, filename):
        """
        Gera G-CODE a partir de uma sequência e salva em um arquivo
        
        Args:
            sequence: Objeto InspectionSequence contendo as posições
            filename: Caminho do arquivo onde o G-CODE será salvo
            
        Returns:
            Boolean indicando sucesso da operação
        """
        try:
            gcode_content = self.generate_gcode_from_sequence(sequence)
            
            with open(filename, 'w') as f:
                f.write(gcode_content)
                
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar arquivo G-CODE: {str(e)}")
            return False