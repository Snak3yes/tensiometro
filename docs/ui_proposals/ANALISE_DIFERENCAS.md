# Análise de Diferenças - Implementação vs Proposta 70/30

**Data:** 2026-03-29
**Branch:** fix/tension-measurement-ui
**Status:** EM PROGRESSO

---

## 📊 Comparação Detalhada

### 1. Painel Direito (30%) - Visualização

| Elemento | Proposta SVG | Implementação Atual | Status |
|----------|--------------|---------------------|--------|
| **Botões Superiores** | 75x28px e 65x28px, lado a lado | 75x28px e 65x28px, lado a lado | ✅ IMPLEMENTADO |
| **Critérios** | Labels 9px, spinboxes 45x18px, "Usar Receita" ao lado | Spinboxes 45x18px, labels 9px, botão 70x22px | ✅ IMPLEMENTADO |
| **Heatmap** | 310x280px, grid 4x4 com círculos r=14px | 310x280px fixo | ✅ IMPLEMENTADO |
| **Resultado** | 310x40px, badge verde "APROVADO" | Badge 310x40px centralizado | ✅ IMPLEMENTADO |
| **Estatísticas** | Box com 3 linhas: OK/WARN/NOK, Min/Máx/Média, Total | 3 linhas organizadas em GroupBox | ✅ IMPLEMENTADO |
| **Legenda** | Box com título + 3 itens horizontais | Título + 3 itens horizontais, 310x50px | ✅ IMPLEMENTADO |
| **Botão Histórico** | 310x35px, "Ver Histórico Completo" | 310x35px | ✅ IMPLEMENTADO |
| **Info Arquivo** | Box 310x60px no final | GroupBox "Arquivo" 310x60px | ✅ IMPLEMENTADO |

### 2. Painel Esquerdo (70%) - Lista

| Elemento | Proposta SVG | Implementação Atual | Status |
|----------|--------------|---------------------|--------|
| **Filtros** | 4 campos: Buscar, Período, Status, Ordenar | 4 campos implementados | ✅ IMPLEMENTADO |
| **Lista** | 6 colunas: Código, Descrição, Status, Tensão, Última, Ações | 6 colunas (ok) | ✅ IMPLEMENTADO |
| **Items** | 45px altura, selected verde | min-height: 45px, selected PRIMARY | ✅ IMPLEMENTADO |
| **Detalhes** | Layout horizontal, 7 campos + 2 botões | Layout vertical, poucos campos | ⚠️ PENDENTE |
| **Botões Detalhes** | 75x30px e 55x30px | Padrão StandardButton | ⚠️ PENDENTE |

### 3. Design System - Tokens Existentes vs Necessários

| Token | Existe? | Valor Atual | Valor Necessário |
|-------|---------|-------------|------------------|
| `BUTTON_INLINE_COMPACT` | ✅ | (50, 20) | Manter |
| `INPUT_HEIGHT_SM` | ✅ | 22px | Manter |
| `TYPO.LABEL_SMALL` | ✅ | 11px | Manter |
| `TYPO.LABEL_MEDIUM` | ✅ | 12px | Manter |

---

## 🎯 Plano de Correções

### Prioridade 1: Layout do Painel Direito ✅ CONCLUÍDO
1. [x] Reduzir botões superiores para `inline-compact`
2. [x] Reorganizar critérios em layout horizontal compacto
3. [x] Fixar tamanho do heatmap (310x280px minimum)
4. [x] Criar badge de resultado estilo "APROVADO/ATENÇÃO/REPROVADO"
5. [x] Separar estatísticas em múltiplas linhas
6. [x] Implementar legenda horizontal
7. [x] Adicionar info do arquivo no final

### Prioridade 2: Layout do Painel Esquerdo
1. [x] Adicionar filtro "Ordenar"
2. [x] Customizar altura dos items da tree (45px)
3. [ ] Reorganizar detalhes em layout horizontal (grid 3 colunas) - PENDENTE

### Prioridade 3: Ajustes Finos
1. [x] Reduzir font sizes conforme proposta (9-11px para labels secundários)
2. [x] Ajustar espaçamentos (padding/margin)
3. [x] Melhorar contraste de cores

---

## 📐 Dimensões de Referência (da Proposta)

### Botões
```
Superiores:     75x28px, 65x28px
Critérios:      Usar Receita: 100x22px
Resultado:      310x40px (badge full width)
Histórico:      310x35px
Detalhes:       75x30px, 55x30px
```

### Inputs
```
Spinboxes:      45x18px (critérios)
Search:         200x26px
Período/Status: 100-110x26px
```

### Heatmap
```
Container:      310x280px
Grid cell:      77.5x70px (aprox)
Círculos:       r=14px
Font tensão:    9px bold
```

### Tipografia
```
Título painel:  13px bold
Subtítulo:      10px
Labels críticos: 9px
Stats:          9-10px
Legenda:        10px bold
```

---

## 🔧 Arquivos para Modificar

1. `consumo_lib/tabs/tension_measurement_tab.py` - Layout principal
2. `consumo_lib/widgets/mini_tension_heatmap.py` - Heatmap sizing
3. `consumo_lib/ui/design_tokens.py` - Adicionar tokens se necessário
4. `consumo_lib/ui/widget_standards.py` - Adicionar variant de badge se necessário

---

**Próximo Passo:** Implementar correções por prioridade
