# Especificação da Track: Refactor large monolithic files

## Visão Geral
**Track ID:** refactor_large_files_20260113
**Tipo:** Refactor
**Prioridade:** Medium-High
**Complexidade:** High
**Data de Criação:** 2026-01-13
**Estimativa:** 4-6 semanas

## Descrição Detalhada

Refatorar 38 arquivos Python grandes (>500 linhas) identificados na análise de código para melhorar manutenibilidade, testabilidade e aderência à arquitetura do projeto. O foco principal é eliminar anti-patterns arquiteturais e separar responsabilidades misturadas.

## Contexto e Motivação

### Problema Atual
- **38 arquivos** com mais de 500 linhas totalizando 63,403 linhas de código
- **7 arquivos** com mais de 1,000 linhas (monolíticos)
- **Anti-patterns identificados:**
  - `signal_aggregator.py` (1,098 linhas): Centralização de eventos cria acoplamento tight
  - `stencil_tension.py` (1,409 linhas): Mistura serial protocol, GUI, threading e business logic
  - `stencil_tracker_ui.py` (1,301 linhas): GUI em `aoi_lib/` (deveria estar em `consumo_lib/`)

### Histórico Recente
O projeto já passou por refatoração significativa (`consumo_lib.py`: 6,245 → 1,060 linhas), mas permanecem arquivos monolíticos que violam princípios SOLID e a arquitetura estabelecida.

## Objetivos

### Primário
1. Eliminar anti-patterns arquiteturais (signal_aggregator, mistura GUI/business logic)
2. Separar responsabilidades misturadas em arquivos grandes
3. Alinhar código GUI com arquitetura (mover de `aoi_lib/` para `consumo_lib/`)
4. Estabelecer limite de tamanho: 200-400 linhas por arquivo (máximo 500)

### Secundário
1. Melhorar testabilidade através de módulos menores e focados
2. Facilitar manutenção futura
3. Preparar código base para crescimento sustentável

## Alcance (Scope)

### INCLUÍDO
✅ Divisão de arquivos >500 linhas em múltiplos módulos
✅ Eliminação de `signal_aggregator.py` (distribuir handlers)
✅ Mova de código GUI de `aoi_lib/` para `consumo_lib/`
✅ Atualização de imports em todos os arquivos afetados
✅ Atualização de `CLAUDE.md` com nova estrutura
✅ Manter cobertura de testes existente

### EXCLUÍDO
❌ Alteração de funcionalidade existente (apenas refatoração)
❌ Adição de novos features
❌ Refatoração de arquivos em `poc_gerber/` (produto separado)
❌ Refatoração de testes >500 linhas (aceitável para testes de integração)

## Critérios de Aceitação

### Fase 1: Alta Prioridade
- [ ] `stencil_tension.py` (1,409 linhas) dividido em 4 módulos:
  - `aoi_lib/tensiometer/serial_protocol.py`
  - `aoi_lib/tensiometer/measurement_thread.py`
  - `aoi_lib/tensiometer/tension_measurement.py`
  - `consumo_lib/dialogs/tension_measurement_dialog.py`
- [ ] `signal_aggregator.py` (1,098 linhas) eliminado:
  - Handlers distribuídos para controllers respectivos
  - Cada controller gerencia seus próprios signals
- [ ] `stencil_tracker_ui.py` (1,301 linhas) movido para `consumo_lib/`:
  - 6 dialogs/widgets separados em arquivos individuais
  - Imports atualizados em todo código base

### Fase 2: Média Prioridade
- [ ] `report_generator.py` (1,366 linhas) dividido em:
  - `aoi_lib/reports/config.py`
  - `aoi_lib/reports/builders/tension_builder.py`
  - `aoi_lib/reports/builders/history_builder.py`
  - `aoi_lib/reports/builders/inspection_builder.py`
  - `aoi_lib/reports/chart_generator.py`
  - `aoi_lib/reports/report_generator.py` (orchestrator)
- [ ] `main_window.py` (1,060 linhas) reduzido:
  - Extrair `MainWindowState` class
  - Extrair `MainWindowInitializer` class
  - Reduzir para 200-300 linhas (orchestrator puro)
- [ ] `map_controller.py` (965 linhas) dividido em:
  - `consumo_lib/services/map_program_manager.py`
  - `consumo_lib/controllers/map_controller.py`
  - `consumo_lib/dialogs/map_settings_dialog.py`

### Geral
- [ ] Todos os testes existentes passando
- [ ] Cobertura de testes mantida (>80%)
- [ ] Sem warnings de import ou pylint
- [ ] `CLAUDE.md` atualizado com nova estrutura
- [ ] Documentação de arquitetura atualizada (se necessário)

## Requisitos de Testes

### Testes Unitários
- Criar testes unitários para novos módulos extraídos
- Testar separação de responsabilidades
- Mock dependencies apropriadas

### Testes de Integração
- Validar que refatoração não quebra workflows existentes
- Testar imports cruzados entre módulos
- Validar integração GUI ↔ business logic

### Testes de Regressão
- Executar suite completa de testes antes de cada commit
- Comparar comportamento antes/depois com golden tests
- Validar todos workflows principais (CNC, tensão, inspeção)

## Plano de Migração

### Estratégia de Refatoração
1. **Preparação:** Backup com git branch
2. **Análise:** Mapear dependencies antes de dividir
3. **Extração:** Criar novos módulos mantendo interfaces
4. **Migração:** Atualizar imports incrementalmente
5. **Validação:** Testar a cada mudança
6. **Cleanup:** Remover código antigo após validação

### Ordem de Execução
1. Fase 1 (Alta Prioridade): stencil_tension, signal_aggregator, stencil_tracker_ui
2. Fase 2 (Média Prioridade): report_generator, main_window, map_controller
3. Fase 3 (Baixa Prioridade): demais arquivos >500 linhas

### Compatibilidade
- Manter interfaces públicas estáveis
- Usar deprecation warnings para APIs obsoletas
- Documentar breaking changes em CHANGELOG

## Plano de Rollback

### Estratégia Git
- Criar branch feature para cada fase
- Checkpoint commits ao final de cada arquivo refatorado
- Git notes documentando validação

### Rollback por Fase
```bash
# Se Fase 1 falhar
git revert --no-commit <fase1_commits...>
git reset --hard <checkpoint_before_phase1>

# Refazer Fase 1 com abordagem diferente
```

### Rollback Completo
- Deletar branches de refatoração
- Reset para branch main/master
- Restaurar estado anterior

## Considerações de Performance

### Impacto Esperado
- **Neutro ou Positivo:** Módulos menores permitem melhor otimização
- **Startup time:** Possível aumento leve (+5-10%) devido a mais imports
- **Memory usage:** Neutro (mesmo código, apenas organizado diferente)

### Mitigações
- Lazy loading de módulos GUI
- Caching de imports pesados
- Profile antes/depois para validar

## Considerações de Segurança

### Riscos
- Introdução de bugs durante refatoração
- Quebra de workflows críticos (CNC, medição de tensão)

### Mitigações
- Testes abrangentes antes de cada commit
- Code review obrigatório para mudanças em hardware controllers
- Validação com hardware real (PLC, tensiômetro)
- Feature flags para ativar/desativar novos módulos

## Impacto na Documentação

### Arquivos a Atualizar
- `CLAUDE.md`: Atualizar estrutura de diretórios e contagem de linhas
- `docs/architecture/`: Criar diagramas de nova estrutura
- `CHANGELOG.md`: Documentar breaking changes
- `README.md`: Atualizar instruções de instalação (se necessário)

### Novo Conteúdo
- Guia de arquitetura atualizado
- Diagramas de dependência entre módulos
- Exemplos de uso de novos módulos

## Métricas de Sucesso

### Métricas Quantitativas
- **Zero** arquivos >500 linhas em `aoi_lib/` core
- **Zero** arquivos >1,000 linhas no projeto
- **>90%** dos arquivos <400 linhas
- **0** regressions em testes de integração
- **<10%** aumento no tempo de startup

### Métricas Qualitativas
- Separação clara entre GUI (consumo_lib) e business logic (aoi_lib)
- Cada módulo com responsabilidade única
- Código mais fácil de entender e manter
- Reviews de código mais rápidas

## Riscos e Dependências

### Riscos
- **Alta complexidade:** Muitos arquivos para refatorar
- **Dependencies complexas:** Risco de quebrar imports
- **Validação com hardware:** Requer acesso a PLC, tensiômetro
- **Tempo estimado:** 4-6 semanas pode ser otimista

### Dependências
- Disponibilidade de hardware para testes (PLC, tensiômetro)
- Tempo para code review completo
- Paciência para refatoração incremental

### Mitigações
- Priorizar fases críticas primeiro
- Testes automatizados abrangentes
- Commits pequenos e frequentes
- Code review contínuo

## Recursos Necessários

### Recursos Técnicos
- Python 3.14+
- PyQt6
- Acesso a hardware de teste (PLC Delta, Tensiômetro AS-120N, Camera)
- Suite de testes atualizada

### Recursos Humanos
- Desenvolvedor Python sênior (familiarizado com projeto)
- Code reviewer (conhecedor de arquitetura)
- Validador de hardware (para testes com PLC/tensiômetro)

### Tempo Estimado
- **Fase 1:** 2-3 semanas (crítico)
- **Fase 2:** 1-2 semanas (importante)
- **Fase 3:** 1 semana (melhorias)
- **Total:** 4-6 semanas

## Metadados

**Track ID:** refactor_large_files_20260113
**Tipo:** Refactor
**Prioridade:** Medium-High
**Complexidade:** High
**Data de Criação:** 2026-01-13
**Estimativa:** 4-6 semanas
**Fases Estimadas:** 3

---
*Generated by Conductor Planning Agent*
