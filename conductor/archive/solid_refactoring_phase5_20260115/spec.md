# Especificação - SOLID Refactoring Phase 5
**Track ID:** solid_refactoring_phase5_20260115
**Status:** PLANNING
**Data de Criação:** 2026-01-15

## Visão Geral

Refatoração de arquivos grandes seguindo princípios SOLID, focando em separação de responsabilidades e testabilidade.

## Contexto

### FASE 4 Concluída ✅
- **Arquivo:** `aoi_lib/gerber_core/gui/mainwindow.py`
- **Resultado:** 1.421 → 735 linhas (-48.3%)
- **Módulos Extraídos:**
  - `ObjectEditor` (748 linhas)
  - `GerberFileManager` (404 linhas)
  - `WidthHeightDialog` (239 linhas)

### Limpeza de Legacy Concluída ✅
- **Removido:** 2.289 linhas de código obsoleto
- **Arquivos:** `stencil_tension_old.py`, `recipe_dialog.py`, backups

### Próximos Alvos Identificados
Dois arquivos candidatos para refatoração:

1. **`aoi_lib/report_generator.py`** (1.366 linhas)
2. **`aoi_lib/fiducial_alignment_widget.py`** (959 linhas)

---

## Candidato A: report_generator.py

### Descrição Atual
Gerador de relatórios PDF para inspeção de stencils, incluindo:
- Gráficos de tendência
- Heatmaps de tensão
- Tabelas de resultados
- Imagens overlay

### Responsabilidades Identificadas
1. **Geração de PDF** (reportlab)
   - Criação de documento
   - Layout de página
   - Headers/footers
   - Múltiplas páginas

2. **Geração de Gráficos** (matplotlib)
   - Scatter plots
   - Line charts
   - Heatmaps
   - Histograms

3. **Cálculos Estatísticos**
   - Média, desvio padrão
   - Detecção de outliers
   - Tendências
   - Classificação

4. **Renderização de Imagens**
   - Overlay Gerber/imagem
   - Capturas de câmera
   - Anotações

5. **Templates de Relatório**
   - Configuração de estilos
   - Logotipos
   - Cores
   - Fontes

### Problemas Atuais
- ❌ **Monolítico:** Todas as responsabilidades em um arquivo
- ❌ **Difícil de Testar:** Geração de PDF requer validação visual
- ❌ **Difícil de Estender:** Adicionar novo gráfico requer modificar arquivo principal
- ❌ **Baixa Reutilização:** Código específico para stencil tension não pode ser usado em outros contextos

### Proposta de Refatoração

#### Módulos a Criar

**1. `aoi_lib/reports/pdf_generator.py` (~400 linhas)**
```python
class PDFGenerator:
    """Gera documentos PDF usando reportlab."""

    def create_document(self, config: PDFConfig) -> PdfDocument:
        """Cria um novo documento PDF."""

    def add_page(self, doc: PdfDocument, content: str):
        """Adiciona uma página ao documento."""

    def add_image(self, doc: PdfDocument, image: np.ndarray, position: tuple):
        """Adiciona uma imagem ao documento."""

    def add_table(self, doc: PdfDocument, data: list, headers: list):
        """Adiciona uma tabela ao documento."""

    def save(self, doc: PdfDocument, path: str):
        """Salva o documento em arquivo."""
```

**2. `aoi_lib/reports/chart_generator.py` (~300 linhas)**
```python
class ChartGenerator:
    """Gera gráficos usando matplotlib."""

    def create_scatter_plot(self, data: list) -> Figure:
        """Cria scatter plot."""

    def create_line_chart(self, data: list) -> Figure:
        """Cria line chart."""

    def create_heatmap(self, data: np.ndarray) -> Figure:
        """Cria heatmap."""

    def create_histogram(self, data: list) -> Figure:
        """Cria histogram."""

    def apply_style(self, fig: Figure, style: ChartStyle):
        """Aplica estilo ao gráfico."""

    def save_as_image(self, fig: Figure, path: str):
        """Salva gráfico como imagem."""
```

**3. `aoi_lib/reports/statistics_calculator.py` (~200 linhas)**
```python
class StatisticsCalculator:
    """Calcula estatísticas para relatórios."""

    def calculate_mean_std(self, data: list) -> tuple[float, float]:
        """Calcula média e desvio padrão."""

    def detect_outliers(self, data: list, method: str = "iqr") -> list:
        """Detecta outliers nos dados."""

    def calculate_trend(self, data: list) -> dict:
        """Calcula tendência dos dados."""

    def classify_results(self, data: list, thresholds: dict) -> dict:
        """Classifica resultados (OK/WARNING/NOK)."""

    def generate_summary(self, data: list) -> str:
        """Gera resumo textual."""
```

**4. `report_generator.py` (refatorado, ~400 linhas)**
```python
class ReportGenerator:
    """Orquestrador de geração de relatórios."""

    def __init__(self):
        self.pdf_gen = PDFGenerator()
        self.chart_gen = ChartGenerator()
        self.stats_calc = StatisticsCalculator()

    def generate_tension_report(
        self,
        session: TensionMeasurementSession,
        config: ReportConfig,
    ) -> str:
        """Gera relatório de medição de tensão."""

    def generate_inspection_report(
        self,
        results: InspectionResult,
        config: ReportConfig,
    ) -> str:
        """Gera relatório de inspeção visual."""
```

### Benefícios Esperados
- ✅ **Separação de Responsabilidades:** Cada módulo tem uma função clara
- ✅ **Testabilidade:** Serviços podem ser testados independentemente
- ✅ **Reutilização:** Serviços podem ser usados em outros contextos
- ✅ **Extensibilidade:** Fácil adicionar novos tipos de gráficos ou layouts
- ✅ **Manutenibilidade:** Mudanças localizadas

---

## Candidato B: fiducial_alignment_widget.py

### Descrição Atual
Widget para captura e alinhamento de fiduciais marks usando template matching OpenCV.

### Responsabilidades Identificadas
1. **Captura de Templates**
   - Seleção de pontos na imagem
   - Extração de sub-imagens
   - Armazenamento de templates

2. **Template Matching**
   - Busca de fiduciais usando OpenCV
   - Validação de correspondências
   - Múltiplos fiduciais

3. **Cálculo de Transformação**
   - Translação (dx, dy)
   - Rotação (ângulo)
   - Escala (zoom)
   - Matriz de transformação

4. **UI de Visualização**
   - Preview de imagem
   - Overlay de fiduciais
   - Controles de ajuste

5. **Gerenciamento de Estado**
   - Templates capturados
   - Fiduciais detectados
   - Transformação calculada

### Problemas Atuais
- ❌ **Monolítico:** UI misturada com lógica de visão computacional
- ❌ **Difícil de Testar:** Requer UI e câmera para testar
- ❌ **Baixa Reutilização:** Lógica de matching não pode ser usada em outros lugares
- ❌ **Acoplado:** Widget dependente de implementação específica

### Proposta de Refatoração

#### Módulos a Criar

**1. `aoi_lib/gerber_core/template_matcher.py` (~200 linhas)**
```python
class TemplateMatcherService:
    """Serviço para detecção via template matching."""

    def locate_fiducial(
        self,
        image: np.ndarray,
        template: np.ndarray,
        search_radius: int = 100,
        threshold: float = 0.7,
        method: int = cv2.TM_CCOEFF_NORMED,
    ) -> tuple[float, float, float] | None:  # (x, y, score)
        """Localiza um fiducial na imagem."""

    def locate_multiple_fiducials(
        self,
        image: np.ndarray,
        templates: list[tuple[int, np.ndarray]],  # (id, template)
        search_radius: int = 100,
        threshold: float = 0.7,
    ) -> list[tuple[int, float, float, float]]:  # (id, x, y, score)
        """Localiza múltiplos fiduciais."""

    def validate_match(
        self,
        score: float,
        threshold: float,
    ) -> bool:
        """Valida se correspondência é aceitável."""

    def extract_template(
        self,
        image: np.ndarray,
        center: tuple[int, int],
        size: int = 50,
    ) -> np.ndarray:
        """Extrai template da imagem."""
```

**2. `aoi_lib/gerber_core/alignment_calculator.py` (~150 linhas)**
```python
class AlignmentCalculator:
    """Calcula transformações geométricas de alinhamento."""

    def calculate_transform(
        self,
        reference_points: list[tuple[float, float]],  # (x, y) esperados
        detected_points: list[tuple[float, float]],   # (x, y) detectados
        method: str = "affine",  # affine, similarity, rigid
    ) -> AlignmentTransform:
        """Calcula matriz de transformação."""

    def apply_transform(
        self,
        point: tuple[float, float],
        transform: AlignmentTransform,
    ) -> tuple[float, float]:
        """Aplica transformação a um ponto."""

    def apply_transform_to_points(
        self,
        points: list[tuple[float, float]],
        transform: AlignmentTransform,
    ) -> list[tuple[float, float]]:
        """Aplica transformação a múltiplos pontos."""

    def calculate_alignment_error(
        self,
        reference: list[tuple[float, float]],
        detected: list[tuple[float, float]],
        transform: AlignmentTransform,
    ) -> float:
        """Calcula erro médio de alinhamento (RMSE)."""

    def validate_alignment(
        self,
        transform: AlignmentTransform,
        max_rotation: float = 5.0,
        max_scale: tuple[float, float] = (0.9, 1.1),
        max_translation: float = 10.0,
    ) -> tuple[bool, str]:
        """Valida se transformação está dentro de limites."""
```

**3. `fiducial_alignment_widget.py` (refatorado, ~400 linhas)**
```python
class FiducialAlignmentWidget(QWidget):
    """Widget para captura e alinhamento de fiduciais (ORQUESTRADOR)."""

    def __init__(self, ...):
        # Serviços injetados
        self.template_matcher = TemplateMatcherService()
        self.alignment_calculator = AlignmentCalculator()

        # Estado
        self.templates = {}  # id -> np.ndarray
        self.detected_fiducials = {}  # id -> (x, y, score)
        self.transform = None

    def capture_template(self, x: int, y: int):
        """Callback: Usuário clica para capturar template."""
        template = self.template_matcher.extract_template(
            self.current_image,
            (x, y),
            self.template_size,
        )
        self.templates[len(self.templates)] = template
        self._update_preview()

    def search_fiducials(self):
        """Busca fiduciais na imagem atual."""
        self.detected_fiducials = {}
        for fid_id, template in self.templates.items():
            result = self.template_matcher.locate_fiducial(
                self.current_image,
                template,
                self.search_radius,
                self.threshold,
            )
            if result:
                x, y, score = result
                self.detected_fiducials[fid_id] = (x, y, score)
        self._update_preview()

    def calculate_alignment(self):
        """Calcula transformação de alinhamento."""
        reference_points = [self._get_expected_pos(fid_id)
                           for fid_id in self.detected_fiducials.keys()]
        detected_points = [(x, y)
                          for (x, y, _) in self.detected_fiducials.values()]

        self.transform = self.alignment_calculator.calculate_transform(
            reference_points,
            detected_points,
        )

        valid, msg = self.alignment_calculator.validate_alignment(
            self.transform,
        )
        if not valid:
            QMessageBox.warning(self, "Alinhamento inválido", msg)
```

### Benefícios Esperados
- ✅ **Separação UI/Lógica:** Widget orquestra, serviços fazem trabalho
- ✅ **Testabilidade:** Serviços 100% testáveis sem UI
- ✅ **Reutilização:** Template matching pode ser usado em outras partes
- ✅ **Manutenibilidade:** Mudanças em algoritmos não afetam UI
- ✅ **Padrão Validado:** Segue sucesso da FASE 4

---

## Critérios de Aceite

### Para Ambos os Alvos
- [ ] Zero breaking changes (funcionalidade mantida)
- [ ] >80% cobertura de testes nos serviços
- [ ] Serviços 100% testáveis sem PyQt6/UI
- [ ] Redução de linhas no arquivo principal (>40%)
- [ ] Validação manual completa
- [ ] Documentação atualizada
- [ ] Commit com tag

### Específicos por Alvo

**Candidato A (report_generator):**
- [ ] Novo tipo de gráfico pode ser adicionado sem modificar código principal
- [ ] Testes de geração de PDF passam
- [ ] Relatórios gerados são visualmente idênticos

**Candidato B (fiducial_alignment_widget):**
- [ ] Captura de fiduciais funciona
- [ ] Template matching funciona
- [ ] Cálculo de transformação é preciso
- [ ] Alinhamento visual está correto

---

## Recomendação Final

**Escolher Candidato B (fiducial_alignment_widget.py)**

**Justificativa:**
1. Menos risco (MÉDIA vs ALTA complexidade)
2. Mais rápido (2-3 dias vs 4-5 dias)
3. Padrão validado na FASE 4
4. Serviços reutilizáveis imediatamente
5. Melhor relação custo-benefício

---

## Decisão Pendente

**❓ Qual alvo escolher para FASE 5?**

Por favor, informe sua preferência:
- **[ ] Opção B (RECOMENDADA):** `fiducial_alignment_widget.py`
- **[ ] Opção A:** `report_generator.py`
- **[ ] Outro:** (especificar)
