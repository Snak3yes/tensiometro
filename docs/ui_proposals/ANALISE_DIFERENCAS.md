# Análise de Diferenças - Implementação vs Proposta 70/30

**Data:** 2026-03-29
**Branch:** fix/tension-measurement-ui

---

## 📊 Comparação Detalhada

### 1. Painel Direito (30%) - Visualização

| Elemento | Proposta SVG | Implementação Atual | Ação Necessária |
|----------|--------------|---------------------|-----------------|
| **Botões Superiores** | 75x28px e 65x28px, lado a lado | Largura total, um por linha | Usar `semantic_size="inline-compact"`, layout horizontal |
| **Critérios** | Labels 9px, spinboxes 45x18px, "Usar Receita" ao lado | Spinboxes grandes, "Usar Receita" abaixo | Reduzir spinboxes, layout horizontal compacto |
| **Heatmap** | 310x280px, grid 4x4 com círculos r=14px | Sem size definido, placeholder | Fixar minimum size, melhorar rendering |
| **Resultado** | 310x40px, badge verde "APROVADO" | Label "---", largura total,  estilo diferente | Criar widget de resultado tipo badge |
| **Estatísticas** | Box com 3 linhas: OK/WARN/NOK, Min/Máx/Média, Total | Label único linha longa | Separar em layout vertical com labels |
| **Legenda** | Box com 3 itens horizontais: 🟢 OK  WARN 🔴 NOK | Label vazio/não aparece | Implementar legenda horizontal |
| **Botão Histórico** | 310x35px, "Ver Histórico Completo" | Largura total, grande | Reduzir com `semantic_size="inline-primary"` |
| **Info Arquivo** | Box 310x60px no final | Não existe | Adicionar widget de info do arquivo |

### 2. Painel Esquerdo (70%) - Lista

| Elemento | Proposta SVG | Implementação Atual | Ação Necessária |
|----------|--------------|---------------------|-----------------|
| **Filtros** | 4 campos: Buscar, Período, Status, Ordenar | 3 campos: Buscar, Período, Status | Adicionar combo "Ordenar" |
| **Lista** | 6 colunas: Código, Descrição, Status, Tensão, Última, Ações | 6 colunas (ok) | Layout ok |
| **Items** | 45px altura, selected verde | Default QTreeWidget | Customizar item height, selected bg |
| **Detalhes** | Layout horizontal, 7 campos + 2 botões | Layout vertical, poucos campos | Mudar para horizontal grid |
| **Botões Detalhes** | 75x30px e 55x30px | Padrão StandardButton | Usar tamanhos compactos |

### 3. Design System - Tokens Existentes vs Necessários

| Token | Existe? | Valor Atual | Valor Necessário |
|-------|---------|-------------|------------------|
| `BUTTON_INLINE_COMPACT` | ✅ | (50, 20) | Manter |
| `INPUT_HEIGHT_SM` | ✅ | 22px | Manter |
| `TYPO.LABEL_SMALL` | ✅ | 11px | Manter |
| `TYPO.LABEL_MEDIUM` | ✅ | 12px | Manter |

---

## 🎯 Plano de Correções

### Prioridade 1: Layout do Painel Direito
1. [ ] Reduzir botões superiores para `inline-compact`
2. [ ] Reorganizar critérios em layout horizontal compacto
3. [ ] Fixar tamanho do heatmap (310x280px minimum)
4. [ ] Criar badge de resultado estilo "APROVADO/ATENÇÃO/REPROVADO"
5. [ ] Separar estatísticas em múltiplas linhas
6. [ ] Implementar legenda horizontal
7. [ ] Adicionar info do arquivo no final

### Prioridade 2: Layout do Painel Esquerdo
1. [ ] Adicionar filtro "Ordenar"
2. [ ] Customizar altura dos items da tree (45px)
3. [ ] Reorganizar detalhes em layout horizontal (grid 3 colunas)

### Prioridade 3: Ajustes Finos
1. [ ] Reduzir font sizes conforme proposta (9-11px para labels secundários)
2. [ ] Ajustar espaçamentos (padding/margin)
3. [ ] Melhorar contraste de cores

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
