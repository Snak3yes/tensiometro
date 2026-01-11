# Plano da Track: Refatoração da Gestão de Receitas

## Fase 1: Análise e Criação do Serviço [checkpoint: 3137ff7]
- [x] Tarefa: Analisar `RecipeManager` (aoi_lib) e `RecipeDialog` (consumo_lib) para mapear a lógica existente
- [x] Tarefa: Aprimorar `RecipeManager` em `aoi_lib` para incluir validações robustas (centralizar lógica)
- [x] Tarefa: Criar testes unitários para o `RecipeManager` aprimorado (CRUD + Validações) <!-- 35 testes, 96% coverage, d0b3255 -->
- [ ] Tarefa: Conductor - User Manual Verification 'Fase 1: Análise e Criação do Serviço' (Protocol in workflow.md)

## Fase 2: Integração com a Interface [checkpoint: passed]
- [x] Tarefa: Refatorar `RecipeManagerController` para usar as novas capacidades do `RecipeManager` <!-- manual -->
- [x] Tarefa: Limpar `RecipeDialog` removendo validações locais e delegando ao controller/service <!-- manual -->
- [x] Tarefa: Garantir que mensagens de erro de validação do serviço sejam exibidas corretamente na UI <!-- manual -->
- [x] Tarefa: Conductor - User Manual Verification 'Fase 2: Integração com a Interface' (Protocol in workflow.md)

## Fase 3: Validação Final
- [x] Tarefa: Executar Smoke Test da aplicação (foco em criar/editar receitas) <!-- passed -->
- [x] Tarefa: Verificar cobertura de testes do `RecipeManager` <!-- 96% (35 testes) -->
- [x] Tarefa: Conductor - User Manual Verification 'Fase 3: Validação Final' (Protocol in workflow.md)
