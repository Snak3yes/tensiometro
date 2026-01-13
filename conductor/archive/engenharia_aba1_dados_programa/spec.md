# Especificação da Track: Engineering Wizard Aba 1 - Dados do Programa

## Visão Geral
**Track ID:** engenharia_aba1_dados_programa
**Tipo:** Feature
**Prioridade:** High
**Complexidade:** Low
**Data de Criação:** 2026-01-13
**Estimativa:** 1 dia

## Descrição Detalhada

Implementar o widget **Dados do Programa (Aba 1)**, a primeira aba do Engineering Wizard. Esta aba coleta informações básicas sobre o programa de inspeção que está sendo criado: nome do programa, código do stencil associado, descrição opcional, versão e informações de rastreamento (criador, data de criação).

## Contexto e Motivação

### Fluxo do Engineering Wizard
O Engineering Wizard é um sistema de 7 abas para criar programas de inspeção AOI:
1. **Aba 1:** Dados do Programa ⭐ **ESTA TRACK**
2. **Aba 2:** Carregar Gerber
3. **Aba 3:** Definir Fiduciais
4. **Aba 4:** Capturar Mosaico
5. **Aba 5:** Alinhamento
6. **Aba 6:** Janelas de Inspeção
7. **Aba 7:** Confirmar e Salvar

### Problema a Resolver
Todo programa de inspeção precisa ser identificado univocamente e associado a um stencil específico. O sistema deve coletar these informações no início do wizard para:
- Identificar o programa posteriormente
- Associar ao stencil correto
- Permitir rastreamento (quem criou, quando)
- Organizar programas por versão

## Objetivos

### Primário
1. Coletar nome do programa (obrigatório)
2. Coletar código do stencil (obrigatório, validado)
3. Coletar descrição (opcional)
4. Coletar versão (obrigatório, padrão v1.0)
5. Coletar criador (obrigatório, padrão do usuário logado)

### Secundário
1. Validar código stencil contra banco de dados
2. Validação em tempo real
3. Interface intuitiva e limpa
4. Prevenir dados inválidos

## Alcance (Scope)

### INCLUÍDO
✅ Widget ProgramDataWidget com formulário
✅ Campos: nome, código stencil, descrição, versão, criador
✅ Validação de campos obrigatórios
✅ Validação de formato de código stencil
✅ Signal `data_changed(dict)` emitido ao modificar
✅ Método `get_data() -> dict`
✅ Método `is_valid() -> bool`
✅ Testes unitários

### EXCLUÍDO
❌ Edição de programas existentes (apenas criação)
❌ Upload de imagem do stencil
❌ Seleção de receita base (pode ser adicionado depois)

## Requisitos Funcionais

### RF1. Campo Nome do Programa
**Prioridade:** Alta
**Descrição:** QLineEdit para nomear o programa

**Critérios:**
- [x] Campo de texto obrigatório
- [x] Placeholder: "Ex: Inspeção STENCIL-ABC-123"
- [x] Validação: não vazio, mínimo 3 caracteres
- [x] Max length: 100 caracteres
- [x] Trim automático de espaços

### RF2. Campo Código Stencil
**Prioridade:** Alta
**Descrição:** QLineEdit para código do stencil

**Critérios:**
- [x] Campo obrigatório
- [x] Placeholder: "Ex: STENCIL-ABC-123"
- [x] Validação de formato (maiúsculas, hífens, algarismos)
- [x] Validação contra StencilManager (opcional)
- [x] Max length: 50 caracteres

### RF3. Campo Descrição
**Prioridade:** Média
**Descrição:** QTextEdit para descrição detalhada

**Critérios:**
- [x] Campo opcional
- [x] Placeholder: "Descreva o propósito deste programa..."
- [x] Max length: 500 caracteres
- [x] Multi-linha permitido
- [x] Scroll se necessário

### RF4. Campo Versão
**Prioridade:** Alta
**Descrição:** QLineEdit para versão do programa

**Critérios:**
- [x] Campo obrigatório
- [x] Valor padrão: "v1.0"
- [x] Placeholder: "Ex: v1.0, v2.1"
- [x] Validação de formato (v + número)
- [x] Max length: 20 caracteres

### RF5. Campo Criador
**Prioridade:** Média
**Descrição:** QLineEdit para identificar criador

**Critérios:**
- [x] Campo obrigatório
- [x] Valor padrão: usuário logado (se disponível)
- [x] Placeholder: "Ex: engenheiro@empresa.com"
- [x] Validação: não vazio
- [x] Max length: 100 caracteres

### RF6. Validação
**Prioridade:** Alta
**Descrição:** Validar campos em tempo real

**Critérios:**
- [x] Validar campos obrigatórios preenchidos
- [x] Validar formatos (código stencil, versão)
- [x] Exibir indicadores visuais (✓ ou ✗)
- [x] Emitir signal `data_changed(dict)` ao modificar

### RF7. Coleta de Dados
**Prioridade:** Alta
**Descrição:** Método para retornar todos os dados

**Critérios:**
- [x] Método `get_data() -> dict`
- [x] Retornar todos os campos em dict
- [x] Incluir timestamp de criação
- [x] Pronto para salvar na Track 7

## Requisitos Não-Funcionais

### RNF1. Usabilidade
- Layout limpo e organizado
- Labels claros acima de cada campo
- Placeholder texts descritivos
- Indicadores visuais de erro/ok

### RNF2. Performance
- Validação instantânea (<100ms)
- Sem blocking durante validação

### RNF3. Confiabilidade
- Validação robusta de entrada
- Sem crashes com dados inválidos
- Mensagens de erro claras

## Requisitos de Testes

### Testes Unitários
- [x] Test criação do widget
- [x] Test validação de campos obrigatórios
- [x] Test validação de formato
- [x] Test get_data()
- [x] Test is_valid()
- [x] Test signal data_changed

### Cobertura de Código
- [x] Cobertura ≥85%

## Dependências

### Dependências de Código
- `PyQt6.QtWidgets`: Framework GUI
- `consumo_lib.managers.StencilManager`: Validação de stencil

### Dependências de Dados
- Nenhuma (primeira aba)

## Entregáveis (Deliverables)

### Arquivos de Código
1. `consumo_lib/widgets/engenharia/program_data_widget.py`
   - ProgramDataWidget
   - Formulário com 5 campos
   - Validação
   - Signals

### Metadados
1. `conductor/tracks/engenharia_aba1_dados_programa/spec.md` (este arquivo)
2. `conductor/tracks/engenharia_aba1_dados_programa/plan.md`
3. `conductor/tracks/engenharia_aba1_dados_programa/metadata.json`

## Critérios de Sucesso

- [x] ProgramDataWidget implementado
- [x] 5 campos funcionando
- [x] Validação funcionando
- [x] Signal emitido corretamente
- [x] get_data() retornando dict correto
- [x] is_valid() funcionando
- [x] Testes passando
- [x] Integração com Engineering Wizard

## Aprovações

- [x] Especificação aprovada por: Claude Code (Sonnet 4.5)
- [x] Data de aprovação: 2026-01-13
- [x] Implementação concluída: 2026-01-13

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-13
**Versão:** 1.0
**Status:** ✅ COMPLETO
