# Plano da Track: Refatoração da Interface e Extração de Lógica

## Fase 1: Abstração do Controle de Movimento
- [x] Tarefa: Criar `MovementOrchestrator` em `aoi_lib` (camada lógica pura)
- [x] Tarefa: Criar testes unitários para `MovementOrchestrator`
- [x] Tarefa: Refatorar `MovementControlWidget` para delegar ações ao `MovementOrchestrator`
- [ ] Tarefa: Conductor - User Manual Verification 'Fase 1: Abstração do Controle de Movimento' (Protocol in workflow.md)

## Fase 2: Desacoplamento do Fluxo de Inspeção
- [~] Tarefa: Analisar `InspectionUIController` e identificar lógica de negócio misturada com UI
- [x] Tarefa: Extrair lógica para `InspectionFlowService` em `aoi_lib`
- [x] Tarefa: Criar testes unitários para `InspectionFlowService`
- [~] Tarefa: Atualizar `InspectionUIController` para usar o novo serviço
- [ ] Tarefa: Conductor - User Manual Verification 'Fase 2: Desacoplamento do Fluxo de Inspeção' (Protocol in workflow.md)

## Fase 3: Validação Final e Limpeza
- [ ] Tarefa: Executar Smoke Test da aplicação para garantir que refatorações não quebraram a UI
- [ ] Tarefa: Verificar cobertura de testes dos novos módulos
- [ ] Tarefa: Conductor - User Manual Verification 'Fase 3: Validação Final e Limpeza' (Protocol in workflow.md)
