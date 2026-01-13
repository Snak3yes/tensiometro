# Especificação da Track: Engineering Wizard Aba 2 - Carregar Gerber

## Visão Geral
**Track ID:** engenharia_aba2_carregar_gerber
**Tipo:** Feature
**Prioridade:** High
**Complexidade:** High
**Data de Criação:** 2026-01-13
**Estimativa:** 2-3 dias

## Descrição Detalhada

Implementar o widget **Carregar Gerber (Aba 2)** do Engineering Wizard. Esta aba permite ao engenheiro carregar um arquivo Gerber RS-274X (formato padrão da indústria para PCB stencils), visualizar o preview vetorial, limpar aperturas indesejadas (que não são aberturas do stencil), e extrair informações críticas como dimensões, contagem de aperturas e detecção automática de fiduciais.

## Contexto e Motivação

O arquivo Gerber contém o design virtual do stencil. Antes de usá-lo para inspeção, o engenheiro precisa:
1. **Carregar** o arquivo correto (.gbr)
2. **Visualizar** para confirmar que é o stencil certo
3. **Limpar** elementos que não são aberturas (texto, marcas, etc.)
4. **Validar** que o arquivo está correto (tem fiduciais, dimensões, etc.)

## Objetivos

### Primário
1. Implementar upload de arquivo Gerber RS-274X
2. Renderizar preview vetorial com zoom/pan
3. Implementar limpeza interativa de aperturas
4. Detectar fiduciais automaticamente
5. Extrair métricas (dimensões, contagem)

### Secundário
1. Suportar arquivos grandes (>1MB)
2. Undo/redo na limpeza
3. Interface responsiva
4. Validação robusta

## Requisitos Funcionais

### RF1. Upload de Arquivo
**Prioridade:** Alta
- Botão "Carregar Gerber"
- Filtro .gbr, .ger, .txt
- Diálogo de seleção de arquivo
- Parse RS-274X

### RF2. Preview Visual
**Prioridade:** Alta
- Renderização vetorial
- Zoom com scroll
- Pan com clique do meio
- Informações do arquivo

### RF3. Limpeza de Gerber
**Prioridade:** Alta
- Seleção por clique
- Remoção de elementos
- Undo/redo
- Concluir limpeza

### RF4. Detecção de Fiduciais
**Prioridade:** Alta
- Buscar círculos em corners
- Listar candidatos
- Permitir seleção manual

### RF5. Extração de Dados
**Prioridade:** Alta
- Dimensões (width, height)
- Contagem de aperturas
- Posição dos fiduciais
- get_gerber_data()

## Requisitos Não-Funcionais

- Performance: <5s para parse
- Usabilidade: interface intuitiva
- Confiabilidade: sem crashes

## Critérios de Sucesso

- [x] GerberLoaderWidget implementado
- [x] Upload funcionando
- [x] Preview funcionando
- [x] Limpeza funcionando
- [x] Detecção de fiduciais
- [x] get_gerber_data() retornando dict

---

**Autor:** Claude Code (Sonnet 4.5)
**Data:** 2026-01-13
**Status:** ✅ COMPLETO
