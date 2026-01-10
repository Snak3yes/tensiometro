# Especificação da Track: Refatoração da Interface e Extração de Lógica

## Objetivo
Desacoplar a lógica de negócios e controle da camada de interface gráfica (Qt Widgets), movendo-a para serviços testáveis na `aoi_lib`.

## Escopo
- **Movement Control:** Refatorar `MovementControlWidget` para usar exclusivamente um `MovementService` puro, removendo lógica direta de chamadas ao `controller` dentro do widget.
- **Inspection UI:** Refatorar `InspectionUIController` para separar a lógica de orquestração do fluxo de inspeção da lógica de exibição de diálogos.
- **Cobertura:** Criar testes unitários para os novos serviços extraídos (almejando 100% de cobertura nestes novos módulos).

## Critérios de Aceite
- `MovementControlWidget` não deve ter lógica de decisão, apenas repasse de eventos para o serviço.
- Novos serviços criados em `aoi_lib` (ou subpacote apropriado) devem ser independentes de `PyQt6`.
- Testes unitários para os novos serviços devem passar sem necessidade de display gráfico.
- Funcionalidade da aplicação deve permanecer inalterada (regressão visual manual necessária).
