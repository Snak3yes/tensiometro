# -*- coding: utf-8 -*-
"""
recipe_manager.py
-----------------
Sistema de gerenciamento de receitas para inspeção de stencils.

Uma receita contém todas as configurações necessárias para inspecionar
um modelo específico de stencil:
- Informações básicas (nome, ID, dimensões)
- Configuração de medição de tensão
- Configuração de captura de imagem
- Configuração de inspeção visual (opcional)

Autor: Sistema AOI Tensiometro
Data: 2024-12-10
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path

from aoi_lib.config_manager import AOIConfigManager
from aoi_lib.runtime_paths import get_runtime_path
from aoi_lib.system_change_log import get_system_change_log

logger = logging.getLogger(__name__)

# Diretório padrão para receitas
DEFAULT_RECIPES_DIR = "recipes"

# Limites da máquina (para validação)
MACHINE_LIMITS = {
    "max_width_mm": 800.0,
    "max_height_mm": 800.0,
    "min_step_mm": 0.1,
    "min_tension": 5.0,
    "max_tension": 100.0
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Point2D:
    """Ponto 2D (X, Y)."""
    x: float = 0.0
    y: float = 0.0
    
    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Point2D':
        return cls(x=data.get("x", 0.0), y=data.get("y", 0.0))


@dataclass
class Point3D:
    """Ponto 3D (X, Y, Z)."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y, "z": self.z}
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Point3D':
        return cls(
            x=data.get("x", 0.0),
            y=data.get("y", 0.0),
            z=data.get("z", 0.0)
        )


@dataclass
class StencilInfo:
    """Informações do stencil."""
    width_mm: float = 400.0
    height_mm: float = 300.0
    thickness_mm: float = 0.12
    material: str = "Inox"
    notes: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StencilInfo':
        return cls(
            width_mm=data.get("width_mm", 400.0),
            height_mm=data.get("height_mm", 300.0),
            thickness_mm=data.get("thickness_mm", 0.12),
            material=data.get("material", "Inox"),
            notes=data.get("notes", "")
        )


@dataclass
class TensionAcceptance:
    """Critérios de aceitação para tensão."""
    min_tension: float = 25.0  # N/cm² mínimo aceitável
    max_tension: float = 45.0  # N/cm² máximo aceitável
    warning_low: float = 28.0  # Abaixo = warning
    warning_high: float = 42.0  # Acima = warning
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TensionAcceptance':
        return cls(
            min_tension=data.get("min_tension", 25.0),
            max_tension=data.get("max_tension", 45.0),
            warning_low=data.get("warning_low", 28.0),
            warning_high=data.get("warning_high", 42.0)
        )
        
    def classify(self, value: float) -> str:
        """Classifica um valor de tensão."""
        if value < self.min_tension or value > self.max_tension:
            return "NOK"
        if value < self.warning_low or value > self.warning_high:
            return "WARNING"
        return "OK"


@dataclass
class TensionConfig:
    """Configuração de medição de tensão."""
    enabled: bool = False
    grid_rows: int = 3
    grid_cols: int = 3
    start_point: Point2D = field(default_factory=Point2D)
    end_point: Point2D = field(default_factory=lambda: Point2D(300.0, 200.0))
    acceptance: TensionAcceptance = field(default_factory=TensionAcceptance)
    measurement_pattern_name: str = ""
    measurement_height: float = 5.0
    movement_height: float = 10.0
    stabilization_time_ms: int = 500
    feed_rate: Optional[float] = None
    
    # Campos restaurados para compatibilidade
    z_start: float = 0.0
    z_end: float = -5.0
    z_speed: float = 100.0
    
    def to_dict(self) -> Dict:
        return {
            "enabled": self.enabled,
            "grid_rows": self.grid_rows,
            "grid_cols": self.grid_cols,
            "start_point": self.start_point.to_dict(),
            "end_point": self.end_point.to_dict(),
            "acceptance": self.acceptance.to_dict(),
            "measurement_pattern_name": self.measurement_pattern_name,
            "measurement_height": self.measurement_height,
            "movement_height": self.movement_height,
            "stabilization_time_ms": self.stabilization_time_ms,
            "feed_rate": self.feed_rate,
            "z_start": self.z_start,
            "z_end": self.z_end,
            "z_speed": self.z_speed
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TensionConfig':
        return cls(
            enabled=data.get("enabled", False),
            grid_rows=data.get("grid_rows", 3),
            grid_cols=data.get("grid_cols", 3),
            start_point=Point2D.from_dict(data.get("start_point", {})),
            end_point=Point2D.from_dict(data.get("end_point", {"x": 300.0, "y": 200.0})),
            acceptance=TensionAcceptance.from_dict(data.get("acceptance", {})),
            measurement_pattern_name=data.get("measurement_pattern_name", ""),
            measurement_height=data.get("measurement_height", data.get("z_end", 5.0)),
            movement_height=data.get("movement_height", data.get("z_start", 10.0)),
            stabilization_time_ms=data.get("stabilization_time_ms", 500),
            feed_rate=data.get("feed_rate"),
            z_start=data.get("z_start", 0.0),
            z_end=data.get("z_end", -5.0),
            z_speed=data.get("z_speed", 100.0)
        )


@dataclass
class CaptureConfig:
    """Configuração de captura de imagem (mosaico)."""
    enabled: bool = True
    step_x: float = 50.0  # Passo em mm
    step_y: float = 50.0
    capture_delay_ms: int = 200
    backlight_enabled: bool = False
    origin: Point2D = field(default_factory=Point2D)
    end: Point2D = field(default_factory=lambda: Point2D(300.0, 200.0))
    
    # Campo restaurado
    feed_rate: float = 2000.0
    
    def to_dict(self) -> Dict:
        return {
            "enabled": self.enabled,
            "step_x": self.step_x,
            "step_y": self.step_y,
            "capture_delay_ms": self.capture_delay_ms,
            "backlight_enabled": self.backlight_enabled,
            "origin": self.origin.to_dict(),
            "end": self.end.to_dict(),
            "feed_rate": self.feed_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CaptureConfig':
        return cls(
            enabled=data.get("enabled", True),
            step_x=data.get("step_x", 50.0),
            step_y=data.get("step_y", 50.0),
            capture_delay_ms=data.get("capture_delay_ms", 200),
            backlight_enabled=data.get("backlight_enabled", False),
            origin=Point2D.from_dict(data.get("origin", {})),
            end=Point2D.from_dict(data.get("end", {"x": 300.0, "y": 200.0})),
            feed_rate=data.get("feed_rate", 2000.0)
        )


@dataclass
class InspectionConfig:
    """Configuração de inspeção visual (AOI)."""
    enabled: bool = True
    default_min_percent: int = 70  # Mínimo % de área limpa para considerar OK
    target_color: str = "black"    # Cor esperada do furo (black/white)
    default_threshold: int = 128   # Threshold de binarização padrão
    
    # Campo restaurado (parece que o teste esperava)
    gerber_file: str = ""
    masks: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "enabled": self.enabled,
            "default_min_percent": self.default_min_percent,
            "target_color": self.target_color,
            "default_threshold": self.default_threshold,
            "gerber_file": self.gerber_file,
            "masks": self.masks
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InspectionConfig':
        return cls(
            enabled=data.get("enabled", True),
            default_min_percent=data.get("default_min_percent", 70),
            target_color=data.get("target_color", "black"),
            default_threshold=data.get("default_threshold", 128),
            gerber_file=data.get("gerber_file", ""),
            masks=data.get("masks", [])
        )


@dataclass
class Recipe:
    """
    Receita completa de inspeção.
    """
    name: str
    recipe_id: str = ""  # Opcional na criação, gerado auto
    version: str = "1.0"
    created_at: str = ""
    modified_at: str = ""
    created_by: str = ""
    
    # Configurações
    stencil: StencilInfo = field(default_factory=StencilInfo)
    tension: TensionConfig = field(default_factory=TensionConfig)
    capture: CaptureConfig = field(default_factory=CaptureConfig)
    inspection: InspectionConfig = field(default_factory=InspectionConfig)
    
    def __post_init__(self):
        """Inicializa timestamps se não fornecidos."""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.modified_at:
            self.modified_at = now
        if not self.recipe_id:
            # Gera ID baseado no timestamp com microsegundos para evitar colisão
            self.recipe_id = f"RECIPE_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def to_dict(self) -> Dict:
        """Serializa a receita para dicionário."""
        return {
            "version": self.version,
            "recipe_id": self.recipe_id,
            "name": self.name,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "created_by": self.created_by,
            "stencil": self.stencil.to_dict(),
            "tension_config": self.tension.to_dict(),
            "capture_config": self.capture.to_dict(),
            "inspection_config": self.inspection.to_dict()
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Serializa a receita para JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Recipe':
        """Cria receita a partir de dicionário."""
        return cls(
            recipe_id=data.get("recipe_id", ""),
            name=data.get("name", "Nova Receita"),
            version=data.get("version", "1.0"),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            created_by=data.get("created_by", ""),
            stencil=StencilInfo.from_dict(data.get("stencil", {})),
            tension=TensionConfig.from_dict(data.get("tension_config", {})),
            capture=CaptureConfig.from_dict(data.get("capture_config", {})),
            inspection=InspectionConfig.from_dict(data.get("inspection_config", {}))
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Recipe':
        """Cria receita a partir de JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def update_modified(self):
        """Atualiza timestamp de modificação."""
        self.modified_at = datetime.now().isoformat()
    
    def validate(self) -> List[str]:
        """
        Valida a receita e retorna lista de erros.
        
        Returns:
            Lista vazia se válida, ou lista de mensagens de erro.
        """
        errors = []
        
        # 1. Validação Básica
        if not self.name or self.name.strip() == "":
            errors.append("Nome da receita não pode estar vazio")
        
        # 2. Validação Stencil
        if self.stencil.width_mm <= 0:
            errors.append("Largura do stencil deve ser maior que zero")
        elif self.stencil.width_mm > MACHINE_LIMITS["max_width_mm"]:
            errors.append(f"Largura excede limite da máquina ({MACHINE_LIMITS['max_width_mm']}mm)")
            
        if self.stencil.height_mm <= 0:
            errors.append("Altura do stencil deve ser maior que zero")
        elif self.stencil.height_mm > MACHINE_LIMITS["max_height_mm"]:
            errors.append(f"Altura excede limite da máquina ({MACHINE_LIMITS['max_height_mm']}mm)")
        
        # 3. Validação Tensão
        if self.tension.enabled:
            if self.tension.grid_rows < 1 or self.tension.grid_cols < 1:
                errors.append("Grid de tensão deve ter pelo menos 1x1")
            
            acc = self.tension.acceptance
            if acc.min_tension < MACHINE_LIMITS["min_tension"]:
                errors.append(f"Tensão mínima abaixo do limite físico ({MACHINE_LIMITS['min_tension']})")
            if acc.max_tension > MACHINE_LIMITS["max_tension"]:
                errors.append(f"Tensão máxima acima do limite físico ({MACHINE_LIMITS['max_tension']})")
            if acc.min_tension >= acc.max_tension:
                errors.append("Tensão mínima deve ser menor que máxima")
            
            # Os pontos de medição são coordenadas absolutas da máquina.
            # Portanto, validamos apenas consistência geométrica básica.
            sp = self.tension.start_point
            ep = self.tension.end_point
            if sp.x < 0 or sp.y < 0 or ep.x < 0 or ep.y < 0:
                errors.append("Pontos de medição não podem ser negativos")
            if ep.x <= sp.x:
                errors.append("Ponto final X deve ser maior que o ponto inicial X")
            if ep.y <= sp.y:
                errors.append("Ponto final Y deve ser maior que o ponto inicial Y")
        
        # 4. Validação Captura
        if self.capture.step_x < MACHINE_LIMITS["min_step_mm"] or self.capture.step_y < MACHINE_LIMITS["min_step_mm"]:
            errors.append(f"Steps de captura muito pequenos (mínimo {MACHINE_LIMITS['min_step_mm']}mm)")
            
        return errors


# =============================================================================
# RECIPE MANAGER
# =============================================================================

class RecipeManager:
    """
    Gerenciador de receitas.
    Responsável por salvar, carregar e listar receitas em disco.
    """
    
    def __init__(self, recipes_dir: str = None, config_manager: AOIConfigManager | None = None):
        """
        Inicializa o RecipeManager.
        
        Args:
            recipes_dir: Diretório onde as receitas serão salvas.
                         Se None, usa diretório padrão relativo ao projeto.
        """
        if recipes_dir is None:
            # Usa diretório relativo ao projeto
            recipes_dir = get_runtime_path(DEFAULT_RECIPES_DIR)
        
        self.recipes_dir = Path(recipes_dir)
        self._ensure_directory()
        self.config_manager = config_manager or AOIConfigManager()
        
        self.current_recipe: Optional[Recipe] = None
        self._recipes_cache: Dict[str, Recipe] = {}
        
        logger.info(f"RecipeManager inicializado em: {self.recipes_dir}")

    def get_global_tension_acceptance(self) -> TensionAcceptance:
        """Retorna os critérios globais de tensão configurados na aplicação."""
        return TensionAcceptance(
            min_tension=float(
                self.config_manager.get("tension_criteria", "min_tension", default=25.0)
            ),
            max_tension=float(
                self.config_manager.get("tension_criteria", "max_tension", default=45.0)
            ),
            warning_low=float(
                self.config_manager.get("tension_criteria", "warning_low", default=28.0)
            ),
            warning_high=float(
                self.config_manager.get("tension_criteria", "warning_high", default=42.0)
            ),
        )

    def _apply_global_tension_acceptance(self, recipe: Recipe) -> Recipe:
        """Sincroniza a receita com os critérios globais de tensão."""
        recipe.tension.acceptance = self.get_global_tension_acceptance()
        return recipe
    
    def _ensure_directory(self):
        """Cria o diretório de receitas se não existir."""
        self.recipes_dir.mkdir(parents=True, exist_ok=True)
    
    def list_recipes(self) -> List[Dict]:
        """
        Lista todas as receitas disponíveis.
        
        Returns:
            Lista de dicionários com metadados das receitas.
        """
        recipes = []
        if not self.recipes_dir.exists():
            return recipes
            
        for file_path in self.recipes_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    recipes.append({
                        'name': data.get('name', 'Sem Nome'),
                        'recipe_id': data.get('recipe_id', file_path.stem),
                        'modified_at': data.get('modified_at', ''),
                        'file_path': str(file_path)
                    })
            except Exception as e:
                logger.warning(f"Erro ao ler receita {file_path}: {e}")
        
        # Ordena por data de modificação (mais recente primeiro)
        recipes.sort(key=lambda x: x.get('modified_at', ''), reverse=True)
        return recipes
    
    def load_recipe(self, recipe_id: str) -> Optional[Recipe]:
        """
        Carrega uma receita pelo ID.
        
        Args:
            recipe_id: ID da receita ou nome do arquivo (sem extensão)
        
        Returns:
            Objeto Recipe ou None se não encontrada
        """
        # Tenta encontrar o arquivo
        file_path = self.recipes_dir / f"{recipe_id}.json"
        
        if not file_path.exists():
            # Tenta buscar pelo recipe_id ou nome dentro dos arquivos
            for fp in self.recipes_dir.glob("*.json"):
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('recipe_id') == recipe_id or data.get('name') == recipe_id:
                            file_path = fp
                            break
                except:
                    continue
        
        if not file_path.exists():
            logger.error(f"Receita não encontrada: {recipe_id}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recipe = self._apply_global_tension_acceptance(Recipe.from_dict(data))
            self.current_recipe = recipe
            self._recipes_cache[recipe.recipe_id] = recipe
            
            logger.info(f"Receita carregada: {recipe.name} ({recipe.recipe_id})")
            return recipe
        
        except Exception as e:
            logger.error(f"Erro ao carregar receita {recipe_id}: {e}")
            return None
    
    def save_recipe(self, recipe: Recipe, filename: str = None) -> bool:
        """
        Salva uma receita em arquivo.
        
        Args:
            recipe: Objeto Recipe para salvar
            filename: Nome do arquivo (sem extensão). 
                      Se None, usa recipe_id.
        
        Returns:
            True se salvou com sucesso
        """
        # Atualiza timestamp de modificação
        recipe.update_modified()
        self._apply_global_tension_acceptance(recipe)
        
        # Valida
        errors = recipe.validate()
        if errors:
            logger.error(f"Receita inválida: {errors}")
            return False
        
        # Define nome do arquivo
        if filename is None:
            # Sanitiza o recipe_id para nome de arquivo
            filename = "".join(c for c in recipe.recipe_id if c.isalnum() or c in ('_', '-'))

        file_path = self.recipes_dir / f"{filename}.json"
        old_data = None
        action = "created"
        description = f"Receita criada: {recipe.name}"
        if file_path.exists():
            action = "updated"
            description = f"Receita atualizada: {recipe.name}"
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao ler receita anterior para auditoria: {e}")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(recipe.to_json(indent=2))

            self._recipes_cache[recipe.recipe_id] = recipe
            get_system_change_log().log_event(
                category="recipe",
                action=action,
                target_type="recipe",
                target_id=recipe.recipe_id,
                description=description,
                changes={"old": old_data, "new": recipe.to_dict()},
                metadata={"file_path": str(file_path), "recipe_name": recipe.name},
            )
            logger.info(f"Receita salva: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao salvar receita: {e}")
            return False
    
    def create_recipe(self, name: str, **kwargs) -> Recipe:
        """
        Cria uma nova receita.
        
        Args:
            name: Nome da receita
            **kwargs: Outros parâmetros da receita
            
        Returns:
            Nova receita (não salva ainda)
        """
        recipe = Recipe(
            name=name,
            **kwargs
        )
        return self._apply_global_tension_acceptance(recipe)
    
    def delete_recipe(self, recipe_id: str) -> bool:
        """
        Remove uma receita.
        
        Args:
            recipe_id: ID da receita
            
        Returns:
            True se removida com sucesso
        """
        file_path = self.recipes_dir / f"{recipe_id}.json"
        
        if not file_path.exists():
            # Tenta buscar pelo conteúdo
            recipe = self.load_recipe(recipe_id)
            if not recipe:
                return False
            # Recalcula path (caso load_recipe tenha achado por outro nome)
            # Mas load_recipe não retorna path.
            # Vamos assumir que ID = filename por padrão.
            # Se não, busca arquivo
            for fp in self.recipes_dir.glob("*.json"):
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('recipe_id') == recipe_id:
                            file_path = fp
                            break
                except:
                    continue
        
        if file_path.exists():
            try:
                old_data = None
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        old_data = json.load(f)
                except Exception as e:
                    logger.warning(f"Erro ao ler receita para auditoria antes da exclusao: {e}")
                os.remove(file_path)
                self._recipes_cache.pop(recipe_id, None)
                if self.current_recipe and self.current_recipe.recipe_id == recipe_id:
                    self.current_recipe = None
                get_system_change_log().log_event(
                    category="recipe",
                    action="deleted",
                    target_type="recipe",
                    target_id=recipe_id,
                    description=f"Receita removida: {recipe_id}",
                    changes={"old": old_data, "new": None},
                    metadata={"file_path": str(file_path)},
                )
                logger.info(f"Receita removida: {recipe_id}")
                return True
            except Exception as e:
                logger.error(f"Erro ao remover receita: {e}")
                return False
        
        return False
        
    def duplicate_recipe(self, recipe_id: str, new_name: str) -> Optional[Recipe]:
        """
        Duplica uma receita existente.
        
        Args:
            recipe_id: ID da receita original
            new_name: Nome da nova receita
            
        Returns:
            Nova receita salva ou None
        """
        original = self.load_recipe(recipe_id)
        if not original:
            return None
            
        # Cria cópia dos dados
        data = original.to_dict()
        data['name'] = new_name
        data['recipe_id'] = "" # Reset ID para gerar novo
        data['created_at'] = "" # Reset datas
        data['modified_at'] = ""
        
        new_recipe = Recipe.from_dict(data)
        
        if self.save_recipe(new_recipe):
            return new_recipe
        return None

    def set_current_recipe(self, recipe: Recipe):
        """Define a receita atual."""
        self.current_recipe = recipe

    def get_current_recipe(self) -> Optional[Recipe]:
        """Retorna a receita atual."""
        return self.current_recipe

# =============================================================================
# UTILS
# =============================================================================

def create_sample_recipe() -> Recipe:
    """Cria uma receita de exemplo."""
    r = Recipe(name="Stencil Exemplo PCB", recipe_id="SAMPLE_001")
    
    r.stencil.width_mm = 400
    r.stencil.height_mm = 300
    r.stencil.material = "Inox"
    
    r.tension.enabled = True
    r.tension.grid_rows = 3
    r.tension.grid_cols = 3
    r.tension.start_point = Point2D(50, 50)
    r.tension.end_point = Point2D(350, 250)
    
    r.capture.enabled = True
    r.capture.step_x = 50
    r.capture.step_y = 50
    
    return r
