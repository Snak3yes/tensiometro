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

logger = logging.getLogger(__name__)

# Diretório padrão para receitas
DEFAULT_RECIPES_DIR = "recipes"


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
        """
        Classifica um valor de tensão.
        
        Returns:
            'OK', 'WARNING', ou 'NOK'
        """
        if value < self.min_tension or value > self.max_tension:
            return 'NOK'
        if value < self.warning_low or value > self.warning_high:
            return 'WARNING'
        return 'OK'


@dataclass
class TensionConfig:
    """Configuração de medição de tensão."""
    enabled: bool = True
    grid_rows: int = 5
    grid_cols: int = 5
    start_point: Point2D = field(default_factory=Point2D)
    end_point: Point2D = field(default_factory=lambda: Point2D(350, 250))
    z_start: float = 0.0  # Altura inicial do sensor
    z_end: float = -5.0  # Altura final (sobre o stencil)
    z_speed: float = 100.0  # Velocidade de descida mm/min
    acceptance: TensionAcceptance = field(default_factory=TensionAcceptance)
    
    def to_dict(self) -> Dict:
        return {
            "enabled": self.enabled,
            "grid": {"rows": self.grid_rows, "cols": self.grid_cols},
            "start_point": self.start_point.to_dict(),
            "end_point": self.end_point.to_dict(),
            "z_params": {
                "start_z": self.z_start,
                "end_z": self.z_end,
                "speed": self.z_speed
            },
            "acceptance": self.acceptance.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TensionConfig':
        grid = data.get("grid", {})
        z_params = data.get("z_params", {})
        return cls(
            enabled=data.get("enabled", True),
            grid_rows=grid.get("rows", 5),
            grid_cols=grid.get("cols", 5),
            start_point=Point2D.from_dict(data.get("start_point", {})),
            end_point=Point2D.from_dict(data.get("end_point", {})),
            z_start=z_params.get("start_z", 0.0),
            z_end=z_params.get("end_z", -5.0),
            z_speed=z_params.get("speed", 100.0),
            acceptance=TensionAcceptance.from_dict(data.get("acceptance", {}))
        )


@dataclass
class CaptureConfig:
    """Configuração de captura de imagem/mapa."""
    origin: Point2D = field(default_factory=Point2D)
    end: Point2D = field(default_factory=lambda: Point2D(400, 300))
    step_x: float = 50.0  # Passo em X (mm)
    step_y: float = 50.0  # Passo em Y (mm)
    feed_rate: float = 2000.0  # Velocidade de movimento (mm/min)
    capture_delay_ms: int = 200  # Delay após movimento (ms)
    backlight_enabled: bool = True  # Usar backlight na captura
    
    def to_dict(self) -> Dict:
        return {
            "origin": self.origin.to_dict(),
            "end": self.end.to_dict(),
            "step_x": self.step_x,
            "step_y": self.step_y,
            "feed_rate": self.feed_rate,
            "capture_delay_ms": self.capture_delay_ms,
            "backlight_enabled": self.backlight_enabled
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'CaptureConfig':
        return cls(
            origin=Point2D.from_dict(data.get("origin", {})),
            end=Point2D.from_dict(data.get("end", {})),
            step_x=data.get("step_x", 50.0),
            step_y=data.get("step_y", 50.0),
            feed_rate=data.get("feed_rate", 2000.0),
            capture_delay_ms=data.get("capture_delay_ms", 200),
            backlight_enabled=data.get("backlight_enabled", True)
        )


@dataclass
class InspectionConfig:
    """Configuração de inspeção visual (para uso futuro com Gerber)."""
    enabled: bool = False
    gerber_file: Optional[str] = None  # Caminho do arquivo Gerber
    masks: List[Dict] = field(default_factory=list)  # Máscaras geradas
    default_threshold: int = 128  # Threshold padrão
    default_min_percent: float = 95.0  # % mínimo de aprovação
    target_color: str = "white"  # 'white' ou 'black'
    
    def to_dict(self) -> Dict:
        return {
            "enabled": self.enabled,
            "gerber_file": self.gerber_file,
            "masks": self.masks,
            "default_threshold": self.default_threshold,
            "default_min_percent": self.default_min_percent,
            "target_color": self.target_color
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InspectionConfig':
        return cls(
            enabled=data.get("enabled", False),
            gerber_file=data.get("gerber_file"),
            masks=data.get("masks", []),
            default_threshold=data.get("default_threshold", 128),
            default_min_percent=data.get("default_min_percent", 95.0),
            target_color=data.get("target_color", "white")
        )


@dataclass
class Recipe:
    """
    Receita completa para inspeção de um modelo de stencil.
    
    Contém todas as configurações necessárias para:
    - Identificar o modelo de stencil
    - Medir tensão superficial
    - Capturar imagens para mosaico
    - Inspecionar aberturas (futuro)
    """
    # Metadados
    recipe_id: str = ""
    name: str = "Nova Receita"
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
            # Gera ID baseado no timestamp
            self.recipe_id = f"RECIPE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
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
        
        if not self.name or self.name.strip() == "":
            errors.append("Nome da receita não pode estar vazio")
        
        if self.stencil.width_mm <= 0:
            errors.append("Largura do stencil deve ser maior que zero")
        
        if self.stencil.height_mm <= 0:
            errors.append("Altura do stencil deve ser maior que zero")
        
        if self.tension.enabled:
            if self.tension.grid_rows < 1 or self.tension.grid_cols < 1:
                errors.append("Grid de tensão deve ter pelo menos 1x1")
            
            acc = self.tension.acceptance
            if acc.min_tension >= acc.max_tension:
                errors.append("Tensão mínima deve ser menor que máxima")
        
        if self.capture.step_x <= 0 or self.capture.step_y <= 0:
            errors.append("Steps de captura devem ser maiores que zero")
        
        return errors


# =============================================================================
# RECIPE MANAGER
# =============================================================================

class RecipeManager:
    """
    Gerenciador de receitas.
    
    Responsável por:
    - Listar receitas disponíveis
    - Carregar/Salvar receitas
    - Criar/Editar/Excluir receitas
    - Validar receitas
    """
    
    def __init__(self, recipes_dir: str = None):
        """
        Inicializa o gerenciador de receitas.
        
        Args:
            recipes_dir: Diretório para armazenar receitas.
                         Se None, usa DEFAULT_RECIPES_DIR.
        """
        self.recipes_dir = Path(recipes_dir or DEFAULT_RECIPES_DIR)
        self._ensure_recipes_dir()
        
        self.current_recipe: Optional[Recipe] = None
        self._recipes_cache: Dict[str, Recipe] = {}
    
    def _ensure_recipes_dir(self):
        """Garante que o diretório de receitas existe."""
        self.recipes_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Diretório de receitas: {self.recipes_dir.absolute()}")
    
    def list_recipes(self) -> List[Dict[str, str]]:
        """
        Lista todas as receitas disponíveis.
        
        Returns:
            Lista de dicionários com 'recipe_id', 'name', 'modified_at'
        """
        recipes = []
        
        for file_path in self.recipes_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    recipes.append({
                        'recipe_id': data.get('recipe_id', file_path.stem),
                        'name': data.get('name', 'Sem nome'),
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
            # Tenta buscar pelo recipe_id dentro dos arquivos
            for fp in self.recipes_dir.glob("*.json"):
                try:
                    with open(fp, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get('recipe_id') == recipe_id:
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
            
            recipe = Recipe.from_dict(data)
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
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(recipe.to_json(indent=2))
            
            self._recipes_cache[recipe.recipe_id] = recipe
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
            Objeto Recipe criado
        """
        recipe = Recipe(name=name, **kwargs)
        self.current_recipe = recipe
        return recipe
    
    def delete_recipe(self, recipe_id: str) -> bool:
        """
        Exclui uma receita.
        
        Args:
            recipe_id: ID da receita
        
        Returns:
            True se excluiu com sucesso
        """
        file_path = self.recipes_dir / f"{recipe_id}.json"
        
        if not file_path.exists():
            # Busca pelo ID
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
                file_path.unlink()
                self._recipes_cache.pop(recipe_id, None)
                logger.info(f"Receita excluída: {recipe_id}")
                return True
            except Exception as e:
                logger.error(f"Erro ao excluir receita: {e}")
                return False
        
        logger.warning(f"Receita não encontrada para exclusão: {recipe_id}")
        return False
    
    def duplicate_recipe(self, recipe_id: str, new_name: str) -> Optional[Recipe]:
        """
        Duplica uma receita existente.
        
        Args:
            recipe_id: ID da receita original
            new_name: Nome para a nova receita
        
        Returns:
            Nova receita ou None se falhar
        """
        original = self.load_recipe(recipe_id)
        if not original:
            return None
        
        # Cria cópia
        new_recipe = Recipe.from_dict(original.to_dict())
        new_recipe.name = new_name
        new_recipe.recipe_id = f"RECIPE_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_recipe.created_at = datetime.now().isoformat()
        new_recipe.modified_at = new_recipe.created_at
        
        return new_recipe
    
    def get_current_recipe(self) -> Optional[Recipe]:
        """Retorna a receita atualmente carregada."""
        return self.current_recipe
    
    def set_current_recipe(self, recipe: Recipe):
        """Define a receita atual."""
        self.current_recipe = recipe


# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def create_sample_recipe() -> Recipe:
    """
    Cria uma receita de exemplo para testes.
    
    Returns:
        Receita de exemplo
    """
    recipe = Recipe(
        name="Stencil Exemplo PCB",
        recipe_id="SAMPLE_001",
        stencil=StencilInfo(
            width_mm=400,
            height_mm=300,
            thickness_mm=0.12,
            material="Inox 304",
            notes="Stencil de exemplo para testes"
        ),
        tension=TensionConfig(
            enabled=True,
            grid_rows=5,
            grid_cols=5,
            start_point=Point2D(50, 50),
            end_point=Point2D(350, 250),
            z_start=0,
            z_end=-5,
            z_speed=100,
            acceptance=TensionAcceptance(
                min_tension=25.0,
                max_tension=45.0,
                warning_low=28.0,
                warning_high=42.0
            )
        ),
        capture=CaptureConfig(
            origin=Point2D(0, 0),
            end=Point2D(400, 300),
            step_x=50,
            step_y=50,
            feed_rate=2000,
            capture_delay_ms=200,
            backlight_enabled=True
        ),
        inspection=InspectionConfig(
            enabled=False,
            default_threshold=128,
            default_min_percent=95.0
        )
    )
    return recipe


# =============================================================================
# TESTE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== Teste do Sistema de Receitas ===\n")
    
    # Cria gerenciador
    manager = RecipeManager()
    
    # Cria receita de exemplo
    recipe = create_sample_recipe()
    print(f"Receita criada: {recipe.name}")
    print(f"  ID: {recipe.recipe_id}")
    print(f"  Stencil: {recipe.stencil.width_mm}x{recipe.stencil.height_mm} mm")
    print(f"  Tensão: Grid {recipe.tension.grid_rows}x{recipe.tension.grid_cols}")
    print(f"  Aceitação: {recipe.tension.acceptance.min_tension}-{recipe.tension.acceptance.max_tension} N/cm²")
    
    # Valida
    errors = recipe.validate()
    if errors:
        print(f"\n❌ Erros de validação: {errors}")
    else:
        print("\n✅ Receita válida")
    
    # Salva
    if manager.save_recipe(recipe):
        print(f"\n✅ Receita salva em: {manager.recipes_dir}")
    
    # Lista receitas
    recipes = manager.list_recipes()
    print(f"\n📋 Receitas disponíveis: {len(recipes)}")
    for r in recipes:
        print(f"  - {r['name']} ({r['recipe_id']})")
    
    # Testa classificação de tensão
    print("\n🎯 Teste de classificação de tensão:")
    acc = recipe.tension.acceptance
    for val in [20, 26, 30, 40, 44, 50]:
        result = acc.classify(val)
        print(f"  {val} N/cm² → {result}")
    
    print("\n=== Teste concluído! ===")
