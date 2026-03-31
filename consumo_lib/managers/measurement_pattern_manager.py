"""
Gerenciador de Padrões de Medição de Tensão

Gerencia padrões de medição de tensão (MeasurementPattern):
- Salvar padrões de medição
- Carregar padrões existentes
- Listar padrões disponíveis
- Editar/excluir padrões
- Persistência em arquivos JSON

Author: Claude
Created: 2026-03-31
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict

from PyQt6.QtCore import QObject, pyqtSignal

from aoi_lib.tensiometer.models import MeasurementPattern, GridParameters

logger = logging.getLogger(__name__)


class MeasurementPatternManager(QObject):
    """
    Gerencia padrões de medição de tensão.

    Responsabilidades:
        - Salvar padrões de medição em JSON
        - Carregar padrões do diretório
        - Listar padrões disponíveis
        - Editar e excluir padrões
        - Persistência em arquivos JSON

    Atributos:
        patterns_dir: Diretório onde os padrões são armazenados
        pattern_saved: Signal emitido quando padrão é salvo
        pattern_deleted: Signal emitido quando padrão é excluído

    Exemplo:
        >>> pattern_mgr = MeasurementPatternManager()
        >>> pattern_mgr.pattern_saved.connect(update_ui)
        >>> patterns = pattern_mgr.list_patterns()
    """

    pattern_saved = pyqtSignal(str)  # pattern_name
    pattern_deleted = pyqtSignal(str)  # pattern_name
    pattern_loaded = pyqtSignal(object)  # MeasurementPattern

    def __init__(self, patterns_dir: str = None):
        """
        Inicializa gerenciador de padrões.

        Args:
            patterns_dir: Diretório para armazenar padrões (default: patterns/ no projeto)
        """
        super().__init__()

        if patterns_dir is None:
            # Usa diretório relativo ao projeto
            base = Path(__file__).parent.parent.parent
            patterns_dir = str(base / "patterns")

        self.patterns_dir = Path(patterns_dir)
        self._ensure_directory()

        # Cache de padrões carregados
        self._patterns_cache: Dict[str, MeasurementPattern] = {}

        logger.info(f"MeasurementPatternManager inicializado em: {self.patterns_dir}")

    def _ensure_directory(self):
        """Cria o diretório de padrões se não existir."""
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

    def _get_pattern_filename(self, name: str) -> str:
        """
        Converte nome do padrão em nome de arquivo seguro.

        Args:
            name: Nome do padrão

        Returns:
            Nome de arquivo seguro (sem caracteres especiais)
        """
        # Remove caracteres especiais e substitui espaços por underscores
        safe_name = "".join(c if c.isalnum() or c in " _-." else "_" for c in name)
        return f"{safe_name}.json"

    def _get_pattern_filepath(self, name: str) -> Path:
        """
        Obtém caminho completo do arquivo de padrão.

        Args:
            name: Nome do padrão

        Returns:
            Path completo do arquivo
        """
        return self.patterns_dir / self._get_pattern_filename(name)

    def save_pattern(self, pattern: MeasurementPattern) -> bool:
        """
        Salva um padrão de medição.

        Args:
            pattern: MeasurementPattern para salvar

        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Atualiza timestamp
            pattern.update_modified()

            # Obtém caminho do arquivo
            file_path = self._get_pattern_filepath(pattern.name)

            # Serializa para JSON
            data = pattern.to_dict()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atualiza cache
            self._patterns_cache[pattern.name] = pattern

            logger.info(f"Padrão salvo: {file_path}")

            # Emite signal
            self.pattern_saved.emit(pattern.name)

            return True

        except Exception as e:
            logger.error(f"Erro ao salvar padrão '{pattern.name}': {e}")
            return False

    def load_pattern(self, name: str) -> Optional[MeasurementPattern]:
        """
        Carrega um padrão de medição pelo nome.

        Args:
            name: Nome do padrão

        Returns:
            MeasurementPattern ou None se não encontrado
        """
        # Verifica cache primeiro
        if name in self._patterns_cache:
            logger.debug(f"Padrão '{name}' carregado do cache")
            return self._patterns_cache[name]

        # Tenta carregar do arquivo
        file_path = self._get_pattern_filepath(name)

        if not file_path.exists():
            logger.warning(f"Padrão não encontrado: {name}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            pattern = MeasurementPattern.from_dict(data)

            # Atualiza cache
            self._patterns_cache[name] = pattern

            logger.info(f"Padrão carregado: {name}")

            # Emite signal
            self.pattern_loaded.emit(pattern)

            return pattern

        except Exception as e:
            logger.error(f"Erro ao carregar padrão '{name}': {e}")
            return None

    def list_patterns(self) -> List[Dict]:
        """
        Lista todos os padrões disponíveis.

        Returns:
            Lista de dicionários com metadados dos padrões
        """
        patterns = []

        if not self.patterns_dir.exists():
            return patterns

        for file_path in self.patterns_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                patterns.append({
                    'name': data.get('name', file_path.stem),
                    'description': data.get('description', ''),
                    'created_at': data.get('created_at', ''),
                    'modified_at': data.get('modified_at', ''),
                    'created_by': data.get('created_by', ''),
                    'grid_size': data.get('parameters', {}).get('grid_size', 0),
                    'file_path': str(file_path)
                })

            except Exception as e:
                logger.warning(f"Erro ao ler padrão {file_path}: {e}")

        # Ordena por data de modificação (mais recente primeiro)
        patterns.sort(key=lambda x: x.get('modified_at', ''), reverse=True)

        return patterns

    def delete_pattern(self, name: str) -> bool:
        """
        Exclui um padrão de medição.

        Args:
            name: Nome do padrão

        Returns:
            True se excluído com sucesso, False caso contrário
        """
        file_path = self._get_pattern_filepath(name)

        if not file_path.exists():
            logger.warning(f"Padrão não encontrado para exclusão: {name}")
            return False

        try:
            # Remove arquivo
            file_path.unlink()

            # Remove do cache
            self._patterns_cache.pop(name, None)

            logger.info(f"Padrão excluído: {name}")

            # Emite signal
            self.pattern_deleted.emit(name)

            return True

        except Exception as e:
            logger.error(f"Erro ao excluir padrão '{name}': {e}")
            return False

    def get_pattern(self, name: str) -> Optional[MeasurementPattern]:
        """
        Obtém um padrão pelo nome (alias para load_pattern).

        Args:
            name: Nome do padrão

        Returns:
            MeasurementPattern ou None
        """
        return self.load_pattern(name)

    def pattern_exists(self, name: str) -> bool:
        """
        Verifica se um padrão já existe.

        Args:
            name: Nome do padrão

        Returns:
            True se padrão existe, False caso contrário
        """
        # Verifica cache
        if name in self._patterns_cache:
            return True

        # Verifica arquivo
        file_path = self._get_pattern_filepath(name)
        return file_path.exists()

    def create_pattern_from_dialog_params(
        self,
        name: str,
        description: str,
        start_point: tuple,
        end_point: tuple,
        grid_size: int,
        z_height: float,
        z_move: float,
        stabilization_time_ms: int = 500,
        feed_rate: float = 1000.0,
        created_by: str = ""
    ) -> Optional[MeasurementPattern]:
        """
        Cria um padrão a partir de parâmetros (típicos do diálogo de medição).

        Args:
            name: Nome do padrão
            description: Descrição
            start_point: (x, y) ponto inicial
            end_point: (x, y) ponto final
            grid_size: Tamanho do grid NxN
            z_height: Altura de medição Z
            z_move: Altura de movimento Z
            stabilization_time_ms: Tempo de estabilização (ms)
            feed_rate: Velocidade de movimento (mm/min)
            created_by: Usuário criador

        Returns:
            MeasurementPattern criado ou None se erro
        """
        try:
            # Cria GridParameters
            grid_params = GridParameters(
                start_point=start_point,
                end_point=end_point,
                grid_size=grid_size,
                z_height=z_height,
                z_move=z_move
            )

            # Cria padrão
            pattern = MeasurementPattern(
                name=name,
                description=description,
                grid_parameters=grid_params,
                stabilization_time_ms=stabilization_time_ms,
                feed_rate=feed_rate,
                created_by=created_by
            )

            return pattern

        except Exception as e:
            logger.error(f"Erro ao criar padrão '{name}': {e}")
            return None

    def clear_cache(self):
        """Limpa o cache de padrões."""
        self._patterns_cache.clear()
        logger.debug("Cache de padrões limpo")
