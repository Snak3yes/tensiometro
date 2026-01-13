"""
program_config.py
-----------------

Modelo de dados para configuração de programa de inspeção visual.

Este módulo define o modelo ProgramConfig que agrega todos os dados
coletados nas 7 abas do wizard de criação de programa de inspeção.

Autor: Claude Code (Sonnet 4.5)
Data: 2026-01-13
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class FiducialConfig:
    """
    Configuração de fiduciais.

    Attributes:
        fiducial1: Coordenadas do fiducial 1 (X, Y)
        fiducial2: Coordenadas do fiducial 2 (X, Y)
        template1_path: Caminho da imagem template do fiducial 1
        template2_path: Caminho da imagem template do fiducial 2
    """
    fiducial1: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    fiducial2: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    template1_path: Optional[str] = None
    template2_path: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'FiducialConfig':
        return cls(
            fiducial1=data.get("fiducial1", {"x": 0.0, "y": 0.0}),
            fiducial2=data.get("fiducial2", {"x": 0.0, "y": 0.0}),
            template1_path=data.get("template1_path"),
            template2_path=data.get("template2_path"),
        )


@dataclass
class MosaicConfig:
    """
    Configuração de captura de mosaico.

    Attributes:
        corner1: Coordenadas do canto 1 (X, Y)
        corner2: Coordenadas do canto 2 (X, Y)
        grid_rows: Número de linhas do grid
        grid_cols: Número de colunas do grid
        total_fovs: Número total de FOVs capturadas
        capture_delay_ms: Delay entre capturas (ms)
    """
    corner1: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    corner2: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    grid_rows: int = 4
    grid_cols: int = 4
    total_fovs: int = 16
    capture_delay_ms: int = 200

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'MosaicConfig':
        return cls(
            corner1=data.get("corner1", {"x": 0.0, "y": 0.0}),
            corner2=data.get("corner2", {"x": 0.0, "y": 0.0}),
            grid_rows=data.get("grid_rows", 4),
            grid_cols=data.get("grid_cols", 4),
            total_fovs=data.get("total_fovs", 16),
            capture_delay_ms=data.get("capture_delay_ms", 200),
        )


@dataclass
class AlignmentConfig:
    """
    Configuração de alinhamento Gerber-Imagem.

    Attributes:
        translation_x: Translação em X (mm)
        translation_y: Translação em Y (mm)
        rotation: Rotação (graus)
        scale: Fator de escala
        alignment_score: Score de qualidade do alinhamento (0-100)
    """
    translation_x: float = 0.0
    translation_y: float = 0.0
    rotation: float = 0.0
    scale: float = 1.0
    alignment_score: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'AlignmentConfig':
        return cls(
            translation_x=data.get("translation_x", 0.0),
            translation_y=data.get("translation_y", 0.0),
            rotation=data.get("rotation", 0.0),
            scale=data.get("scale", 1.0),
            alignment_score=data.get("alignment_score", 0.0),
        )


@dataclass
class InspectionGroupConfig:
    """
    Configuração de inspeção para um grupo de aberturas.

    Attributes:
        name: Nome do grupo (ex: "0.5mm Círculo")
        aperture_count: Número de aberturas no grupo
        ok_threshold: Threshold OK (%)
        partial_threshold: Threshold PARTIAL (%)
        binarization_method: Método de binarização
        pre_processing: Pré-processamento aplicado
        confirmed: Se o grupo foi confirmado pelo usuário
    """
    name: str
    aperture_count: int
    ok_threshold: float = 90.0
    partial_threshold: float = 70.0
    binarization_method: str = "otsu"
    pre_processing: str = "blur"
    confirmed: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'InspectionGroupConfig':
        return cls(
            name=data.get("name", ""),
            aperture_count=data.get("aperture_count", 0),
            ok_threshold=data.get("ok_threshold", 90.0),
            partial_threshold=data.get("partial_threshold", 70.0),
            binarization_method=data.get("binarization_method", "otsu"),
            pre_processing=data.get("pre_processing", "blur"),
            confirmed=data.get("confirmed", False),
        )


@dataclass
class ProgramConfig:
    """
    Configuração completa de um programa de inspeção visual.

    Este modelo agrega todos os dados coletados nas 7 abas do wizard:
    1. Dados do Programa (stencil_code, program_name, description, version)
    2. Gerber (gerber_file, aperture_count, fiducial_count)
    3. Fiduciais (posições, templates)
    4. Posicionamento (cantos, grid de mosaico)
    5. Alinhamento (translação, rotação, escala)
    6. Janelas de Inspeção (grupos, thresholds)
    7. Metadados (created_at, created_by, etc.)

    Attributes:
        # Aba 1: Dados do Programa
        stencil_code: Código do stencil (ex: "STENCIL-ABC-123")
        program_name: Nome do programa de inspeção
        description: Descrição do programa
        version: Versão do programa (ex: "v1.0")
        recipe_name: Nome da receita base (opcional)

        # Aba 2: Gerber
        gerber_file: Caminho do arquivo Gerber
        gerber_dimensions: Dimensões do Gerber (width, height em mm)
        aperture_count: Número de apertures no Gerber
        detected_fiducials: Número de fiduciais detectados automaticamente

        # Aba 3: Fiduciais
        fiducials: Configuração dos fiduciais

        # Aba 4: Posicionamento e Captura
        mosaic: Configuração do mosaico

        # Aba 5: Alinhamento
        alignment: Configuração de alinhamento

        # Aba 6: Janelas de Inspeção
        inspection_groups: Lista de grupos de inspeção
        total_apertures: Número total de aberturas
        configured_groups: Número de grupos configurados
        confirmed_groups: Número de grupos confirmados

        # Metadados
        created_at: Data/hora de criação
        created_by: Usuário que criou
        modified_at: Data/hora da última modificação
        modified_by: Usuário que modificou pela última vez
        notes: Observações adicionais
    """

    # Aba 1: Dados do Programa
    stencil_code: str
    program_name: str
    description: str = ""
    version: str = "v1.0"
    recipe_name: Optional[str] = None

    # Aba 2: Gerber
    gerber_file: Optional[str] = None
    gerber_dimensions: Dict[str, float] = field(default_factory=lambda: {"width": 0.0, "height": 0.0})
    aperture_count: int = 0
    detected_fiducials: int = 0

    # Aba 3: Fiduciais
    fiducials: FiducialConfig = field(default_factory=FiducialConfig)

    # Aba 4: Posicionamento e Captura
    mosaic: MosaicConfig = field(default_factory=MosaicConfig)

    # Aba 5: Alinhamento
    alignment: AlignmentConfig = field(default_factory=AlignmentConfig)

    # Aba 6: Janelas de Inspeção
    inspection_groups: List[InspectionGroupConfig] = field(default_factory=list)
    total_apertures: int = 0
    configured_groups: int = 0
    confirmed_groups: int = 0

    # Metadados
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: Optional[str] = None
    modified_at: Optional[str] = None
    modified_by: Optional[str] = None
    notes: str = ""

    def __post_init__(self):
        """Atualiza contadores após inicialização."""
        self.configured_groups = len(self.inspection_groups)
        self.confirmed_groups = sum(1 for g in self.inspection_groups if g.confirmed)
        if self.total_apertures == 0:
            self.total_apertures = sum(g.aperture_count for g in self.inspection_groups)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converte para dicionário.

        Returns:
            Dicionário com todos os dados do programa
        """
        data = asdict(self)
        # Converte sub-objetos para dict
        data["fiducials"] = self.fiducials.to_dict()
        data["mosaic"] = self.mosaic.to_dict()
        data["alignment"] = self.alignment.to_dict()
        data["inspection_groups"] = [g.to_dict() for g in self.inspection_groups]
        return data

    def to_json(self, indent: int = 2) -> str:
        """
        Converte para JSON string.

        Args:
            indent: Indentação JSON

        Returns:
            String JSON
        """
        import json
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save_to_file(self, filepath: str) -> None:
        """
        Salva configuração em arquivo JSON.

        Args:
            filepath: Caminho do arquivo

        Raises:
            IOError: Se não conseguir salvar
        """
        import json
        from pathlib import Path

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info(f"Programa salvo em: {filepath}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgramConfig':
        """
        Cria instância a partir de dicionário.

        Args:
            data: Dicionário com dados do programa

        Returns:
            Instância de ProgramConfig
        """
        fiducials_data = data.get("fiducials", {})
        mosaic_data = data.get("mosaic", {})
        alignment_data = data.get("alignment", {})
        inspection_groups_data = data.get("inspection_groups", [])

        return cls(
            # Aba 1
            stencil_code=data.get("stencil_code", ""),
            program_name=data.get("program_name", ""),
            description=data.get("description", ""),
            version=data.get("version", "v1.0"),
            recipe_name=data.get("recipe_name"),
            # Aba 2
            gerber_file=data.get("gerber_file"),
            gerber_dimensions=data.get("gerber_dimensions", {"width": 0.0, "height": 0.0}),
            aperture_count=data.get("aperture_count", 0),
            detected_fiducials=data.get("detected_fiducials", 0),
            # Aba 3
            fiducials=FiducialConfig.from_dict(fiducials_data),
            # Aba 4
            mosaic=MosaicConfig.from_dict(mosaic_data),
            # Aba 5
            alignment=AlignmentConfig.from_dict(alignment_data),
            # Aba 6
            inspection_groups=[InspectionGroupConfig.from_dict(g) for g in inspection_groups_data],
            total_apertures=data.get("total_apertures", 0),
            # Metadados
            created_at=data.get("created_at", datetime.now().isoformat()),
            created_by=data.get("created_by"),
            modified_at=data.get("modified_at"),
            modified_by=data.get("modified_by"),
            notes=data.get("notes", ""),
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'ProgramConfig':
        """
        Cria instância a partir de JSON string.

        Args:
            json_str: String JSON

        Returns:
            Instância de ProgramConfig
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_file(cls, filepath: str) -> 'ProgramConfig':
        """
        Carrega configuração de arquivo JSON.

        Args:
            filepath: Caminho do arquivo

        Returns:
            Instância de ProgramConfig

        Raises:
            IOError: Se não conseguir ler
            json.JSONDecodeError: Se JSON for inválido
        """
        import json
        from pathlib import Path

        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Programa carregado de: {filepath}")
        return cls.from_dict(data)

    def validate(self) -> tuple[bool, List[str]]:
        """
        Valida configuração do programa.

        Returns:
            Tuple (is_valid, errors)
            - is_valid: True se válido
            - errors: Lista de mensagens de erro
        """
        errors = []

        # Aba 1: Dados do Programa
        if not self.stencil_code:
            errors.append("Código do stencil é obrigatório")
        if not self.program_name:
            errors.append("Nome do programa é obrigatório")

        # Aba 2: Gerber
        if not self.gerber_file:
            errors.append("Arquivo Gerber não foi carregado")
        if self.aperture_count == 0:
            errors.append("Gerber não contém apertures")

        # Aba 3: Fiduciais
        if (self.fiducials.fiducial1["x"] == 0.0 and self.fiducials.fiducial1["y"] == 0.0) or \
           (self.fiducials.fiducial2["x"] == 0.0 and self.fiducials.fiducial2["y"] == 0.0):
            errors.append("Fiduciais não foram definidos")

        # Aba 4: Mosaico
        if self.mosaic.total_fovs == 0:
            errors.append("Mosaico não foi capturado")

        # Aba 5: Alinhamento
        if self.alignment.alignment_score < 70.0:
            errors.append(f"Score de alinhamento baixo: {self.alignment.alignment_score:.1f}%")

        # Aba 6: Janelas de Inspeção
        if self.configured_groups == 0:
            errors.append("Nenhum grupo de inspeção configurado")
        if self.confirmed_groups == 0:
            errors.append("Nenhum grupo de inspeção confirmado")

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_estimated_execution_time(self) -> Dict[str, Any]:
        """
        Estima tempo de execução da inspeção.

        Returns:
            Dicionário com estimativas em minutos
        """
        # Estimativas baseadas em número de FOVs e aberturas
        fov_time_seconds = 2.0  # 2 segundos por FOV
        aperture_time_seconds = 0.01  # 10ms por aperture

        total_fov_time = self.mosaic.total_fovs * fov_time_seconds
        total_aperture_time = self.total_apertures * aperture_time_seconds
        alignment_time = 5.0  # 5 segundos para alinhamento
        report_time = 10.0  # 10 segundos para gerar relatório

        total_seconds = total_fov_time + total_aperture_time + alignment_time + report_time
        total_minutes = total_seconds / 60.0

        return {
            "total_seconds": round(total_seconds, 1),
            "total_minutes": round(total_minutes, 1),
            "fov_capture_time": round(total_fov_time, 1),
            "inspection_time": round(total_aperture_time, 1),
            "alignment_time": alignment_time,
            "report_time": report_time,
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo do programa para exibição.

        Returns:
            Dicionário com informações resumidas
        """
        is_valid, errors = self.validate()
        execution_time = self.get_estimated_execution_time()

        return {
            "stencil_code": self.stencil_code,
            "program_name": self.program_name,
            "version": self.version,
            "gerber_file": self.gerber_file,
            "aperture_count": self.aperture_count,
            "fiducial_positions": [
                self.fiducials.fiducial1,
                self.fiducials.fiducial2,
            ],
            "alignment": {
                "translation_x": self.alignment.translation_x,
                "translation_y": self.alignment.translation_y,
                "rotation": self.alignment.rotation,
                "scale": self.alignment.scale,
                "score": self.alignment.alignment_score,
            },
            "mosaic": {
                "grid": f"{self.mosaic.grid_rows}×{self.mosaic.grid_cols}",
                "total_fovs": self.mosaic.total_fovs,
            },
            "inspection": {
                "total_groups": len(self.inspection_groups),
                "configured_groups": self.configured_groups,
                "confirmed_groups": self.confirmed_groups,
                "total_apertures": self.total_apertures,
            },
            "execution_time": execution_time,
            "is_valid": is_valid,
            "errors": errors,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }

    def get_file_path(self) -> str:
        """
        Retorna caminho padrão para salvar o programa.

        Returns:
            Caminho do arquivo JSON
        """
        from pathlib import Path

        # Cria nome de arquivo seguro
        safe_name = self.program_name.replace(" ", "_").replace("/", "_")
        filename = f"{self.stencil_code}_{safe_name}_{self.version}.json"

        # Salva em data/inspection_programs/
        programs_dir = Path("data/inspection_programs")
        programs_dir.mkdir(parents=True, exist_ok=True)

        return str(programs_dir / filename)
