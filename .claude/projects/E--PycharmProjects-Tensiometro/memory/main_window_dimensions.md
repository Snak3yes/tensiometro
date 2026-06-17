---
name: main_window_dimensions
description: Regra fixa para dimensoes da janela principal do sistema
type: project
---

# Dimensoes da Janela Principal

**REGRA FIXA:** A janela principal deve ter tamanho **1200x800 pixels**.

## Por que essa restricao?

O sistema sera instalado em uma maquina industrial com **monitor predefinido**
de resolucao especifica. A interface foi projetada para funcionar exatamente
nessas dimensoes.

## Especificacoes

| Propriedade | Valor |
|-------------|-------|
| Largura | 1200px (fixo) |
| Altura | 800px (fixo) |
| Redimensionamento | Desabilitado |
| Posicao inicial | (100, 100) |

## Como aplicar no codigo

```python
# setup_coordinator.py
self.window.setGeometry(100, 100, 1200, 800)
self.window.setFixedSize(1200, 800)  # Impede resize
```

## O que NAO fazer

- Nao adicionar `setMinimumSize()` menor que 1200x800.
- Nao permitir que o usuario redimensione a janela.
- Nao criar layouts que dependam de resolucao diferente.

## Notas

- Dialogos podem ter tamanhos proprios, respeitando que nao ultrapassem 800px de altura.
- Monitor industrial: modelo e especificacoes definidos pelo cliente.
