# Especificação da Track: SOLID Refactoring Phase 2

## Objetivo

Refatorar os arquivos mais críticos do projeto Tensiometro para eliminar violações dos princípios SOLID, melhorar a manutenibilidade do código e reduzir a complexidade ciclomática.

**Meta Principal:** Elevar o Score SOLID global de 72/100 para >85/100.

## Contexto

**Análise SOLID Realizada:** 2026-01-14
**Relatório Completo:** `docs/reports/SOLID_ANALYSIS_REPORT_2026-01-14.md`

O projeto Tensiometro (59,516 linhas de código, 184 arquivos Python) apresenta:
- **3 arquivos críticos** >1000 linhas (1 já arquivado)
- **32 arquivos** >500 linhas
- **Funções com complexidade extrema** (47 em `_build_layer_core_mm()`)
- **Violações SRP** (Single Responsibility Principle)
- **Violações OCP** (Open/Closed Principle)
- **Violações ISP** (Interface Segregation Principle)
- **Violações DIP** (Dependency Inversion Principle)

**Prévia Bem-Sucedida:**
- ✅ SOLID Phase 1 completada em 2026-01-14 (2 dias, estimativa: 2 semanas)
- ✅ Refatoração de `stencil_tension.py` (1,409 → 5 módulos)
- ✅ 48 unit tests criados (100% service layer coverage)

## Escopo

### Fase 1: Críticos (Semana 1-2) 🔴

1. **Refatorar `aoi_lib/gerber_core/gui/mainwindow.py`** (1,384 linhas)
   - Extrair `GerberController` (lógica de negócio)
   - Extrair `GerberModel` (dados)
   - Extrair `GerberCommand` (ações - padrão Command)
   - Reduzir complexidade de `on_edit_many_objects()` (46 → <15)
   - Reduzir complexidade de `on_edit_object()` (27 → <15)

2. **Refatorar `aoi_lib/gerber_core/parser.py`**
   - Implementar Strategy Pattern para renderizadores de aperture
   - Criar abstração `ApertureRenderer` (ABC)
   - Criar renderizadores concretos (Circle, Rectangle, Obround, etc.)
   - Reduzir complexidade de `_build_layer_core_mm()` (47 → <15)

3. **Refatorar `aoi_lib/stencil_database.py`** (914 linhas)
   - Criar interfaces de repositórios (ABC)
   - Criar `StencilRepository`, `TensionRepository`, `InspectionRepository`
   - Criar `JsonToSqliteMigrator` (separado)
   - Reduzir métodos públicos de 21 → <10 por classe

### Fase 2: Alta Prioridade (Semana 3-4) 🟠

4. **Refatorar `consumo_lib/widgets/engenharia/alignment_widget.py`** (1,179 linhas)
   - Extrair `FiducialAlignmentService`
   - Extrair `TemplateMatchingService`
   - Extrair `AlignmentState` (separado de wizard_state.py)

5. **Refatorar `consumo_lib/main_window.py`** (650 linhas, 46 métodos)
   - Extrair interfaces (`TabManager`, `MenuManager`, etc.)
   - Implementar Factory Pattern para criação de componentes
   - Reduzir métodos públicos de 46 → <20
   - Injetar dependências via construtor

6. **Refatorar `aoi_lib/plc_axis_controller.py`** (738 linhas, 29 métodos)
   - Criar abstração `ModbusClient` (ABC)
   - Implementar `PymodbusTcpClient` (adaptação)
   - Segregar interfaces (`PLCAbsoluteMovement`, `PLCJogMovement`, etc.)
   - Reduzir métodos públicos de 29 → <15

### Fase 3: Média Prioridade (Mês 2) 🟡

7. **Refatorar `aoi_lib/report_generator.py`** (1,366 linhas)
   - Extrair `ReportLayout` (layout de páginas)
   - Extrair `ChartGenerator` (gráficos Matplotlib)
   - Reduzir tamanho dos builders (~400 → ~200 linhas cada)

8. **Refatorar `consumo_lib/dialogs/recipe_dialogs.py`** (881 linhas)
   - Separar 3 diálogos em arquivos distintos

9. **Refatorar `consumo_lib/coordinators/setup_coordinator.py`** (601 linhas)
   - Injetar dependências via construtor
   - Criar `CoordinatorFactory`

## Critérios de Aceite

### Critérios Gerais
- [ ] Zero breaking changes (backward compatibility mantida)
- [ ] Todos os testes existentes continuam passando (462 testes)
- [ ] Novos testes unitários para código refatorado
- [ ] Coverage de testes mantido ou aumentado (97.7%+)
- [ ] Documentação atualizada (docstrings, type hints)
- [ ] CLAUDE.md atualizado com novas estruturas

### Critérios Específicos por Arquivo

**gerber_core/gui/mainwindow.py:**
- [ ] Arquivo principal <500 linhas
- [ ] Complexidade `on_edit_many_objects()` <15
- [ ] Complexidade `on_edit_object()` <15
- [ ] Separação clara: UI (mainwindow.py), Lógica (controller.py), Dados (model.py)

**gerber_core/parser.py:**
- [ ] Complexidade `_build_layer_core_mm()` <15
- [ ] Strategy Pattern implementado
- [ ] Fácil adicionar novos tipos de aperture (sem modificar código existente)

**stencil_database.py:**
- [ ] 3 repositórios separados (Stencil, Tension, Inspection)
- [ ] Interfaces ABC definidas
- [ ] Cada classe <10 métodos públicos
- [ ] `JsonToSqliteMigrator` separado

**alignment_widget.py:**
- [ ] Serviços extraídos (`FiducialAlignmentService`, `TemplateMatchingService`)
- [ ] Widget apenas UI (sem lógica de negócio)

**main_window.py:**
- [ ] Interfaces segregadas (`TabManager`, `MenuManager`, etc.)
- [ ] Factory Pattern implementado
- [ ] <20 métodos públicos
- [ ] Dependências injetadas via construtor

**plc_axis_controller.py:**
- [ ] Abstração `ModbusClient` criada
- [ ] Interfaces segregadas por funcionalidade
- [ ] <15 métodos públicos por interface

**report_generator.py:**
- [ ] `ReportLayout` extraído
- [ ] `ChartGenerator` extraído
- [ ] Builders <200 linhas cada

**recipe_dialogs.py:**
- [ ] 3 arquivos separados (list, edit, manager)

**setup_coordinator.py:**
- [ ] Dependências injetadas via construtor
- [ ] `CoordinatorFactory` criado

### Critérios de Score SOLID

- [ ] Score SRP >80/100 (atual: 65/100)
- [ ] Score OCP >85/100 (atual: 78/100)
- [ ] Score LSP >90/100 (atual: 85/100)
- [ ] Score ISP >80/100 (atual: 70/100)
- [ ] Score DIP >70/100 (atual: 55/100)
- [ ] **Score SOLID Global >85/100** (atual: 72/100)

## Considerações Técnicas

### Padrões de Design a Aplicar
- **Strategy Pattern:** Para renderizadores de aperture (parser.py)
- **Repository Pattern:** Para acesso a dados (stencil_database.py)
- **Command Pattern:** Para ações de edição (mainwindow.py)
- **Factory Pattern:** Para criação de componentes (main_window.py)
- **Interface Segregation:** Para interfaces grandes (plc_axis_controller.py)

### Abstrações a Criar
- `ApertureRenderer` (ABC) - gerber_core/parser.py
- `StencilRepository`, `TensionRepository`, `InspectionRepository` (ABC) - stencil_database.py
- `ModbusClient` (ABC) - plc_axis_controller.py
- `TabManager`, `MenuManager`, `HardwareManager`, `DialogManager` (ABC) - main_window.py

### Backward Compatibility
- **CRÍTICO:** Manter APIs públicas existentes
- Criar camadas de compatibilidade se necessário
- Adicionar deprecation warnings para métodos obsoletos
- Documentar mudanças breaking em CHANGELOG

### Testes
- Criar testes unitários para cada nova classe
- Testes de integração para garantir backward compatibility
- Mock de dependências externas (Modbus, Serial, Camera)
- Coverage mínimo: 80% por arquivo

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| **Breaking Changes** | Média | Alto | Testes abrangentes, compatibilidade, documentação |
| **Regressões** | Média | Alto | Testes automatizados, code review, validação manual |
| **Aumento de complexidade** | Baixa | Médio | Manter simplicidade, revisão de arquitetura |
| **Atraso no cronograma** | Média | Médio | Priorização, escopo flexível, validação incremental |
| **Perda de funcionalidade** | Baixa | Alto | Testes completos, checklist de validação |

## Dependências

### Dependências Externas
- `pymodbus` - Comunicação Modbus TCP
- `PyQt6` - Interface gráfica
- `opencv-python` - Processamento de imagens
- `reportlab` - Geração de PDF
- `matplotlib` - Gráficos

### Dependências Internas
- Fase 1 não tem dependências
- Fase 2 depende de conclusão da Fase 1
- Fase 3 depende de conclusão da Fase 2

### Conhecimento Necessário
- SOLID principles (entendido)
- Design Patterns (Strategy, Repository, Command, Factory)
- PyQt6 (widgets, signals/slots)
- SQLAlchemy ou SQLite (para repositórios)
- Modbus protocol (para PLC controller)

## Pontos Fora do Escopo

- ❌ Refatoração de arquivos <500 linhas (deixar para technical debt contínuo)
- ❌ Alteração de funcionalidades existentes (apenas refatoração)
- ❌ Adição de novas features
- ❌ Mudança de stack tecnológico
- ❌ Migração completa para SQLAlchemy (se parcial)
- ❌ Refatoração de testes existentes (apenas adaptação)
- ❌ Otimização de performance (apenas se necessária)
- ❌ Alterações de UI/UX (apenas refatoração interna)

## Critérios de Sucesso da Track

### Métricas Quantitativas
- **Score SOLID Global:** 72 → 85+
- **Arquivos >1000 linhas:** 3 → 0
- **Arquivos >500 linhas:** 32 → <15
- **Complexidade >20:** 6 → 0
- **Complexidade >15:** 10+ → <5
- **Classes com >20 métodos públicos:** 7 → 0
- **Testes unitários:** 462 → 500+

### Métricas Qualitativas
- Código mais legível e manutenível
- Separação clara de responsabilidades
- Fácil adicionar novos features (OCP)
- Baixo acoplamento, alta coesão
- Backward compatibility mantida

### Marcos de Conclusão
- [ ] Fase 1 completa (críticos)
- [ ] Fase 2 completa (alta prioridade)
- [ ] Fase 3 completa (média prioridade)
- [ ] Score SOLID >85/100
- [ ] Relatório final de refatoração
- [ ] Documentação atualizada

---
*Generated by Conductor. Created: 2026-01-14*
*Track ID: solid_refactoring_phase2_20260114*
*Type: Refactor*
*Priority: Critical*
*Estimated Duration: 4-6 weeks*
