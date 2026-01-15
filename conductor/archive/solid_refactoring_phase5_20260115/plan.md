# Plano de Implementação - SOLID Refactoring Phase 5
**Track ID:** solid_refactoring_phase5_20260115
**Status:** PLANNING
**Data de Criação:** 2026-01-15
**Prioridade:** ALTA

## Resumo Executivo

Esta fase foca na refatoração de arquivos grandes (>800 linhas) seguindo os princípios SOLID estabelecidos nas fases anteriores. Dois alvos principais foram identificados:

### Alvo A: `aoi_lib/report_generator.py` (1.366 linhas)
**Responsabilidade Atual:** Geração de relatórios PDF com gráficos e tabelas.

### Alvo B: `aoi_lib/fiducial_alignment_widget.py` (959 linhas)
**Responsabilidade Atual:** Widget de captura e alinhamento de fiduciais.

**Decisão Pendente:** Escolha entre Alvo A ou Alvo B (ver análise abaixo).

---

## Análise Comparativa dos Alvos

### Alvo A: report_generator.py (1.366 linhas)

#### Vantagens:
✅ **Alto Impacto no Negócio**
   - Relatórios são entregáveis críticos para clientes
   - Melhorias facilitam adição de novos tipos de relatórios

✅ **Separação Clara de Responsabilidades**
   - Geração de PDF (reportlab)
   - Geração de gráficos (matplotlib)
   - Templates de layout
   - Cálculos estatísticos

✅ **Benefício Imediato**
   - Mais fácil adicionar novos gráficos
   - Mais fácil modificar layouts
   - Reutilização em outros contextos

#### Desvantagens:
⚠️ **Alta Complexidade**
   - 3 dependências externas (reportlab, matplotlib, Pillow)
   - Lógica complexa de layout PDF
   - Cálculos estatísticos intercalados

⚠️ **Testes Difíceis**
   - Geração de PDF requer validação visual
   - Gráficos requerem comparação de imagens
   - Testes lentos (geração de PDF demorada)

#### Estimativa:
- **Duração:** 3-4 dias
- **Novos Módulos:** 3-4
- **Linhas Extraídas:** ~600-700 linhas
- **Complexidade:** ALTA

---

### Alvo B: fiducial_alignment_widget.py (959 linhas)

#### Vantagens:
✅ **Benefício Técnico Imediato**
   - Separa UI da lógica de negócio
   - Serviços reutilizáveis em outras partes do sistema
   - Testes mais fáceis (sem UI)

✅ **Padrão Claro**
   - Segue padrão estabelecido na FASE 4 (mainwindow.py)
   - Extrair serviços (TemplateMatcher, AlignmentCalculator)
   - Widget fica apenas como orquestrador

✅ **Menos Dependências**
   - Principal dependência: OpenCV (já usada em outros lugares)
   - Lógica geométrica bem definida

#### Desvantagens:
⚠️ **Impacto Indireto no Negócio**
   - Melhora arquitetura, mas não adiciona funcionalidades visíveis
   - Benefício a longo prazo (manutenibilidade)

⚠️ **Contexto Complexo**
   - Requer entender visão computacional
   - Template matching com OpenCV
   - Transformações geométricas

#### Estimativa:
- **Duração:** 2-3 dias
- **Novos Módulos:** 2-3
- **Linhas Extraídas:** ~500-600 linhas
- **Complexidade:** MÉDIA

---

## Recomendação

### Escolher **Alvo B (fiducial_alignment_widget.py)** primeiro

**Justificativa:**

1. **Continuidade com FASE 4**
   - Padrão similar ao mainwindow.py refatorado
   - Menos risco que report_generator
   - Permite validar abordagem antes de atacar alvo mais complexo

2. **Melhor Custo-Benefício**
   - Menos tempo (2-3 dias vs 3-4 dias)
   - Testes mais simples (sem validação visual de PDF)
   - Serviços reutilizáveis imediatamente

3. **Maior Aprendizado**
   - Visão computacional é dominante no sistema
   - Serviços extraídos podem ser usados em outros lugares
   - Prepara terreno para refatorar report_generator depois

---

## Plano Detalhado - FASE 5B (fiducial_alignment_widget)

### Objetivos

1. **Extrair Template Matching Service**
   - Lógica de detecção de fiduciais
   - Independente de UI
   - Reutilizável

2. **Extrair Alignment Calculator**
   - Cálculos de transformação (translação, rotação, escala)
   - Matrizes de transformação
   - Independente de UI

3. **Simplificar Widget**
   - Reduzir para orquestrador de UI
   - Delegar lógica para serviços
   - Melhorar testabilidade

### Módulos a Serem Criados

#### 1. `aoi_lib/gerber_core/template_matcher.py` (~200 linhas)
**Responsabilidade:** Detecção de fiduciais usando template matching

```python
class TemplateMatcherService:
    """Serviço para detecção de fiduciais via template matching."""

    def locate_fiducial(
        self,
        image: np.ndarray,
        template: np.ndarray,
        search_radius: int = 100,
        threshold: float = 0.7,
    ) -> tuple[float, float] | None:
        """Localiza um fiducial na imagem."""
        pass

    def locate_multiple_fiducials(
        self,
        image: np.ndarray,
        templates: list[np.ndarray],
        search_radius: int = 100,
        threshold: float = 0.7,
    ) -> list[tuple[int, int, float, float]]:  # (id, x, y, score)
        """Localiza múltiplos fiduciais."""
        pass
```

#### 2. `aoi_lib/gerber_core/alignment_calculator.py` (~150 linhas)
**Responsabilidade:** Cálculos de transformação geométrica

```python
class AlignmentCalculator:
    """Calcula transformações de alinhamento."""

    def calculate_transform(
        self,
        reference_points: list[tuple[float, float]],
        detected_points: list[tuple[float, float]],
    ) -> AlignmentTransform:
        """Calcula matriz de transformação (translação, rotação, escala)."""
        pass

    def apply_transform(
        self,
        point: tuple[float, float],
        transform: AlignmentTransform,
    ) -> tuple[float, float]:
        """Aplica transformação a um ponto."""
        pass

    def validate_alignment(
        self,
        transform: AlignmentTransform,
        max_rotation: float = 5.0,
        max_scale_diff: float = 0.1,
    ) -> bool:
        """Valida se transformação está dentro de limites aceitáveis."""
        pass
```

#### 3. `fiducial_alignment_widget.py` (refatorado, ~400 linhas)
**Responsabilidade:** Orquestrador de UI (apenas coordenar)

```python
class FiducialAlignmentWidget(QWidget):
    """Widget para captura e alinhamento de fiduciais (ORQUESTRADOR)."""

    def __init__(self, ...):
        # Serviços injetados
        self.template_matcher = TemplateMatcherService()
        self.alignment_calculator = AlignmentCalculator()

    def capture_template(self, x: int, y: int):
        """Captura template - delega para serviço."""
        pass

    def search_fiducials(self):
        """Busca fiduciais - delega para serviço."""
        pass

    def calculate_alignment(self):
        """Calcula transformação - delega para serviço."""
        pass
```

### Fases de Implementação

#### FASE 5B.1: Análise e Planejamento (Dia 1)
- [ ] Ler `fiducial_alignment_widget.py` completamente
- [ ] Identificar responsabilidades atuais
- [ ] Mapear métodos a serem extraídos
- [ ] Criar spec.md detalhado
- [ ] Definir interfaces dos serviços

#### FASE 5B.2: Template Matcher Service (Dia 2)
- [ ] Criar `template_matcher.py`
- [ ] Implementar `locate_fiducial()`
- [ ] Implementar `locate_multiple_fiducials()`
- [ ] Escrever testes unitários
- [ ] Validar com OpenCV

#### FASE 5B.3: Alignment Calculator (Dia 3)
- [ ] Criar `alignment_calculator.py`
- [ ] Implementar `calculate_transform()`
- [ ] Implementar `apply_transform()`
- [ ] Implementar `validate_alignment()`
- [ ] Escrever testes unitários
- [ ] Validar cálculos geométricos

#### FASE 5B.4: Refatoração do Widget (Dia 4)
- [ ] Refatorar `fiducial_alignment_widget.py`
- [ ] Injetar serviços
- [ ] Delegar lógica
- [ ] Remover código duplicado
- [ ] Testes de integração

#### FASE 5B.5: Validação e Documentação (Dia 5)
- [ ] Testes manuais completos
- [ ] Atualizar documentação
- [ ] Criar relatório de refatoração
- [ ] Atualizar CLAUDE.md
- [ ] Commit e tag

---

## Critérios de Sucesso

### Métricas Quantitativas
- [ ] Redução de 959 → ~400 linhas no widget (-58%)
- [ ] 2 novos serviços criados
- [ ] >80% cobertura de testes nos serviços
- [ ] Zero breaking changes

### Métricas Qualitativas
- [ ] Serviços 100% testáveis sem PyQt6
- [ ] Widget como orquestrador apenas
- [ ] Código mais legível e maintenível
- [ ] Serviços reutilizáveis em outros contextos

### Validação Funcional
- [ ] Captura de fiduciais funciona
- [ ] Template matching funciona
- [ ] Cálculo de transformação funciona
- [ ] Alinhamento visual funciona
- [ ] Export de transformação funciona

---

## Riscos e Mitigações

### Risco 1: Quebra de Funcionalidade Existente
**Probabilidade:** MÉDIA
**Impacto:** ALTO
**Mitigação:**
- Testes manuais completos antes/depois
- Testes de integração abrangentes
- Commit atômico com rollback fácil

### Risco 2: Complexidade de Template Matching
**Probabilidade:** MÉDIA
**Impacto:** MÉDIO
**Mitigação:**
- Estudar código atual detalhadamente
- Não alterar algoritmos, apenas extrair
- Testes com imagens reais

### Risco 3: Dependência de OpenCV
**Probabilidade:** BAIXA
**Impacto:** BAIXO
**Mitigação:**
- OpenCV já usado em outros lugares
- Serviço isola dependência
- Fácil mockar para testes

---

## Plano B - FASE 5A (report_generator)

*Se escolhido o Alvo A, o plano seria:*

### Módulos a Serem Criados

1. **`aoi_lib/reports/pdf_generator.py`** (~400 linhas)
   - Geração de PDF usando reportlab
   - Layouts de página
   - Headers e footers

2. **`aoi_lib/reports/chart_generator.py`** (~300 linhas)
   - Geração de gráficos matplotlib
   - Heatmaps, scatter plots, line charts
   - Estilização de gráficos

3. **`aoi_lib/reports/statistics_calculator.py`** (~200 linhas)
   - Cálculos estatísticos
   - Média, desvio padrão, outliers
   - Classificação de resultados

4. **`report_generator.py`** (refatorado, ~400 linhas)
   - Orquestrador de geração
   - Coordena os serviços
   - Monta relatório final

**Estimativa:** 4-5 dias
**Complexidade:** ALTA
**Benefício:** Geração de relatórios mais flexível

---

## Decisão Pendente

**❓ Qual alvo você prefere para FASE 5?**

- **[ ] Opção B (RECOMENDADA):** `fiducial_alignment_widget.py`
  - Menos risco (MÉDIA complexidade)
  - Mais rápido (2-3 dias)
  - Padrão validado na FASE 4
  - Serviços reutilizáveis imediatamente

- **[ ] Opção A:** `report_generator.py`
  - Maior impacto no negócio
  - Mais complexo (ALTA complexidade)
  - Testes mais difíceis (validação visual)
  - 4-5 dias

Por favor, informe sua escolha para prosseguirmos!
