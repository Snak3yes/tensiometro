# Release v0.5-tension - Relatório de Alterações

**Data:** 2026-03-28
**Branch:** `release/v0.5-tension`
**Objetivo:** Versão simplificada para entrega ao cliente (apenas medição de tensão, sem inspeção visual)

---

## Alterações Realizadas

### 1. UI Simplificada

| Alteração | Descrição |
|-----------|-----------|
| Aba "Posições e Rotinas" | **REMOVIDA** - Funcionalidade de inspeção não necessária |
| Groupbox "Ações Rápidas" | **REMOVIDO** da aba Rastreabilidade |
| Aba "Movimento" | **CONVERTIDA** para diálogo não-modal (Ctrl+M) |
| Aba "Monitor CLP" | **CONVERTIDA** para diálogo não-modal (Ctrl+L) |

### 2. Diálogos Não-Modais Criados

- `MovementDialog` - Controle CNC acessível via menu Ferramentas
- `PLCMonitorDialog` - Monitoramento PLC acessível via menu Ferramentas

Ambos permanecem sobre a janela principal (`WindowStaysOnTopHint`)

### 3. Limpeza de Interface

- **Todos os emojis removidos** dos menus, abas, botões e diálogos
- Interface mais limpa e profissional

### 4. Documentação

- Regra de dimensões fixas (1200×800px) documentada no CLAUDE.md

---

## Commits Realizados

```
d79fb72 fix: Add KeyboardInterrupt protection in keyboard_handler eventFilter
5c718f9 refactor: Remove Camera & Movement tab for v0.5-tension
2b67eb8 fix: Resolve initialization errors for release v0.5-tension
90487db docs: Update CLAUDE.md with release v0.5-tension info
9d9d023 refactor: Remove all emojis from UI elements
37e64a9 refactor: Replace Monitor CLP tab with non-modal PLCMonitorDialog
36c75e3 refactor: Replace Movement tab with non-modal MovementDialog
09db999 refactor: Remove "Ações Rápidas" groupbox from Tracking tab
da4181a refactor: Remove "Posições e Rotinas" tab for tension-only release
```

---

## Bug Fixes

### KeyboardInterrupt no eventFilter (2026-03-29)

**Problema:** Windows Defender bloqueia arquivos `.pyc` durante primeira execução após período de inatividade, causando `KeyboardInterrupt` no Qt event loop.

**Solução:** Adicionado try-except wrapper no `eventFilter()` de `keyboard_handler.py` para capturar e ignorar o erro graciosamente.

**Arquivo:** `consumo_lib/handlers/keyboard_handler.py:90`

---

## Estado Atual

- **Branch:** `release/v0.5-tension` (sincronizada com GitHub e GitLab)
- **Funcionalidades ativas:** Medição de tensão, rastreabilidade, relatórios
- **Funcionalidades ocultas:** Inspeção visual, mosaico, Gerber

---

## Próximos Passos (Sugestões)

1. Testar aplicação com hardware real
2. Validar fluxo de medição de tensão completo
3. Merge para `main` após validação do cliente