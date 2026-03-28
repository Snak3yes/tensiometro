---
name: main_window_dimensions
description: Regra fixa para dimensões da janela principal do sistema
type: project
---

# Dimensões da Janela Principal

**REGRA FIXA:** A janela principal deve ter tamanho **1200×800 pixels**.

## Por que essa restrição?

O sistema será instalado em uma máquina industrial com **monitor predefinido** de resolução específica. A interface foi projetada para funcionar exatamente nessas dimensões.

## Especificações

| Propriedade | Valor |
|-------------|-------|
| Largura | 1200px (fixo) |
| Altura | 800px (fixo) |
| Redimensionamento | Desabilitado |
| Posição inicial | (100, 100) |

## Como aplicar no código

```python
# setup_coordinator.py
self.window.setGeometry(100, 100, 1200, 800)
self.window.setFixedSize(1200, 800)  # Impede resize
```

## O que NÃO fazer

- ❌ Não adicionar `setMinimumSize()` menor que 1200×800
- ❌ Não permitir que o usuário redimensione a janela
- ❌ Não criar layouts que dependam de resolução diferente

## Notas

- Diálogos podem ter tamanhos próprios (respeitando que não ultrapassem 800px de altura)
- Monitor industrial: modelo e especificações definidos pelo cliente