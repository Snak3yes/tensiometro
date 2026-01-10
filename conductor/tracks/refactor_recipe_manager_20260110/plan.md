# Plano da Track: Refatoração da Gestão de Receitas

## Fase 1: Análise e Criação do Serviço [checkpoint: 3137ff7]
- [~] Tarefa: Analisar `RecipeManager` (aoi_lib) e `RecipeDialog` (consumo_lib) para mapear a lógica existente
- [~] Tarefa: Aprimorar `RecipeManager` em `aoi_lib` para incluir validações robustas (centralizar lógica)
- [ ] Tarefa: Criar testes unitários para o `RecipeManager` aprimorado (CRUD + Validações)
- [ ] Tarefa: Conductor - User Manual Verification 'Fase 1: Análise e Criação do Serviço' (Protocol in workflow.md)

## Fase 2: Integração com a Interface
- [ ] Tarefa: Refatorar `RecipeManagerController` para usar as novas capacidades do `RecipeManager`
- [ ] Tarefa: Limpar `RecipeDialog` removendo validações locais e delegando ao controller/service
- [ ] Tarefa: Garantir que mensagens de erro de validação do serviço sejam exibidas corretamente na UI
- [ ] Tarefa: Conductor - User Manual Verification 'Fase 2: Integração com a Interface' (Protocol in workflow.md)

## Fase 3: Validação Final
- [ ] Tarefa: Executar Smoke Test da aplicação (foco em criar/editar receitas)
- [ ] Tarefa: Verificar cobertura de testes do `RecipeManager`
- [ ] Tarefa: Conductor - User Manual Verification 'Fase 3: Validação Final' (Protocol in workflow.md)
