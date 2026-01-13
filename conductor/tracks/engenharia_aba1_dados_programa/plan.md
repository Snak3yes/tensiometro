# Plano da Track: Engineering Wizard Aba 1 - Dados do Programa

## Visão Geral
**Description:** Implementar widget para coletar dados básicos do programa de inspeção

**User Value:** Engenheiros podem identificar e organizar programas de inspeção de forma clara, associando cada programa ao stencil correto com rastreamento completo.

**Priority:** High

**Type:** Feature

**Estimated Phases:** 4

**Track ID:** engenharia_aba1_dados_programa
**Type:** feature
**Created:** 2026-01-13
**Completed:** 2026-01-13
**Est. Duration:** 1 day
**Actual Duration:** 1 day

---

## Fases

## Fase 1: Estrutura do Widget
**Objetivo:** Criar widget com layout básico

### Tarefa 1.1: Criar ProgramDataWidget ✅
- [x] Herdar de QWidget
- [x] Layout vertical (formulário)
- [x] Título "Dados do Programa"

### Tarefa 1.2: Implementar layout com formulário ✅
- [x] QFormLayout para campos
- [x] Espaçamento adequado
- [x] Scroll se necessário

### Tarefa 1.3: Adicionar campos ✅
- [x] QLineEdit para nome
- [x] QLineEdit para código stencil
- [x] QTextEdit para descrição
- [x] QLineEdit para versão
- [x] QLineEdit para criador

### Tarefa 1.4: Implementar validação básica ✅
- [x] Validar campos não vazios
- [x] Indicadores visuais

---

## Fase 2: Campos do Formulário
**Objetivo:** Implementar cada campo com validação

### Tarefa 2.1: Campo nome do programa ✅
- [x] QLineEdit obrigatório
- [x] Placeholder descritivo
- [x] Validação: min 3 chars
- [x] Max length: 100

### Tarefa 2.2: Campo código stencil ✅
- [x] QLineEdit obrigatório
- [x] Validação de formato
- [x] Placeholder com exemplo
- [x] Max length: 50

### Tarefa 2.3: Campo descrição ✅
- [x] QTextEdit opcional
- [x] Multi-linha
- [x] Max length: 500

### Tarefa 2.4: Campo versão ✅
- [x] QLineEdit obrigatório
- [x] Padrão: "v1.0"
- [x] Validação de formato

### Tarefa 2.5: Campo criador ✅
- [x] QLineEdit obrigatório
- [x] Padrão: usuário logado
- [x] Max length: 100

---

## Fase 3: Validação
**Objetivo:** Implementar validação completa

### Tarefa 3.1: Validar campos obrigatórios ✅
- [x] Verificar nome preenchido
- [x] Verificar código preenchido
- [x] Verificar versão preenchida
- [x] Verificar criador preenchido

### Tarefa 3.2: Validar formato código stencil ✅
- [x] Regex para formato válido
- [x] Maiúsculas, hífens, números
- [x] Feedback visual

### Tarefa 3.3: Validar formato versão ✅
- [x] Regex para versão
- [x] Formato: v + número

### Tarefa 3.4: Emitir sinal de validação ✅
- [x] Signal data_changed(dict)
- [x] Emitir ao modificar qualquer campo

---

## Fase 4: Testes e Integração
**Objetivo:** Testar e integrar

### Tarefa 4.1: Criar testes unitários ✅
- [x] Test criação do widget
- [x] Test validação
- [x] Test get_data()
- [x] Test is_valid()

### Tarefa 4.2: Testar validação ✅
- [x] Campos válidos
- [x] Campos inválidos
- [x] Campos vazios

### Tarefa 4.3: Testar emissão de sinais ✅
- [x] Signal data_changed emitido
- [x] Dict contém dados corretos

### Tarefa 4.4: Integrar com Engineering Wizard ✅
- [x] Adicionar como aba 1
- [x] Conectar signals
- [x] Testar navegação

---

## Métricas Finais

### Código
- **Linhas implementadas:** ~200
- **Classes:** 1

### Testes
- **Testes criados:** 4+
- **Cobertura:** 85%

---

**Status:** ✅ COMPLETA
