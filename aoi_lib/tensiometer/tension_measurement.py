"""
Módulo: tension_measurement.py
Descrição: Lógica de negócio para medição de tensão de stencil
Contém cálculo de grid e salvamento de medições em JSON
"""

import json
import logging
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)

# Pasta para salvar rotinas de medição
ROUTINES_FOLDER = Path(__file__).parent.parent.parent / "tension_routines"
ROUTINES_FOLDER.mkdir(exist_ok=True)


class StencilTensionMeasurement:
    """
    Gerencia lógica de medição de tensão de stencil.

    Responsabilidades:
    - Calcular grid de pontos NxN
    - Salvar medições em JSON
    - Carregar rotinas de medição
    - Validação de parâmetros

    Esta classe contém apenas lógica de negócio, sem interface gráfica.
    """

    def __init__(self, cnc_controller=None, tensiometer=None):
        """
        Inicializa gerenciador de medição de tensão.

        Args:
            cnc_controller: Controlador CNC (opcional, para medição)
            tensiometer: Gerenciador serial do tensiômetro (opcional)
        """
        self.cnc = cnc_controller
        self.tensiometer = tensiometer
        self.measurements = []

    def calculate_grid_points(self, start_x: float, start_y: float,
                             end_x: float, end_y: float,
                             n: int) -> Optional[List[Tuple[float, float]]]:
        """
        Calcula grid de pontos NxN entre ponto inicial e final.

        O grid segue padrão zig-zag:
        - Linha ímpar: esquerda → direita
        - Linha par: direita → esquerda

        Args:
            start_x: Coordenada X inicial
            start_y: Coordenada Y inicial
            end_x: Coordenada X final
            end_y: Coordenada Y final
            n: Número de pontos por eixo (grid NxN)

        Returns:
            Lista de tuplas [(x1, y1), (x2, y2), ...] ou None se inválido

        Raises:
            ValueError: Se parâmetros inválidos
        """
        try:
            if n < 2:
                raise ValueError("Quantidade deve ser >= 2")

            # Gera pontos X e Y linearmente espaçados
            x_points = np.linspace(start_x, end_x, n)
            y_points = np.linspace(start_y, end_y, n)

            # Cria grid em padrão zig-zag
            points = []
            for i, y in enumerate(y_points):
                row_points = []
                for x in x_points:
                    row_points.append((float(x), float(y)))

                # Inverte linhas pares (zig-zag)
                if i % 2 == 1:
                    row_points.reverse()

                points.extend(row_points)

            logger.info(f"Grid calculado: {len(points)} pontos ({n}x{n})")
            return points

        except Exception as e:
            logger.error(f"Erro ao calcular grid: {e}")
            raise ValueError(f"Parâmetros inválidos: {e}")

    def validate_parameters(self, start_x: float, start_y: float,
                           end_x: float, end_y: float,
                           n: int, z_height: float) -> Tuple[bool, str]:
        """
        Valida parâmetros de medição.

        Args:
            start_x, start_y: Ponto inicial
            end_x, end_y: Ponto final
            n: Número de pontos por eixo
            z_height: Altura Z para medição

        Returns:
            (válido, mensagem_de_erro)
        """
        try:
            if n < 2:
                return False, "Quantidade deve ser >= 2"

            if n > 20:
                return False, "Quantidade não pode exceder 20 (muitas medições)"

            if z_height < -50 or z_height > 0:
                return False, "Altura Z deve estar entre -50 e 0 mm"

            # Verifica se área é razoável
            area_x = abs(end_x - start_x)
            area_y = abs(end_y - start_y)

            if area_x < 10 or area_y < 10:
                return False, "Área de medição muito pequena (mínimo 10x10 mm)"

            if area_x > 1000 or area_y > 1000:
                return False, "Área de medição muito grande (máximo 1000x1000 mm)"

            return True, ""

        except Exception as e:
            return False, f"Erro na validação: {e}"

    def save_measurements(self, measurements: List[Dict],
                         start_x: float, start_y: float,
                         end_x: float, end_y: float,
                         n: int, z_height: float,
                         filename: Optional[str] = None) -> str:
        """
        Salva medições em arquivo JSON.

        Formato do JSON:
        {
            "type": "stencil_tension",
            "timestamp": "2026-01-13T10:30:00",
            "parameters": {
                "start": {"x": 0, "y": 0},
                "end": {"x": 100, "y": 100},
                "quantity": 5,
                "height": -5
            },
            "measurements": [
                {"x": 0, "y": 0, "z": -5, "tension": "35.50"},
                ...
            ]
        }

        Args:
            measurements: Lista de medições
            start_x, start_y, end_x, end_y: Limites da área
            n: Número de pontos por eixo
            z_height: Altura Z de medição
            filename: Nome do arquivo (opcional, usa timestamp se não fornecido)

        Returns:
            Caminho do arquivo salvo
        """
        try:
            # Gera nome de arquivo se não fornecido
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tension_{timestamp}.json"

            filepath = ROUTINES_FOLDER / filename

            # Estrutura dos dados
            data = {
                "type": "stencil_tension",
                "timestamp": datetime.now().isoformat(),
                "parameters": {
                    "start": {"x": float(start_x), "y": float(start_y)},
                    "end": {"x": float(end_x), "y": float(end_y)},
                    "quantity": int(n),
                    "height": float(z_height)
                },
                "statistics": self._calculate_statistics(measurements),
                "measurements": measurements
            }

            # Salva arquivo
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            logger.info(f"Medições salvas em: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Erro ao salvar medições: {e}")
            raise

    def load_measurements(self, filename: str) -> Dict:
        """
        Carrega medições de arquivo JSON.

        Args:
            filename: Nome do arquivo (ou caminho completo)

        Returns:
            Dicionário com dados carregados
        """
        try:
            # Se apenas nome do arquivo, procura na pasta de rotinas
            if not Path(filename).is_absolute():
                filepath = ROUTINES_FOLDER / filename
            else:
                filepath = Path(filename)

            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"Medições carregadas de: {filepath}")
            return data

        except Exception as e:
            logger.error(f"Erro ao carregar medições: {e}")
            raise

    def list_routines(self) -> List[str]:
        """
        Lista rotinas de medição disponíveis.

        Returns:
            Lista de nomes de arquivos JSON
        """
        try:
            files = list(ROUTINES_FOLDER.glob("*.json"))
            return [f.name for f in files]
        except Exception as e:
            logger.error(f"Erro ao listar rotinas: {e}")
            return []

    def _calculate_statistics(self, measurements: List[Dict]) -> Dict:
        """
        Calcula estatísticas das medições.

        Args:
            measurements: Lista de medições com campo "tension"

        Returns:
            Dicionário com estatísticas (min, max, mean, std)
        """
        try:
            tensions = []
            for m in measurements:
                try:
                    tension_val = float(m["tension"])
                    tensions.append(tension_val)
                except (ValueError, KeyError):
                    continue

            if not tensions:
                return {
                    "count": 0,
                    "min": None,
                    "max": None,
                    "mean": None,
                    "std": None
                }

            return {
                "count": len(tensions),
                "min": float(min(tensions)),
                "max": float(max(tensions)),
                "mean": float(np.mean(tensions)),
                "std": float(np.std(tensions))
            }

        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas: {e}")
            return {}
