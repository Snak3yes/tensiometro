# Especificação da Track: Refatoração da Gestão de Receitas

## Objetivo
Centralizar toda a lógica de validação, persistência e manipulação de receitas (CRUD) em um serviço puro na `aoi_lib`, removendo essas responsabilidades da camada de UI (Dialogs e Controllers).

## Escopo
- **RecipeService:** Criar (ou aprimorar `RecipeManager`) para atuar como a única fonte de verdade para operações com receitas.
- **Validação:** Mover regras de validação (ex: limites de tensão, dimensões do stencil) dos widgets para o serviço.
- **Desacoplamento UI:** Refatorar `RecipeManagerController` e `RecipeDialog` para usar exclusivamente o serviço, sem lógica de negócio embutida.
- **Cobertura:** Garantir testes unitários abrangentes para o serviço de receitas.

## Critérios de Aceite
- Todas as operações de CRUD de receitas devem ser possíveis via código (testes), sem instanciar `QDialog`.
- `RecipeDialog` deve apenas coletar inputs e exibir erros retornados pelo serviço.
- Testes funcionais para `RecipeManager` devem ter cobertura >85% (focada em comportamentos, não linhas de código).
- Testes devem verificar funcionalidades reais: persistência em disco, validações, CRUD completo.
- Nenhuma regressão funcional na criação/edição de receitas via interface.
