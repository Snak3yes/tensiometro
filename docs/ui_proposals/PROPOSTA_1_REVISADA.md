# Proposta 1 Revisada - Divisão 80%/20%

**Data:** 2026-03-29
**Arquivo:** `proposta_1_revisada_80_20.svg`

---

## 📐 Layout Revisado

### Divisão de Espaço
| Painel | Largura | Conteúdo |
|--------|---------|----------|
| **Esquerdo** | 80% (960px) | Lista completa de stencils + Filtros + Painel de detalhes |
| **Direito** | 20% (220px) | Mini heatmap + Resultado + Estatísticas compactas + Botões |

---

## ✨ Mudanças Principais

### Painel Esquerdo (80%)
- ✅ Lista expandida com **8 colunas** de dados
- ✅ **8+ stencils visíveis** simultaneamente
- ✅ Coluna "Ações" com botão "Ver" para cada item
- ✅ Painel de detalhes expandido com mais informações
- ✅ Botões de ação rápida (Histórico, Ver) no painel de detalhes

### Painel Direito (20%)
- ✅ **Mini heatmap** (200x200px) - visualização compacta 3x3
- ✅ **Resultado** em destaque (APROVADO/ATENÇÃO/REPROVADO)
- ✅ **Estatísticas compactas** (OK/WARN/NOK counts)
- ✅ **Critérios rápidos** (Mín/Máx/Warn)
- ✅ **3 botões** de ação (Carregar JSON, Recarregar, Histórico)
- ✅ **Legenda** de cores
- ✅ **Estatísticas extra** (Mín/Máx/Média)

---

## 🎯 Vantagens Desta Versão

| Vantagem | Descrição |
|----------|-----------|
| **Mais stencils visíveis** | 8+ items na lista vs 5 anteriores |
| **Contexto completo** | Todos dados do stencil selecionado visíveis |
| **Preview funcional** | Heatmap compacto mas legível para avaliação rápida |
| **Ações rápidas** | Botões diretos em cada linha e no painel lateral |
| **Hierarquia clara** | Lista = foco principal, Visualização = referência |

---

## 🔍 Elementos do Painel Lateral (20%)

```
┌─────────────────────────┐
│ 📊 Visualização         │
│ STN-001 Selecionado     │
├─────────────────────────┤
│ [MINI HEATMAP 3x3]      │
│ 🟢 🟢                 │
│ 🟢 🟢 🟢                │
│ 🟡 🟢                 │
├─────────────────────────┤
│ ✅ APROVADO             │
├─────────────────────────┤
│ Resultados:             │
│ 🟢 OK: 8 (89%)          │
│ 🟡 WARN: 1 (11%)        │
│ Total: 9 pontos         │
├─────────────────────────┤
│ CRITÉRIOS               │
│ Mín: 25 | Máx: 45       │
│ Warn: 28 - 42           │
├─────────────────────────┤
│ [📁 Carregar JSON]      │
│ [↻ Recarregar] [📜 His] │
├─────────────────────────┤
│ Legenda:                │
│ 🟢 OK 🟡 WARN 🔴 NOK    │
├─────────────────────────┤
│ Estatísticas:           │
│ Mín: 23.1 | Máx: 42.8   │
│ Média: 35.7 N/cm²       │
└─────────────────────────┘
```

---

## 📊 Comparação: Original vs Revisada

| Característica | Original (40/60) | Revisada (80/20) |
|----------------|------------------|------------------|
| Stencils visíveis | ~5 items | ~8+ items |
| Espaço heatmap | Grande (400x450) | Compacto (200x200) |
| Detalhes do stencil | Painel dedicado | Linha expandida + painel |
| Foco principal | Visualização | Lista de stencils |
| heat | Média | Rápida |

---

## ✅ Quando Esta Versão é Ideal

- **Operador precisa** gerenciar múltiplos stencils
- **Visualização completa** é secundária (apenas referência)
- **Fluxo principal:** Selecionar stencil → Ver status → Ações
- **Heatmap detalhado** pode ser aberto em diálogo separado se necessário

---

## 🔧 Possíveis Ajustes Futuros

1. **Botão "Ver Completo"** → Abre visualização em diálogo modal
2. **Duplo-clique na lista** → Expande painel lateral temporariamente
3. **Resize handle** → Permite ajustar divisão dinamicamente
4. **Colunas personalizáveis** → Usuário escolhe quais colunas exibir
