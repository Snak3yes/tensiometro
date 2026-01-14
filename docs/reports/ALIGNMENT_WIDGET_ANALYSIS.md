# Análise: Alignment Widget - Fase 3 Refactoring

**Data:** 2026-01-14
**Track:** solid_refactoring_phase2_20260114
**Fase:** Phase 3 - Alignment Widget Refactoring (Task 3.1)
**Arquivo:** `consumo_lib/widgets/engenharia/alignment_widget.py`

## Resumo Executivo

**Arquivo analisado:** `alignment_widget.py` (1,179 linhas)
**Objetivo:** Reduzir para <600 linhas extraindo lógica de negócio para serviços
**Estratégia:** Separar UI → Serviços → Estado

## Estrutura Atual

### 1. Classes Identificadas

#### 1.1. `AlignmentState` (linhas 47-57)
**Tipo:** dataclass
**Responsabilidade:** Estado do alinhamento
**Campos:**
- `tx, ty` - Translação X/Y em pixels
- `angle` - Rotação em graus
- `scale` - Fator de escala
- `opacity` - Opacidade do overlay (0-1)
- `score` - Score de alinhamento (0-100)
- `fiducials_found` - Se fiduciais foram encontrados

**Status:** ✅ BEM DEFINIDO (pode ser melhorado/expandido)

#### 1.2. `AlignmentImageView` (linhas 59-347)
**Tipo:** QWidget customizado (herda QLabel)
**Responsabilidade:** Visualização com zoom/pan e arraste do overlay
**Métodos principais:**
- `set_mosaic()` - Define imagem do mosaico
- `set_gerber_overlay()` - Define overlay do Gerber
- `set_gerber_transform()` - Define transformação do overlay
- `fit_in_view()` - Ajusta zoom para caber na view
- `_update_display()` - Atualiza display da imagem

**Status:** ⚠️ RESPONSABILIDADE MISTA (UI + lógica de renderização)
- **Recomendação:** Manter como widget customizado, mas extrair lógica de transformação

#### 1.3. `AlignmentWidget` (linhas 349-1179)
**Tipo:** QWidget principal (engenharia wizard tab 5)
**Responsabilidade:** Widget de alinhamento do Gerber sobre mosaico
**Métodos públicos (22):**
- `set_mosaic()` - Define mosaico capturado
- `set_parsed_gerber()` - Define Gerber parseado
- `get_alignment()` - Retorna estado atual
- `apply_alignment()` - Aplica e salva transformação
- `is_valid()` - Verifica se estado é válido

**Métodos privados (20):**
- `_build_ui()` - Constrói interface
- `_connect_signals()` - Conecta signals
- `_render_gerber_overlay()` - **LÓGICA DE NEGÓCIO** (extrair)
- `_setup_fiducials()` - **LÓGICA DE NEGÓCIO** (extrair)
- `_align_with_coordinator()` - **LÓGICA DE NEGÓCIO** (extrair)
- `_align_with_legacy()` - **LÓGICA DE NEGÓCIO** (extrair)
- `_estimate_score()` - **LÓGICA DE NEGÓCIO** (extrair)
- `_update_score_display()` - Atualiza display de score
- `_update_validation()` - Atualiza estado de validação
- `_on_transform_changed()` - Handler de mudança de transformação
- `_on_opacity_changed()` - Handler de mudança de opacidade
- `_on_overlay_dragged()` - Handler de arraste do overlay
- `_on_auto_tune()` - Handler de auto-tuning
- `_on_reset()` - Handler de reset
- `_on_apply()` - Handler de aplicar

**Status:** ❌ MUITAS RESPONSABILIDADES (UI + lógica + estado)

## Responsabilidades Identificadas

### 1. Lógica de Template Matching (DEVE SER EXTRAÍDA)

**Localização:** Métodos `_align_with_coordinator()`, `_align_with_legacy()`
**Responsabilidade:** Buscar fiduciais usando template matching
**Complexidade:** Alta (envolve OpenCV, algoritmos de matching)

**O que deve ser extraído:**
```python
# NOVO: consumo_lib/services/template_matching_service.py
class TemplateMatchingService:
    def find_fiducials(
        self,
        image: np.ndarray,
        templates: list[FiducialTemplate],
        transform_hint: Optional[AlignmentTransform] = None
    ) -> list[FiducialMatchResult]:
        """Busca fiduciais na imagem usando template matching."""

    def calculate_match_score(self, results: list[FiducialMatchResult]) -> float:
        """Calcula score de matching (0-100)."""

    def estimate_transform(
        self,
        matches: list[FiducialMatchResult]
    ) -> AlignmentTransform:
        """Estima transformação baseada nos matches."""
```

**Dependências atuais:**
- `aoi_lib.fiducial_alignment.FiducialAligner`
- `aoi_lib.fiducial_alignment.FiducialTemplate`
- `aoi_lib.fiducial_alignment.FiducialMatchResult`
- `aoi_lib.fiducial_alignment.AlignmentTransform`

### 2. Lógica de Alinhamento Fiducial (DEVE SER EXTRAÍDA)

**Localização:** Métodos `_align_with_coordinator()`, `_align_with_legacy()`
**Responsabilidade:** Calcular transformação de alinhamento
**Complexidade:** Alta (geometria, matemática de transformações)

**O que deve ser extraído:**
```python
# NOVO: consumo_lib/services/fiducial_alignment_service.py
class FiducialAlignmentService:
    def align(
        self,
        image: np.ndarray,
        gerber_objects: list,
        templates: list[FiducialTemplate],
        initial_transform: Optional[AlignmentTransform] = None
    ) -> AlignmentResult:
        """Executa alinhamento fiducial completo."""

    def validate_transform(
        self,
        transform: AlignmentTransform,
        min_score: float = 70.0
    ) -> bool:
        """Valida se transformação é aceitável."""

    def refine_transform(
        self,
        transform: AlignmentTransform,
        image: np.ndarray,
        templates: list[FiducialTemplate]
    ) -> AlignmentTransform:
        """Refina transformação com busca adicional."""
```

**Dependências atuais:**
- `aoi_lib.fiducial_alignment.FiducialAligner`
- `aoi_lib.gerber_renderer.GerberRenderer`
- OpenCV (cv2, numpy)

### 3. Renderização do Gerber (PODE SER EXTRAÍDA)

**Localização:** Método `_render_gerber_overlay()`
**Responsabilidade:** Renderizar Gerber como overlay
**Complexidade:** Média (conversão coordenadas → pixmap)

**O que deve ser extraído:**
```python
# NOVO: consumo_lib/services/gerber_overlay_service.py
class GerberOverlayService:
    def render_to_pixmap(
        self,
        gerber_objects: list,
        transform: AlignmentTransform,
        view_size: Tuple[int, int],
        color: str = "#FF0000"
    ) -> QPixmap:
        """Renderiza Gerber como QPixmap com transformação aplicada."""

    def render_to_image(
        self,
        gerber_objects: list,
        transform: AlignmentTransform,
        view_size: Tuple[int, int]
    ) -> np.ndarray:
        """Renderiza Gerber como imagem numpy (OpenCV)."""
```

**Dependências atuais:**
- `aoi_lib.gerber_renderer.GerberRenderer`
- PyQt6 (QImage, QPixmap, QPainter)

### 4. Estado de Alinhamento (JÁ EXISTE, PODE SER EXPANDIDO)

**Localização:** dataclass `AlignmentState` (linhas 47-57)
**Responsabilidade:** Armazenar estado do alinhamento
**Status:** ✅ JÁ DEFINIDO (pode ser movido para models/)

**Melhorias sugeridas:**
```python
# MELHORADO: consumo_lib/models/alignment_state.py
from dataclasses import dataclass, field
from typing import Optional, list
from aoi_lib.fiducial_alignment import AlignmentTransform, FiducialMatchResult

@dataclass
class AlignmentState:
    """Estado completo do alinhamento."""
    # Transformação
    tx: float = 0.0
    ty: float = 0.0
    angle: float = 0.0
    scale: float = 1.0

    # Visualização
    opacity: float = 0.5
    zoom: float = 1.0

    # Resultados
    score: float = 0.0
    fiducials_found: bool = False
    fiducial_matches: list[FiducialMatchResult] = field(default_factory=list)

    # Metadata
    is_valid: bool = False
    timestamp: Optional[str] = None

    def to_transform(self) -> AlignmentTransform:
        """Converte para AlignmentTransform do aoi_lib."""
        return AlignmentTransform(
            tx=self.tx,
            ty=self.ty,
            angle=self.angle,
            scale=self.scale
        )

    def update_from_transform(self, transform: AlignmentTransform):
        """Atualiza estado a partir de AlignmentTransform."""
        self.tx = transform.tx
        self.ty = transform.ty
        self.angle = transform.angle
        self.scale = transform.scale

    @classmethod
    def from_dict(cls, data: dict) -> 'AlignmentState':
        """Cria estado a partir de dict (para serialização)."""
        return cls(**data)

    def to_dict(self) -> dict:
        """Converte estado para dict (para serialização)."""
        return asdict(self)
```

## Plano de Refatoração

### Fase 1: Criar Modelos (Task 3.1.5)
- [ ] Mover `AlignmentState` para `consumo_lib/models/alignment_state.py`
- [ ] Expandir `AlignmentState` com novos campos
- [ ] Adicionar métodos de conversão (to/from dict, to/from AlignmentTransform)

### Fase 2: Criar Serviços (Tasks 3.1.3, 3.1.4)
- [ ] Criar `consumo_lib/services/template_matching_service.py`
  - [ ] Extrair lógica de `_align_with_coordinator()`
  - [ ] Extrair lógica de `_align_with_legacy()`
  - [ ] Implementar `TemplateMatchingService`
  - [ ] Adicionar testes unitários (sem PyQt6)

- [ ] Criar `consumo_lib/services/fiducial_alignment_service.py`
  - [ ] Orquestrar alinhamento completo
  - [ ] Validar transformações
  - [ ] Refinar transformações
  - [ ] Adicionar testes unitários (sem PyQt6)

### Fase 3: Refatorar Widget (Task 3.1.6)
- [ ] Remover lógica de negócio do widget
- [ ] Injetar serviços via construtor
- [ ] Reduzir de 1,179 → <600 linhas
- [ ] Manter apenas UI e handlers

### Fase 4: Testes e Documentação (Tasks 3.1.7, 3.1.8)
- [ ] Testar serviços independentemente
- [ ] Testar widget com mocks
- [ ] Atualizar CLAUDE.md

## Análise de Complexidade

### Métodos Complexos (>50 linhas)

1. **`_align_with_coordinator()`** (linhas 856-960, ~104 linhas)
   - **Complexidade:** MUITO ALTA
   - **Responsabilidade:** Orquestrar alinhamento via EngineeringHardwareCoordinator
   - **Ação:** EXTRAIR para `FiducialAlignmentService`

2. **`_align_with_legacy()`** (linhas 961-1042, ~81 linhas)
   - **Complexidade:** MUITO ALTA
   - **Responsabilidade:** Orquestrar alinhamento via legado FiducialAligner
   - **Ação:** EXTRAIR para `FiducialAlignmentService`

3. **`_render_gerber_overlay()`** (linhas 712-747, ~35 linhas)
   - **Complexidade:** MÉDIA
   - **Responsabilidade:** Renderizar Gerber como QPixmap
   - **Ação:** EXTRAIR para `GerberOverlayService`

### Acoplamentos

**Acoplamento alto com:**
- `aoi_lib.fiducial_alignment` (4 classes)
- `aoi_lib.gerber_renderer.GerberRenderer`
- OpenCV (cv2, numpy)
- PyQt6 (muitos widgets)

**Próximos passos:**
- Inverter dependências (DIP)
- Injetar serviços via construtor
- Depender de abstrações (ABCs)

## Benefícios Esperados

### 1. Redução de Complexidade
- **Antes:** 1,179 linhas, métodos de ~100 linhas
- **Depois:** <600 linhas, métodos <30 linhas
- **Redução:** ~50% linhas, ~70% complexidade

### 2. Melhor Testabilidade
- Serviços testáveis sem PyQt6
- Widget testável com mocks
- Cobertura de testes >90%

### 3. Separação de Responsabilidades (SRP)
- Widget: Apenas UI e handlers
- Serviços: Lógica de negócio
- Model: Estado e serialização

### 4. Baixo Acoplamento
- Widget depende de abstrações (ABCs)
- Serviços independentes de UI
- Fácil substituir implementações

## Riscos e Mitigações

### Risco 1: Regressão em Funcionalidade Crítica
**Nível:** ALTO
**Mitigação:**
- Testes abrangentes antes de refatorar
- Manter backward compatibility
- Smoke test com hardware real após cada fase

### Risco 2: Performance
**Nível:** MÉDIO
**Mitigação:**
- Perfilar antes/depois
- Otimizar caminhos críticos
- Cache de renderização se necessário

### Risco 3: Complexidade de Migração
**Nível:** MÉDIO
**Mitigação:**
- Migração incremental (fase por fase)
- Testes contínuos
- Documentação detalhada

## Conclusão

**Recomendação:** ✅ **PROSSEGUIR com refatoração**

**Justificativa:**
1. Widget tem 1,179 linhas (objetivo: <600)
2. Muitas responsabilidades misturadas (UI + lógica + estado)
3. Métodos muito complexos (~100 linhas)
4. Difícil de testar (acoplado a PyQt6)
5. Viola múltiplos princípios SOLID

**Próximos passos:**
1. Task 3.1.2: Confirmar responsabilidades identificadas ✅ (FEITO)
2. Task 3.1.5: Criar `alignment_state.py` expandido
3. Task 3.1.3: Criar `fiducial_alignment_service.py`
4. Task 3.1.4: Criar `template_matching_service.py`
5. Task 3.1.6: Refatorar widget para usar serviços
6. Task 3.1.7: Criar testes abrangentes
7. Task 3.1.9: Validação manual com hardware

---

**Analista:** Claude Sonnet 4.5
**Data:** 2026-01-14
**Status:** ✅ ANÁLISE COMPLETA - PRONTO PARA IMPLEMENTAÇÃO
