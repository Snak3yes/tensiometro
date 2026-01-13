# Especificação da Track: Engineering Wizard Aba 7 - Confirmar e Salvar

## Visão Geral
**Track ID:** engenharia_aba7_confirmar_salvar
**Tipo:** Feature
**Prioridade:** High
**Complexidade:** Medium
**Data de Criação:** 2026-01-13
**Estimativa:** 2-3 dias

## Descrição Detalhada

Implementar o widget **Confirmar e Salvar (Aba 7)**, a aba final do Engineering Wizard. Este widget deve exibir um resumo completo de todas as configurações das 6 abas anteriores, validar que o programa está completo e correto, fornecer estimativas de tempo de execução, e salvar o programa de inspeção em formato JSON para uso posterior pelo sistema de inspeção AOI.

## Contexto e Motivação

### Fluxo do Engineering Wizard
O Engineering Wizard é um sistema de 7 abas para criar programas de inspeção AOI:
1. **Aba 1:** Dados do Programa
2. **Aba 2:** Carregar Gerber
3. **Aba 3:** Definir Fiduciais
4. **Aba 4:** Capturar Mosaico
5. **Aba 5:** Alinhamento
6. **Aba 6:** Janelas de Inspeção
7. **Aba 7:** Confirmar e Salvar ⭐ **ESTA TRACK**

### Problema a Resolver
Após configurar todas as abas anteriores, o engenheiro precisa:
1. **Revisar** todas as configurações em um só lugar
2. **Validar** que o programa está completo e correto
3. **Estimar** quanto tempo levará para executar a inspeção
4. **Salvar** o programa em formato reutilizável
5. **Opcionalmente testar** a inspeção antes de salvar

O sistema deve fornecer uma visão consolidada, clara e validada antes de permitir o salvamento.

## Objetivos

### Primário
1. Criar modelo de dados agregado `ProgramConfig` com todas as 7 abas
2. Implementar widget com 7 cards de resumo (um por aba)
3. Implementar validação completa com mensagens de erro específicas
4. Implementar estimativas de tempo de execução por fase
5. Implementar salvamento em JSON com path gerado automaticamente
6. Suportar opção "Programa Base" (não específico de stencil)

### Secundário
1. Fornecer feedback visual color-codificado (verde/laranja/vermelho)
2. Implementar botão "Testar Inspeção" (opcional, com verificação de requisitos)
3. Exibir metadados (data de criação, versão, criador)
4. Suportar edição de campos antes de salvar

## Alcance (Scope)

### INCLUÍDO
✅ Modelos de dados (ProgramConfig, FiducialConfig, MosaicConfig, AlignmentConfig, InspectionGroupConfig)
✅ Widget `ConfirmSaveWidget` com 7 cards de resumo
✅ Validação completa com mensagens específicas
✅ Estimativas de tempo de execução
✅ Checkbox "Programa Base"
✅ Botão "Testar Inspeção" (opcional)
✅ Botão "Salvar Programa" com diálogo de confirmação
✅ Persistência JSON em `data/inspection_programs/`
✅ Signals: `save_requested(ProgramConfig)`, `test_requested(ProgramConfig)`, `back_requested()`
✅ Testes unitários (≥30 testes)
✅ Cobertura de código ≥80%

### EXCLUÍDO
❌ Execução de inspeção (runtime)
❌ Edição de configurações (apenas visualização)
❌ Versionamento de programas (sobrescreve por enquanto)
❌ Exportação para outros formatos (PDF, Excel)

## Requisitos Funcionais

### RF1. Modelo de Dados Agregado
**Prioridade:** Alta
**Descrição:** ProgramConfig deve conter todos os dados das 7 abas

**Critérios:**
- [x] Aba 1: stencil_code, program_name, description, version, created_by
- [x] Aba 2: gerber_file, gerber_dimensions, aperture_count, fiducial_count
- [x] Aba 3: fiducial positions (2), template paths
- [x] Aba 4: mosaic grid, total FOVs, corners, delay
- [x] Aba 5: transform (tx, ty, angle, scale), score
- [x] Aba 6: inspection groups (count, configured, confirmed)
- [x] Metadados: created_at, updated_at, status

### RF2. Cards de Resumo
**Prioridade:** Alta
**Descrição:** 7 cards HTML formatados exibindo dados de cada aba

**Critérios:**
- [x] Card 1: Dados do Programa (nome, código, versão, descrição)
- [x] Card 2: Arquivo Gerber (path, dimensões, aperturas, fiduciais)
- [x] Card 3: Fiduciais (posições, templates)
- [x] Card 4: Mosaico Capturado (grid, FOVs, cantos, delay)
- [x] Card 5: Alinhamento (translação, rotação, escala, score)
- [x] Card 6: Janelas de Inspeção (grupos, configurados, confirmados)
- [x] Card 7: Estimativas de Execução (tempo por fase)

### RF3. Validação Completa
**Prioridade:** Alta
**Descrição:** Verificar que o programa está completo e correto

**Critérios:**
- [x] Método `validate() -> (bool, List[str])`
- [x] Verificar stencil_code e program_name preenchidos
- [x] Verificar Gerber carregado com aperturas
- [x] Verificar fiduciais definidos (ambos)
- [x] Verificar mosaico capturado (FOVs > 0)
- [x] Verificar score de alinhamento ≥ 70%
- [x] Verificar grupos de inspeção configurados e confirmados
- [x] Retornar erros específicos e acionáveis

### RF4. Estimativas de Tempo
**Prioridade:** Média
**Descrição:** Calcular tempo estimado de execução da inspeção

**Critérios:**
- [x] Método `get_estimated_execution_time() -> Dict`
- [x] Estimar tempo por fase (captura, alinhamento, inspeção)
- [x] Basear em número de FOVs e janelas
- [x] Retornar tempos individuais e total
- [x] Formatar em minutos/segundos

### RF5. Opções de Salvamento
**Prioridade:** Média
**Descrição:** Permitir salvar como programa base ou específico

**Critérios:**
- [x] Checkbox "Salvar como Programa Base"
- [x] Se marcado: usar "BASE" em vez de stencil_code
- [x] Campo código stencil (read-only, da Aba 1)
- [x] Path gerado automaticamente baseado na opção

### RF6. Botão Testar Inspeção
**Prioridade:** Baixa
**Descrição:** Permitir teste opcional antes de salvar

**Critérios:**
- [x] Botão "🧪 Testar Inspeção"
- [x] Verificar requisitos (PLC conectado, câmera, stencil)
- [x] Confirmar com usuário antes de executar
- [x] Emitir signal `test_requested(ProgramConfig)`

### RF7. Botão Salvar
**Prioridade:** Alta
**Descrição:** Salvar programa com validação prévia

**Critérios:**
- [x] Botão "💾 Salvar Programa"
- [x] Validar configuração antes de salvar
- [x] Mostrar diálogo de confirmação com path
- [x] Avisar se há erros (mas permitir salvar se usuário insistir)
- [x] Emitir signal `save_requested(ProgramConfig)`

### RF8. Botão Voltar
**Prioridade:** Média
**Descrição:** Permitir voltar para aba anterior

**Critérios:**
- [x] Botão "← Voltar"
- [x] Emitir signal `back_requested()`
- [x] Não salvar mudanças (usuário volta para editar)

## Requisitos Não-Funcionais

### RNF1. Performance
- Validação deve completar em <1 segundo
- Salvamento deve completar em <2 segundos
- Interface deve responder instantaneamente

### RNF2. Usabilidade
- Layout claro e organizado
- Cores para indicar status (verde = válido, laranja = alertas)
- Fontes legíveis e hierarquia visual clara
- Tooltips explicativos

### RNF3. Confiabilidade
- Validação robusta em múltiplos níveis
- Tratamento de erros de I/O no salvamento
- Sem perda de dados
- Confirmations antes de ações destrutivas

### RNF4. Manutenibilidade
- Código bem documentado (docstrings)
- Type hints em todos os métodos
- Separação clara de responsabilidades
- Componentes reutilizáveis (SummaryCard, WarningPanel)

## Requisitos de Testes

### Testes de ProgramConfig (11 testes)
- [x] Criação e inicialização
- [x] Serialização dict (to_dict, from_dict)
- [x] Serialização JSON (to_json, from_json)
- [x] Validação (config válida)
- [x] Validação (config inválida - vários cenários)
- [x] Estimativas de tempo
- [x] Resumo (get_summary)
- [x] File path (get_file_path)
- [x] Salvamento (save_to_file)
- [x] Carregamento (from_file)

### Testes de Sub-Modelos (5 testes)
- [x] FiducialConfig
- [x] MosaicConfig
- [x] AlignmentConfig
- [x] InspectionGroupConfig

### Testes de UI Componentes (6 testes)
- [x] SummaryCard (inicialização, texto, HTML)
- [x] WarningPanel (vazio, com avisos, com erros)

### Testes de Widget (8 testes)
- [x] Inicialização
- [x] set_program_config (válido)
- [x] set_program_config (inválido)
- [x] Signals (save_requested, test_requested, back_requested)
- [x] Checkbox base_program
- [x] get_program_config
- [x] is_ready_to_save

### Cobertura de Código
- [x] Cobertura ≥80% para confirm_save_widget.py
- [x] Cobertura ≥95% para program_config.py
- [x] Todos os caminhos principais testados
- [x] Tratamento de erros testado

## Dependências

### Dependências de Código
- `consumo_lib.models.inspection_window`: Modelos da Track 6
- `aoi_lib.recipe_manager`: Recipe (referência)
- `PyQt6.QtWidgets`: Framework GUI
- `json`: Persistência
- `dataclasses`: Modelos de dados
- `datetime`: Timestamps
- `pathlib`: File paths

### Dependências de Dados (entradas)
- **Dados das 6 abas anteriores** (dict aggregado)
- **Metadados** (created_by, etc.)

### Dependências de Tracks
- **Tracks 1-6:** Fornecem dados para exibir no resumo

## Entregáveis (Deliverables)

### Arquivos de Código
1. `consumo_lib/models/engineering/program_config.py` (521 linhas)
   - ProgramConfig (agregado de 7 abas)
   - Sub-modelos (FiducialConfig, MosaicConfig, AlignmentConfig, InspectionGroupConfig)
   - Métodos de serialização e validação

2. `consumo_lib/widgets/engenharia/confirm_save_widget.py` (500 linhas)
   - ConfirmSaveWidget (widget principal)
   - SummaryCard (componente reutilizável)
   - WarningPanel (painel de avisos)

3. `tests/unit/widgets/engenharia/test_confirm_save_widget.py` (497 linhas)
   - 30 testes unitários
   - Fixtures para pytest
   - Mocks para dependências

### Metadados
1. `conductor/tracks/engenharia_aba7_confirmar_salvar/spec.md` (este arquivo)
2. `conductor/tracks/engenharia_aba7_confirmar_salvar/plan.md`
3. `conductor/tracks/engenharia_aba7_confirmar_salvar/metadata.json`

## Critérios de Sucesso

- [x] ProgramConfig implementado com todos os campos
- [x] Sub-modelos implementados e funcionando
- [x] Serialização JSON funcionando
- [x] Validação completa funcionando com erros específicos
- [x] Estimativas de tempo calculadas corretamente
- [x] ConfirmSaveWidget com 7 cards funcionando
- [x] Painel de avisos funcionando
- [x] Checkbox "Programa Base" funcionando
- [x] Botões "Testar" e "Salvar" funcionando
- [x] Signals emitidos corretamente
- [x] 30/30 testes passando (100%)
- [x] Cobertura de código ≥80%
- [x] Integração com Engineering Wizard possível

## Riscos e Mitigações

### Risco 1: Validação complexa
**Descrição:** Muitos critérios podem ter edge cases
**Probabilidade:** Média
**Impacto:** Alto
**Mitigação:** Validação em múltiplos níveis, testes abrangentes

### Risco 2: Estimativas imprecisas
**Descrição:** Tempos podem variar muito na prática
**Probabilidade:** Alta
**Impacto:** Baixo
**Mitigação:** Estimativas conservadoras, disclaimer de "aproximado"

### Risco 3: Falha no salvamento
**Descrição:** Permissões, disco cheio, etc.
**Probabilidade:** Baixa
**Impacto:** Alto
**Mitigação:** Tratamento robusto de erros, mensagens claras

### Risco 4: Confusão com programas base
**Descrição:** Usuários podem não entender diferença
**Probabilidade:** Média
**Impacto:** Médio
**Mitigação:** Tooltip explicativo, label claro, indicador visual

## Aprovações

- [x] Especificação aprovada por: Claude Code (Sonnet 4.5)
- [x] Data de aprovação: 2026-01-13
- [x] Implementação concluída: 2026-01-13

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-13
**Versão:** 1.0
**Status:** ✅ COMPLETO
