# Propostas de UI - Unificação das Abas Stencil e Visualização de Tensão

**Data:** 2026-03-29
**Objetivo:** Unir as abas "Stencils" e "Visualização de Tensão" em uma única aba "Medição de Tensão"

---

## 📋 Visão Geral das Propostas

### Proposta 1: Divisão Vertical Fixa
**Arquivo:** `proposta_1_vertical_split.svg`

**Características:**
- **Layout:** Split vertical 40%/60%
- **Esquerda (40%):** Lista de stencils + Filtros + Painel de detalhes
- **Direita (60%):** Visualização completa de tensão (heatmap + critérios + estatísticas)
- **Vantagens:**
  - Tudo visível simultaneamente
  - Contexto completo sempre disponível
  - Similar ao explorador de arquivos do Windows
- **Desvantagens:**
  - Menos espaço para o heatmap
  - Pode parecer "apertado" em resoluções menores

**Melhor para:** Operadores que precisam comparar múltiplos stencils rapidamente

---

### Proposta 2: Sub-Abas com Preview Integrado
**Arquivo:** `proposta_2_horizontal_tabs.svg`

**Características:**
- **Layout:** Duas sub-abas dentro da aba principal
- **Sub-aba "Stencils":** Lista completa + Preview do selecionado
- **Sub-aba "Visualização Gráfica":** Heatmap em tela cheia
- **Vantagens:**
  - Separação clara de contextos
  - Preview rápido sem mudar de aba
  - Heatmap com espaço máximo quando necessário
- **Desvantagens:**
  - Requer clique para ver visualização completa
  - Duas camadas de navegação

**Melhor para:** Fluxo de trabalho onde se seleciona um stencil primeiro, depois analisa em detalhe

---

### Proposta 3: Mestre-Detalhe com Lista Compacta
**Arquivo:** `proposta_3_master_detail.svg`

**Características:**
- **Layout:** Lista compacta lateral (350px) + Visualização expandida
- **Esquerda:** Lista vertical compacta com indicadores visuais
- **Direita:** Visualização completa do stencil selecionado
- **Vantagens:**
  - Máximo espaço para visualização
  - Lista sempre acessível para troca rápida
  - Design moderno estilo "inspector" do macOS
  - Indicadores visuais (status, tensão média) em cada item
- **Desvantagens:**
  - Lista mostra menos itens por vez
  - Requer scroll para muitos stencils

**Melhor para:** Análise detalhada de stencil individual com trocas ocasionais

---

## 📊 Comparação Direta

| Característica | Proposta 1 | Proposta 2 | Proposta 3 |
|----------------|------------|------------|------------|
| Espaço p/ Heatmap | Médio | Máximo (aba 2) | Máximo |
| Visão geral da lista | **Melhor** | Média | Limitada |
| Troca rápida de stencil | **Sim** | Sim | **Sim** |
| Contexto simultâneo | **Sim** | Parcial | Parcial |
| Complexidade UI | Baixa | Média | Baixa |
| Similar a | Windows Explorer | IDE com abas | macOS Finder |

---

## 🎯 Recomendação por Caso de Uso

### Se o operador precisa:
- **Comparar múltiplos stencils frequentemente** → **Proposta 1**
- **Analisar um stencil por vez em profundidade** → **Proposta 3**
- **Fluxo sequencial (selecionar → analisar)** → **Proposta 2**

---

## 🔧 Elementos Comuns a Todas Propostas

1. **Filtros:** Buscar, Período, Status
2. **Critérios de Aceitação:** 4 spins + botão "Usar Receita"
3. **Heatmap:** Círculos coloridos com valores de tensão
4. **Estatísticas:** OK/WARNING/NOK counts + médias
5. **Hardware Status Bar:** PLC, Tensiômetro, Câmera

---

## 📝 Próximos Passos

1. **Analisar** as 3 propostas visualmente
2. **Selecionar** uma proposta ou combinar elementos
3. **Ajustar** detalhes conforme necessário
4. **Implementar** a solução escolhida

---

## 🎨 Arquivos SVG

- `docs/ui_proposals/proposta_1_vertical_split.svg`
- `docs/ui_proposals/proposta_2_horizontal_tabs.svg`
- `docs/ui_proposals/proposta_3_master_detail.svg`

**Visualização:** Abra os arquivos SVG em qualquer browser moderno ou visualizador de imagens.
