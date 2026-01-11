# Plano da Track: Refatoração da Gestão de Receitas

## Fase 1: Análise e Criação do Serviço [checkpoint: TBD]
- [x] Tarefa: Analisar `RecipeManager` (aoi_lib) e `RecipeDialog` (consumo_lib) para mapear a lógica existente
- [x] Tarefa: Aprimorar `RecipeManager` em `aoi_lib` para incluir validações robustas (centralizar lógica)
- [x] Tarefa: Criar testes unitários para o `RecipeManager` aprimorado (CRUD + Validações) <!-- 35 testes unitários, d0b3255 -->
- [x] Tarefa: Criar testes funcionais de integração focados em comportamentos <!-- 18 testes funcionais, 80% coverage, abc4db8 -->
- [x] Tarefa: Atualizar documentação de teste (workflow.md, spec.md) para enfatizar cobertura funcional >85% <!-- abc4db8 -->
- [x] Tarefa: Conductor - User Manual Verification 'Fase 1: Análise e Criação do Serviço' (Protocol in workflow.md) <!-- manual confirmation by user -->

## Fase 2: Integração com a Interface [checkpoint: passed]
- [x] Tarefa: Refatorar `RecipeManagerController` para usar as novas capacidades do `RecipeManager` <!-- manual -->
- [x] Tarefa: Limpar `RecipeDialog` removendo validações locais e delegando ao controller/service <!-- manual -->
- [x] Tarefa: Garantir que mensagens de erro de validação do serviço sejam exibidas corretamente na UI <!-- manual -->
- [x] Tarefa: Conductor - User Manual Verification 'Fase 2: Integração com a Interface' (Protocol in workflow.md)

## Fase 3: Validação Final
- [x] Tarefa: Executar Smoke Test da aplicação (foco em criar/editar receitas) <!-- passed -->
- [x] Tarefa: Verificar cobertura funcional de testes do `RecipeManager` <!-- 80% funcional (18 testes integração + 35 unitários), abc4db8 -->
- [x] Tarefa: Conductor - User Manual Verification 'Fase 3: Validação Final' (Protocol in workflow.md)
