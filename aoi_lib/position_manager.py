import time

class InspectionPosition:
    """Representa uma posição de inspeção."""
    
    def __init__(self, name, x, y, z=0.0, camera_params=None):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.camera_params = camera_params or {}
        self.creation_time = time.time()
        
    def to_dict(self):
        """Converte para dicionário para serialização."""
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'camera_params': self.camera_params,
            'creation_time': self.creation_time
        }
        
    @classmethod
    def from_dict(cls, data):
        """Cria a partir de um dicionário."""
        position = cls(
            data['name'],
            data.get('x', 0.0),
            data.get('y', 0.0),
            data.get('z', 0.0),
            data.get('camera_params', {})
        )
        position.creation_time = data.get('creation_time', time.time())
        return position


class InspectionSequence:
    """Representa uma sequência de posições de inspeção."""
    
    def __init__(self, name):
        self.name = name
        self.positions = []
        self.creation_time = time.time()
        self.last_run_time = None
        
    def add_position(self, position):
        """Adiciona uma posição à sequência."""
        self.positions.append(position)
        
    def remove_position(self, index):
        """Remove uma posição pelo índice."""
        if 0 <= index < len(self.positions):
            del self.positions[index]
            return True
        return False
        
    def move_position(self, old_index, new_index):
        """Move uma posição na sequência."""
        if 0 <= old_index < len(self.positions) and 0 <= new_index < len(self.positions):
            position = self.positions.pop(old_index)
            self.positions.insert(new_index, position)
            return True
        return False
        
    def to_dict(self):
        """Converte para dicionário para serialização."""
        return {
            'name': self.name,
            'positions': [p.to_dict() for p in self.positions],
            'creation_time': self.creation_time,
            'last_run_time': self.last_run_time
        }
        
    @classmethod
    def from_dict(cls, data, positions_dict=None):
        """Cria a partir de um dicionário."""
        sequence = cls(data['name'])
        sequence.creation_time = data.get('creation_time', time.time())
        sequence.last_run_time = data.get('last_run_time')
        
        # Reconstruir posições
        for pos_data in data['positions']:
            if positions_dict and pos_data['name'] in positions_dict:
                # Usa posição existente
                sequence.positions.append(positions_dict[pos_data['name']])
            else:
                # Cria nova posição
                position = InspectionPosition.from_dict(pos_data)
                sequence.positions.append(position)
                
        return sequence


class InspectionPositionManager:
    """Gerencia posições e sequências de inspeção."""
    
    def __init__(self):
        self.positions = {}  # name -> position
        self.sequences = {}  # name -> sequence
        
    def add_position(self, position):
        """Adiciona uma posição."""
        self.positions[position.name] = position
        
    def remove_position(self, position_name):
        """Remove uma posição pelo nome."""
        if position_name in self.positions:
            del self.positions[position_name]
            
            # Atualiza sequências que usam esta posição
            for sequence in self.sequences.values():
                sequence.positions = [p for p in sequence.positions if p.name != position_name]
                
            return True
        return False
        
    def get_position(self, position_name):
        """Obtém uma posição pelo nome."""
        return self.positions.get(position_name)
        
    def add_sequence(self, sequence):
        """Adiciona uma sequência."""
        self.sequences[sequence.name] = sequence
        
    def remove_sequence(self, sequence_name):
        """Remove uma sequência pelo nome."""
        if sequence_name in self.sequences:
            del self.sequences[sequence_name]
            return True
        return False
        
    def get_sequence(self, sequence_name):
        """Obtém uma sequência pelo nome."""
        return self.sequences.get(sequence_name)
        
    def save_to_file(self, filename):
        """Salva todas as posições e sequências em um arquivo JSON."""
        data = {
            'positions': {name: pos.to_dict() for name, pos in self.positions.items()},
            'sequences': {name: seq.to_dict() for name, seq in self.sequences.items()}
        }
        
        try:
            with open(filename, 'w') as f:
                import json
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
            return False
            
    def load_from_file(self, filename):
        """Carrega posições e sequências de um arquivo JSON."""
        try:
            with open(filename, 'r') as f:
                import json
                data = json.load(f)
                
            # Limpa dados existentes
            self.positions.clear()
            self.sequences.clear()
            
            # Carrega posições
            for name, pos_data in data.get('positions', {}).items():
                position = InspectionPosition.from_dict(pos_data)
                self.positions[name] = position
                
            # Carrega sequências
            for name, seq_data in data.get('sequences', {}).items():
                sequence = InspectionSequence.from_dict(seq_data, self.positions)
                self.sequences[name] = sequence
                
            return True
            
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return False