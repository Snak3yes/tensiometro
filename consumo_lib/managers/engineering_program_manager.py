"""
EngineeringProgramManager - Gerenciador de Programas de Inspeção

Este módulo gerencia operações CRUD (Create, Read, Update, Delete)
para programas de inspeção criados pelo Engineering Wizard.

Funcionalidades:
- Salvar programas em JSON
- Carregar programas salvos
- Listar programas disponíveis
- Deletar programas
- Verificar existência de programas
- Exportar/importar programas

Author: Claude Code (Sonnet 4.5)
Date: 2026-01-13
"""

import json
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from consumo_lib.models.engineering.program_config import ProgramConfig

logger = logging.getLogger(__name__)


class EngineeringProgramManager:
    """
    Gerenciador de programas de inspeção.

    Responsável por:
    - Salvar programas em arquivos JSON
    - Carregar programas salvos
    - Listar todos os programas disponíveis
    - Deletar programas
    - Verificar existência de programas
    - Gerenciar diretório de programas

    Attributes:
        programs_dir: Diretório onde os programas são salvos
    """

    # Diretório padrão para programas de inspeção
    PROGRAMS_DIR = Path("data/inspection_programs")

    # Subdiretório para auto-saves
    AUTOSAVES_DIR = PROGRAMS_DIR / ".autosaves"

    def __init__(self, programs_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de programas.

        Args:
            programs_dir: Diretório customizado para programas (opcional)
        """
        self.programs_dir = programs_dir or self.PROGRAMS_DIR
        self.autosaves_dir = self.programs_dir / ".autosaves"

        # Cria diretórios se não existirem
        self.programs_dir.mkdir(parents=True, exist_ok=True)
        self.autosaves_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"EngineeringProgramManager inicializado: {self.programs_dir}")

    # ========================================================================
    #  CRUD - CREATE, READ, UPDATE, DELETE
    # ========================================================================

    def save_program(
        self,
        program: ProgramConfig,
        filename: Optional[str] = None
    ) -> Path:
        """
        Salva programa de inspeção em arquivo JSON.

        Args:
            program: Configuração do programa a salvar
            filename: Nome do arquivo (opcional, usa padrão se None)

        Returns:
            Path do arquivo salvo

        Raises:
            IOError: Se não conseguir salvar
            ValueError: Se programa for inválido
        """
        # Valida programa antes de salvar
        is_valid, errors = program.validate()
        if not is_valid:
            logger.warning(f"Salvando programa com erros: {errors}")

        # Gera nome de arquivo se não fornecido
        if filename is None:
            filename = self._generate_filename(program)

        # Caminho completo do arquivo
        filepath = self.programs_dir / filename

        # Atualiza timestamp de modificificação
        program.modified_at = datetime.now().isoformat()

        # Salva usando método do ProgramConfig
        program.save_to_file(str(filepath))

        logger.info(f"✅ Programa salvo: {filepath}")
        return filepath

    def load_program(self, program_name: str) -> ProgramConfig:
        """
        Carrega programa de inspeção de arquivo JSON.

        Args:
            program_name: Nome do programa (com ou sem .json)

        Returns:
            Instância de ProgramConfig

        Raises:
            FileNotFoundError: Se programa não existe
            json.JSONDecodeError: Se JSON for inválido
            ValueError: Se dados forem inválidos
        """
        # Adiciona .json se necessário
        if not program_name.endswith('.json'):
            program_name += '.json'

        # Caminho completo do arquivo
        filepath = self.programs_dir / program_name

        if not filepath.exists():
            raise FileNotFoundError(
                f"Programa não encontrado: {program_name}\n"
                f"Caminho buscado: {filepath}"
            )

        # Carrega usando método do ProgramConfig
        try:
            program = ProgramConfig.from_file(str(filepath))
            logger.info(f"✅ Programa carregado: {filepath}")
            return program
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao carregar programa: {e}")
            raise ValueError(f"Erro ao carregar programa: {e}")

    def update_program(
        self,
        program_name: str,
        program: ProgramConfig
    ) -> Path:
        """
        Atualiza programa existente.

        Args:
            program_name: Nome do programa a atualizar
            program: Nova configuração

        Returns:
            Path do arquivo atualizado

        Raises:
            FileNotFoundError: Se programa não existe
        """
        # Verifica se programa existe
        if not self.program_exists(program_name):
            raise FileNotFoundError(f"Programa não encontrado: {program_name}")

        # Salva com mesmo nome
        return self.save_program(program, filename=program_name)

    def delete_program(
        self,
        program_name: str,
        confirm: bool = False
    ) -> bool:
        """
        Deleta programa de inspeção.

        Args:
            program_name: Nome do programa a deletar
            confirm: Se True, deleta sem confirmação

        Returns:
            True se deletado com sucesso

        Raises:
            FileNotFoundError: Se programa não existe
            PermissionError: Se não tiver permissão para deletar
        """
        # Adiciona .json se necessário
        if not program_name.endswith('.json'):
            program_name += '.json'

        filepath = self.programs_dir / program_name

        if not filepath.exists():
            raise FileNotFoundError(f"Programa não encontrado: {program_name}")

        # Deleta arquivo
        filepath.unlink()
        logger.info(f"🗑️ Programa deletado: {filepath}")

        return True

    # ========================================================================
    #  CONSULTA E LISTAGEM
    # ========================================================================

    def list_programs(self) -> List[Dict[str, any]]:
        """
        Lista todos os programas disponíveis.

        Returns:
            Lista de dicionários com metadados dos programas:
            - name: Nome do arquivo
            - program_name: Nome do programa
            - stencil_code: Código do stencil
            - version: Versão
            - created_at: Data de criação
            - modified_at: Data de modificação
            - filepath: Caminho completo
        """
        programs = []

        # Varre diretório de programas
        for filepath in self.programs_dir.glob("*.json"):
            # Ignora autosaves
            if filepath.name.startswith(".autosave_"):
                continue

            try:
                # Lê metadados do JSON
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                programs.append({
                    "name": filepath.stem,
                    "program_name": data.get("program_name", "N/A"),
                    "stencil_code": data.get("stencil_code", "N/A"),
                    "version": data.get("version", "N/A"),
                    "created_at": data.get("created_at", "N/A"),
                    "modified_at": data.get("modified_at", "N/A"),
                    "filepath": str(filepath),
                })
            except Exception as e:
                logger.warning(f"Erro ao ler metadados de {filepath}: {e}")
                continue

        # Ordena por nome
        programs.sort(key=lambda p: p["name"])

        logger.debug(f"Listados {len(programs)} programas")
        return programs

    def program_exists(self, program_name: str) -> bool:
        """
        Verifica se programa existe.

        Args:
            program_name: Nome do programa

        Returns:
            True se programa existe
        """
        # Adiciona .json se necessário
        if not program_name.endswith('.json'):
            program_name += '.json'

        filepath = self.programs_dir / program_name
        return filepath.exists()

    def get_program_info(self, program_name: str) -> Dict[str, any]:
        """
        Retorna metadados de um programa.

        Args:
            program_name: Nome do programa

        Returns:
            Dicionário com metadados

        Raises:
            FileNotFoundError: Se programa não existe
        """
        # Adiciona .json se necessário
        if not program_name.endswith('.json'):
            program_name += '.json'

        filepath = self.programs_dir / program_name

        if not filepath.exists():
            raise FileNotFoundError(f"Programa não encontrado: {program_name}")

        # Lê metadados
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "name": filepath.stem,
            "filepath": str(filepath),
            **data
        }

    # ========================================================================
    #  AUTO-SAVE
    # ========================================================================

    def save_autosave(self, state: Dict) -> Path:
        """
        Salva estado automaticamente (auto-save).

        Args:
            state: Dicionário com estado do wizard

        Returns:
            Path do arquivo salvo
        """
        # Gera nome único para auto-save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f".autosave_{timestamp}.json"
        filepath = self.autosaves_dir / filename

        # Salva estado
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        logger.debug(f"Auto-save salvo: {filepath}")
        return filepath

    def get_latest_autosave(self) -> Optional[Dict]:
        """
        Retorna o auto-save mais recente.

        Returns:
            Dicionário com estado ou None se não houver autosaves
        """
        autosaves = sorted(
            self.autosaves_dir.glob(".autosave_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not autosaves:
            return None

        latest = autosaves[0]
        with open(latest, 'r', encoding='utf-8') as f:
            state = json.load(f)

        logger.info(f"Auto-save mais recente: {latest.name}")
        return state

    def cleanup_autosaves(self, keep_latest: int = 5):
        """
        Limpa autosaves antigos, mantendo apenas os mais recentes.

        Args:
            keep_latest: Número de autosaves a manter
        """
        autosaves = sorted(
            self.autosaves_dir.glob(".autosave_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove autosaves excedentes
        for old_autosave in autosaves[keep_latest:]:
            old_autosave.unlink()
            logger.debug(f"Auto-save antigo removido: {old_autosave}")

        logger.info(f"Cleanup de autosaves: mantidos {len(autosaves[:keep_latest])}, "
                    f"removidos {len(autosaves[keep_latest:])}")

    def clear_autosaves(self):
        """Remove todos os autosaves."""
        for autosave in self.autosaves_dir.glob(".autosave_*.json"):
            autosave.unlink()
        logger.info("Todos os autosaves removidos")

    # ========================================================================
    #  EXPORTAR/IMPORTAR
    # ========================================================================

    def export_program(
        self,
        program_name: str,
        export_path: str
    ) -> Path:
        """
        Exporta programa para caminho específico.

        Args:
            program_name: Nome do programa a exportar
            export_path: Caminho de destino

        Returns:
            Path do arquivo exportado

        Raises:
            FileNotFoundError: Se programa não existe
        """
        # Adiciona .json se necessário
        if not program_name.endswith('.json'):
            program_name += '.json'

        source = self.programs_dir / program_name
        destination = Path(export_path)

        if not source.exists():
            raise FileNotFoundError(f"Programa não encontrado: {program_name}")

        # Copia arquivo
        shutil.copy2(source, destination)
        logger.info(f"Programa exportado: {destination}")

        return destination

    def import_program(
        self,
        import_path: str,
        new_name: Optional[str] = None
    ) -> Path:
        """
        Importa programa de caminho específico.

        Args:
            import_path: Caminho do programa a importar
            new_name: Novo nome do programa (opcional)

        Returns:
            Path do arquivo importado

        Raises:
            FileNotFoundError: Se arquivo não existe
        """
        source = Path(import_path)

        if not source.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {import_path}")

        # Determina nome de destino
        if new_name is None:
            filename = source.name
        else:
            if not new_name.endswith('.json'):
                new_name += '.json'
            filename = new_name

        destination = self.programs_dir / filename

        # Copia arquivo
        shutil.copy2(source, destination)
        logger.info(f"Programa importado: {destination}")

        return destination

    # ========================================================================
    #  MÉTODOS PRIVADOS
    # ========================================================================

    def _generate_filename(self, program: ProgramConfig) -> str:
        """
        Gera nome de arquivo para programa.

        Args:
            program: Configuração do programa

        Returns:
            Nome do arquivo (com .json)
        """
        # Cria nome seguro
        safe_stencil = program.stencil_code.replace(" ", "_").replace("/", "_")
        safe_name = program.program_name.replace(" ", "_").replace("/", "_")
        version = program.version.replace(".", "_")

        filename = f"{safe_stencil}_{safe_name}_{version}.json"
        return filename
